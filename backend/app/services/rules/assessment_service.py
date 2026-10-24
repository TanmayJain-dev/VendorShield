from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from ...schemas.case import Case
from ...schemas.assessment import RiskAssessment
from ...schemas.forensic_graph import DirectorProfile, AddressClusterProfile
from ...schemas.enums import RecommendationOutcome
from ...config import settings
from ..reconciler.evidence_reconciler import EvidenceReconciler
from .engine import DeterministicRuleEngine
from .forensic_engine import ForensicRiskEngine

class AssessmentService:
    """
    Unified Single Source of Truth for Case Assessment.
    Used consistently across create_case, investigate, invoice corrections (PATCH),
    manual evidence entry, and reviewer sign-off preparation.
    
    Principles:
    1. Core Engine: DeterministicRuleEngine evaluates explicit rule triggers, deducts
       compliance scores, and produces deterministic recommendation (PASS/MANUAL_REVIEW/BLOCK).
    2. Experimental Forensics: 5-vector forensic risk topology, ITC clawback calculator,
       and knowledge entity graph are computed only when ENABLE_EXPERIMENTAL_FORENSICS=true
       or when evaluating synthetic demonstration fixtures (is_demo=True).
    3. Fail-Closed Invariant: Unavailable or missing evidence prevents PASS outcomes.
    """
    def __init__(self, version: Optional[str] = None):
        self.version = version or settings.RULES_VERSION
        self.reconciler = EvidenceReconciler()
        self.rule_engine = DeterministicRuleEngine(version=self.version)
        self.forensic_engine = ForensicRiskEngine(version=self.version)

    def assess(
        self,
        case: Case,
        directors: Optional[List[DirectorProfile]] = None,
        address_cluster: Optional[AddressClusterProfile] = None,
        litigation_meta: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        gstr2b_entry: Optional[Any] = None,
        buyer_has_gstr2b: bool = False
    ) -> RiskAssessment:
        if not case.invoice:
            raise ValueError(f"Cannot assess case {case.case_id}: invoice claims are missing")

        # 0. Check GSTR-2B entry if db provided
        if db and gstr2b_entry is None:
            from ...db.repository import CaseRepository
            gstr2b_entry = CaseRepository.find_gstr2b_entry(db, case.invoice.gstin, case.invoice.invoice_number)
            buyer_has_gstr2b = CaseRepository.has_gstr2b_entries_for_buyer(db, case.invoice.buyer_gstin)

        # 1. Reconcile invoice against all current evidence items
        field_checks = self.reconciler.reconcile(case.invoice, case.evidence_items)

        # 2. Run core deterministic rules engine with GSTR-2B facts
        assessment = self.rule_engine.evaluate(
            case.case_id,
            case.invoice,
            field_checks,
            gstr2b_entry=gstr2b_entry,
            buyer_has_gstr2b=buyer_has_gstr2b
        )

        # 3. Additive forensic vectors if enabled or demo
        is_demo = getattr(case, "is_demo", False)
        enable_forensics = getattr(settings, "ENABLE_EXPERIMENTAL_FORENSICS", False)

        if enable_forensics or is_demo:
            forensic_res = self.forensic_engine.evaluate(
                case_id=case.case_id,
                invoice=case.invoice,
                field_checks=field_checks,
                directors=directors or [],
                address_cluster=address_cluster or AddressClusterProfile(
                    raw_address=case.invoice.billing_address or "Unknown",
                    collocated_gstins_count=1,
                    premises_type="COMMERCIAL_HUB",
                    is_ghost_hub=False
                ),
                litigation_meta=litigation_meta or {"active_cases": 0, "nclt_petitions": []},
                evidence_items=case.evidence_items
            )
            assessment.forensic_vectors = forensic_res.forensic_vectors
            assessment.itc_exposure = forensic_res.itc_exposure
            assessment.entity_graph = forensic_res.entity_graph

            # Enforce strictest outcome between core rules and forensic hard gates
            if forensic_res.recommendation == RecommendationOutcome.BLOCK:
                assessment.recommendation = RecommendationOutcome.BLOCK
            elif forensic_res.recommendation == RecommendationOutcome.MANUAL_REVIEW and assessment.recommendation == RecommendationOutcome.PASS:
                assessment.recommendation = RecommendationOutcome.MANUAL_REVIEW

            for code in forensic_res.reason_codes:
                if code not in assessment.reason_codes:
                    assessment.reason_codes.append(code)
            for gate in forensic_res.hard_gates_triggered:
                if gate not in assessment.hard_gates_triggered:
                    assessment.hard_gates_triggered.append(gate)
        else:
            # Cleanly nullify forensic vectors for real non-experimental cases
            assessment.forensic_vectors = None
            assessment.itc_exposure = None
            assessment.entity_graph = None

        return assessment

    def explain_verdict(self, case: Case) -> Dict[str, Any]:
        """
        Produces a plain-English explanation of why the case received its verdict
        and specific actions that would resolve or clear the review status.
        """
        assessment = case.assessment
        if not assessment:
            return {
                "case_id": case.case_id,
                "verdict": "NOT_ASSESSED",
                "risk_score": 0,
                "why_this_verdict": ["No automated assessment has been performed on this case."],
                "what_would_change_it": ["Trigger vendor investigation or submit registry evidence."]
            }

        why_items: List[str] = []
        action_items: List[str] = []

        # Determine 'Why' items from triggered rules and hard gates
        for rule in assessment.triggered_rules:
            if rule.reason_code == "ITC_NOT_IN_GSTR2B":
                why_items.append("Invoice is missing from imported GSTR-2B returns filed by suppliers.")
                action_items.append("Place payment on hold until supplier files GSTR-1 or re-import the updated GSTR-2B.")
            elif rule.reason_code == "GSTR2B_VALUE_MISMATCH":
                why_items.append("Invoice gross amount contradicts the value reported by the supplier in GSTR-2B.")
                action_items.append("Request credit note or amended invoice matching the filed GSTR-1 value.")
            elif rule.reason_code == "GSTR2B_ITC_NOT_AVAILABLE":
                why_items.append("Supplier explicitly marked this invoice as ineligible for Input Tax Credit (itcavl=N).")
                action_items.append("Hold the GST tax portion of the payment until supplier amends their GSTR-1 return.")
            elif rule.reason_code == "GSTIN_FORMAT_INVALID":
                why_items.append("Supplier GSTIN failed official 15-character Modulo-36 format and checksum validation.")
            elif rule.reason_code == "GST_STATUS_INACTIVE_CONFIRMED":
                why_items.append("Supplier GST registration is confirmed Cancelled, Suspended, or Inactive on the public registry.")
            elif rule.reason_code == "CRITICAL_NAME_MISMATCH":
                why_items.append("Severe discrepancy between supplier name on invoice and registered legal entity name.")
            elif rule.reason_code == "EINVOICE_QR_MISMATCH":
                why_items.append("Tampering detected: Cryptographically verified E-Invoice QR code contradicts printed totals.")
            elif rule.reason_code == "EVIDENCE_INSUFFICIENT" or rule.reason_code == "GST_STATUS_UNKNOWN":
                why_items.append("Public GST registry data is currently unavailable (no active or manual lookup).")
            elif rule.reason_code == "INVOICE_ARITHMETIC_MISMATCH":
                why_items.append(f"Invoice mathematical totals do not reconcile: {rule.description}")
            elif rule.reason_code == "BUYER_GSTIN_MISMATCH":
                why_items.append("Billed Buyer GSTIN does not match any registered organization GSTIN.")
            elif rule.reason_code == "BUYER_GSTIN_MISSING":
                why_items.append("Buyer GSTIN is omitted from the invoice.")
            elif rule.reason_code == "TAX_TYPE_STATE_MISMATCH":
                why_items.append(f"State tax inconsistency: {rule.description}")
            elif rule.reason_code == "FUTURE_INVOICE_DATE":
                why_items.append("Invoice date is set in the future.")
            elif rule.reason_code == "ITC_TIME_BAR_WARNING":
                why_items.append("Invoice date exceeds statutory Section 16(4) ITC cut-off (30 Nov following FY).")
            elif rule.reason_code == "EXTRACTION_CONFLICT":
                why_items.append("Unresolved conflicts between document QR code, text, and OCR extraction layers.")
            elif rule.reason_code == "BANK_OWNERSHIP_UNVERIFIED":
                why_items.append("Bank account beneficiary ownership has not been attested by human review.")
            elif rule.reason_code == "IFSC_INVALID":
                why_items.append("Bank IFSC code was rejected by the RBI IFSC repository.")
            elif rule.reason_code == "ZERO_TAX_UNVERIFIED":
                why_items.append("Zero GST tax claimed on invoice without exemption proof.")
            else:
                why_items.append(rule.description)

        # What would change it
        if assessment.recommendation == RecommendationOutcome.BLOCK:
            action_items.append("Reject invoice payment hold; vendor must reissue compliant invoice with valid GST registration.")
            action_items.append("Verify whether vendor has obtained GST restoration order before re-evaluating.")
        elif assessment.recommendation == RecommendationOutcome.MANUAL_REVIEW:
            if "GST_STATUS_UNKNOWN" in assessment.reason_codes or "EVIDENCE_INSUFFICIENT" in assessment.reason_codes:
                action_items.append("Submit verified GST portal taxpayer details via manual entry or connect registry API.")
            if "INVOICE_ARITHMETIC_MISMATCH" in assessment.reason_codes or "TAX_BREAKDOWN_INFERRED" in assessment.reason_codes or "ZERO_TAX_UNVERIFIED" in assessment.reason_codes:
                action_items.append("Confirm invoice line item arithmetic and exact tax rate breakdown (CGST/SGST/IGST).")
            if "BUYER_GSTIN_MISMATCH" in assessment.reason_codes or "BUYER_GSTIN_MISSING" in assessment.reason_codes:
                action_items.append("Confirm whether invoice was billed to an authorized sister organization or branch.")
            if "BANK_OWNERSHIP_UNVERIFIED" in assessment.reason_codes:
                action_items.append("Upload cancelled cheque or run penny-drop verification to confirm beneficiary bank account ownership.")
            if "EXTRACTION_CONFLICT" in assessment.reason_codes:
                action_items.append("Inspect original document image to manually confirm disputed fields.")
            if not action_items:
                action_items.append("Review flagged invoice fields and reconcile with supplier documentation.")
        elif assessment.recommendation == RecommendationOutcome.PASS:
            why_items = [
                "Supplier GSTIN is valid with verified Modulo-36 checksum.",
                "Active GST registration confirmed with matching business name.",
                "Invoice line items, tax split, and totals verified without inference.",
                "Buyer GSTIN and tax states match authorized company registrations."
            ]
            action_items.append("Ready for final AP analyst / reviewer sign-off and payment release.")

        return {
            "case_id": case.case_id,
            "verdict": assessment.recommendation.value,
            "risk_score": assessment.risk_score,
            "score_policy": "Policy compliance index (0-100); not a statistical fraud probability.",
            "why_this_verdict": why_items if why_items else ["Standard policy criteria met."],
            "what_would_change_it": action_items
        }

assessment_service = AssessmentService()
