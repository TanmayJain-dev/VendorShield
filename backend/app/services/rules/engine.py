import uuid
from typing import List, Tuple, Optional
from datetime import datetime, timezone
from ...schemas.invoice import InvoiceClaim
from ...schemas.evidence import FieldCheckResult
from ...schemas.assessment import RiskAssessment, RuleTrigger
from ...schemas.enums import RecommendationOutcome, CheckStatus, SourceMode, ExtractionStatus

class DeterministicRuleEngine:
    """
    Deterministic VendorShield Rule Engine:
    - Transparent, deterministic deductions based on explicit rules.
    - Explicitly NOT presented as a calibrated statistical fraud probability.
    - Granular rule trigger objects with severities, reason codes, weights, and evidence links.
    - Robust evidence completeness calculation distinguishing live, simulated, missing, and conflicting evidence.
    """
    def __init__(self, version: str = "1.0.0"):
        self.version = version

    def evaluate(
        self,
        case_id: str,
        invoice: InvoiceClaim,
        field_checks: List[FieldCheckResult]
    ) -> RiskAssessment:
        triggered_rules: List[RuleTrigger] = []
        reason_codes: List[str] = []
        hard_gates_triggered: List[str] = []
        missing_evidence_items: List[str] = []
        
        # Base policy compliance index (100 = full policy compliance)
        score = 100

        # --- Rule 1: GSTIN Format Checksum ---
        if invoice.gstin_format_valid is False:
            rule = RuleTrigger(
                rule_id="RULE_GSTIN_FORMAT_INVALID",
                rule_name="GSTIN Format or Checksum Failure",
                severity="CRITICAL",
                weight=30,
                is_hard_gate=True,
                reason_code="GSTIN_FORMAT_INVALID",
                description="Invoice GSTIN does not conform to official 15-character format or fails Modulo-36 checksum."
            )
            triggered_rules.append(rule)
            hard_gates_triggered.append("GSTIN_FORMAT_INVALID")
            reason_codes.append("GSTIN_FORMAT_INVALID")
            score -= 30

        # --- Rule 2: Invoice Mathematical Consistency ---
        if invoice.arithmetic_valid is False:
            rule = RuleTrigger(
                rule_id="RULE_ARITHMETIC_MISMATCH",
                rule_name="Invoice Arithmetic Discrepancy",
                severity="HIGH",
                weight=20,
                is_hard_gate=False,
                reason_code="INVOICE_ARITHMETIC_MISMATCH",
                description=invoice.arithmetic_notes or "Tax breakdown and taxable amounts do not sum to total invoice value."
            )
            triggered_rules.append(rule)
            reason_codes.append("INVOICE_ARITHMETIC_MISMATCH")
            score -= 20

        # --- Rule 3: Tax Breakdown Uncertainty / Inferred ---
        def _check_inferred(v):
            if hasattr(v, "status"):
                return v.status == ExtractionStatus.INFERRED
            if isinstance(v, dict):
                return v.get("status") in (ExtractionStatus.INFERRED, ExtractionStatus.INFERRED.value)
            return False

        if invoice.tax_inferred or any(_check_inferred(v) for v in invoice.extraction_metadata.values()):
            rule = RuleTrigger(
                rule_id="RULE_TAX_INFERRED_UNCERTAINTY",
                rule_name="Inferred Tax Breakdown",
                severity="MEDIUM",
                weight=15,
                is_hard_gate=False,
                reason_code="TAX_BREAKDOWN_INFERRED",
                description="Tax breakdown was inferred/estimated rather than extracted as explicit invoice facts."
            )
            triggered_rules.append(rule)
            reason_codes.append("TAX_BREAKDOWN_INFERRED")
            score -= 15

        # --- Rule 4: Zero-Tax / Missing Tax Specification ---
        total_tax = round(invoice.cgst + invoice.sgst + invoice.igst, 2)
        if invoice.total_amount > 0 and total_tax == 0.0:
            rule = RuleTrigger(
                rule_id="RULE_ZERO_TAX_INVOICE",
                rule_name="Zero-Tax / Missing Tax Specification",
                severity="MEDIUM",
                weight=15,
                is_hard_gate=False,
                reason_code="ZERO_TAX_UNVERIFIED",
                description="Invoice has zero GST tax claimed. Requires human review to verify tax exemption or export/SEZ documentation."
            )
            triggered_rules.append(rule)
            reason_codes.append("ZERO_TAX_UNVERIFIED")
            missing_evidence_items.append("Tax Exemption Certificate / LUT / Export Proof")
            score -= 15

        # --- Rule 5: Extraction Errors / Parsing Failures ---
        if invoice.parsing_errors:
            rule = RuleTrigger(
                rule_id="RULE_PARSING_EXTRACTION_FAILURE",
                rule_name="Invoice Extraction Failure",
                severity="HIGH",
                weight=30,
                is_hard_gate=False,
                reason_code="PARSING_EXTRACTION_ERROR",
                description="Invoice parsing failed. Fail-closed policy requires manual document inspection."
            )
            triggered_rules.append(rule)
            reason_codes.append("PARSING_EXTRACTION_ERROR")
            score -= 30

        # --- Evaluate Field-Level Checks from Evidence Reconciliation ---
        for check in field_checks:
            if check.reason_code and check.reason_code not in reason_codes:
                reason_codes.append(check.reason_code)

            if check.reason_code == "GST_STATUS_INACTIVE_CONFIRMED":
                rule = RuleTrigger(
                    rule_id="RULE_GST_STATUS_INACTIVE",
                    rule_name="Inactive GST Registration",
                    severity="CRITICAL",
                    weight=50,
                    is_hard_gate=True,
                    reason_code="GST_STATUS_INACTIVE_CONFIRMED",
                    description=check.explanation,
                    evidence_reference=check.source_url
                )
                triggered_rules.append(rule)
                hard_gates_triggered.append("GST_STATUS_INACTIVE_CONFIRMED")
                score -= 50

            elif check.reason_code == "CRITICAL_NAME_MISMATCH":
                rule = RuleTrigger(
                    rule_id="RULE_CRITICAL_NAME_MISMATCH",
                    rule_name="Critical Supplier Name Mismatch",
                    severity="CRITICAL",
                    weight=40,
                    is_hard_gate=True,
                    reason_code="CRITICAL_NAME_MISMATCH",
                    description=check.explanation,
                    evidence_reference=check.source_url
                )
                triggered_rules.append(rule)
                hard_gates_triggered.append("CRITICAL_NAME_MISMATCH")
                score -= 40

            elif check.reason_code == "LEGAL_NAME_MISMATCH":
                rule = RuleTrigger(
                    rule_id="RULE_LEGAL_NAME_MISMATCH",
                    rule_name="Trade Name vs Legal Entity Discrepancy",
                    severity="MEDIUM",
                    weight=20,
                    is_hard_gate=False,
                    reason_code="LEGAL_NAME_MISMATCH",
                    description=check.explanation,
                    evidence_reference=check.source_url
                )
                triggered_rules.append(rule)
                score -= 20

            elif check.reason_code == "BANK_OWNERSHIP_UNVERIFIED":
                rule = RuleTrigger(
                    rule_id="RULE_BANK_OWNERSHIP_UNVERIFIED",
                    rule_name="Unverified Bank Beneficiary Ownership",
                    severity="LOW",
                    weight=12,
                    is_hard_gate=False,
                    reason_code="BANK_OWNERSHIP_UNVERIFIED",
                    description=check.explanation,
                    evidence_reference=check.source_url
                )
                triggered_rules.append(rule)
                score -= 12
                missing_evidence_items.append("Beneficiary Bank Account Proof (Cancelled Cheque / Penny Drop)")

            elif check.reason_code == "EVIDENCE_INSUFFICIENT":
                rule = RuleTrigger(
                    rule_id="RULE_EVIDENCE_INSUFFICIENT",
                    rule_name="Insufficient Public Registry Evidence",
                    severity="HIGH",
                    weight=25,
                    is_hard_gate=True,
                    reason_code="EVIDENCE_INSUFFICIENT",
                    description=check.explanation,
                    missing_evidence="Authoritative GSTIN Registration Record"
                )
                triggered_rules.append(rule)
                hard_gates_triggered.append("EVIDENCE_INSUFFICIENT")
                score -= 25
                missing_evidence_items.append("Authoritative GSTIN Registration Record")

            elif check.reason_code == "GST_STATUS_UNKNOWN":
                rule = RuleTrigger(
                    rule_id="RULE_GST_STATUS_UNKNOWN",
                    rule_name="GST Registration Status Unavailable",
                    severity="MEDIUM",
                    weight=15,
                    is_hard_gate=False,
                    reason_code="GST_STATUS_UNKNOWN",
                    description=check.explanation,
                    missing_evidence="Active GST Registration Status"
                )
                triggered_rules.append(rule)
                score -= 15
                missing_evidence_items.append("Active GST Registration Status")

            elif check.reason_code == "RULE_DUPLICATE_INVOICE_EXACT":
                rule = RuleTrigger(
                    rule_id="RULE_DUPLICATE_INVOICE_EXACT",
                    rule_name="Exact Duplicate Invoice Detected",
                    severity="HIGH",
                    weight=30,
                    is_hard_gate=False,
                    reason_code="RULE_DUPLICATE_INVOICE_EXACT",
                    description=check.explanation
                )
                triggered_rules.append(rule)
                score -= 30

            elif check.reason_code == "RULE_DUPLICATE_INVOICE_SUSPECT":
                rule = RuleTrigger(
                    rule_id="RULE_DUPLICATE_INVOICE_SUSPECT",
                    rule_name="Suspected Duplicate Invoice Number",
                    severity="HIGH",
                    weight=20,
                    is_hard_gate=False,
                    reason_code="RULE_DUPLICATE_INVOICE_SUSPECT",
                    description=check.explanation
                )
                triggered_rules.append(rule)
                score -= 20

        # Normalize score bounds
        score = max(0, min(100, score))

        # --- Recommendation Policy Routing (Fail-Closed) ---
        # Duplicates require manual human review; only confirmed inactive GST or critical legal name mismatch block directly
        critical_block_gates = {"GST_STATUS_INACTIVE_CONFIRMED", "CRITICAL_NAME_MISMATCH"}
        if any(gate in critical_block_gates for gate in hard_gates_triggered):
            recommendation = RecommendationOutcome.BLOCK
        elif (
            hard_gates_triggered 
            or len(reason_codes) > 0 
            or score < 75 
            or invoice.tax_inferred 
            or (invoice.total_amount > 0 and total_tax == 0.0) 
            or len(invoice.parsing_errors) > 0
        ):
            recommendation = RecommendationOutcome.MANUAL_REVIEW
        else:
            recommendation = RecommendationOutcome.PASS

        # --- Evidence Completeness & Provenance Calculation ---
        has_unavailable = any(c.status in (CheckStatus.UNAVAILABLE, CheckStatus.NOT_FOUND) for c in field_checks)
        has_simulated = any(getattr(c, "source_mode", SourceMode.SIMULATED) == SourceMode.SIMULATED for c in field_checks)
        has_conflicts = any(c.status == CheckStatus.MISMATCH for c in field_checks)

        if any(c.reason_code == "EVIDENCE_INSUFFICIENT" for c in field_checks):
            completeness = "INSUFFICIENT"
        elif has_conflicts:
            completeness = "CONFLICTING"
        elif has_unavailable:
            completeness = "PARTIAL"
        elif has_simulated:
            completeness = "SIMULATED_VERIFIED"
        else:
            completeness = "COMPLETE"

        provenance_mode = SourceMode.SIMULATED if has_simulated else SourceMode.LIVE

        return RiskAssessment(
            assessment_id=f"assess_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            ruleset_version=self.version,
            recommendation=recommendation,
            risk_score=score,
            score_explanation=(
                "Deterministic policy compliance index (0-100) reflecting explicit rule deductions; "
                "not a calibrated statistical fraud probability."
            ),
            reason_codes=reason_codes,
            field_checks=field_checks,
            hard_gates_triggered=hard_gates_triggered,
            triggered_rules=triggered_rules,
            missing_evidence_items=missing_evidence_items,
            evidence_completeness=completeness,
            evidence_provenance_mode=provenance_mode,
            human_signoff_required=True,
            assessed_at=datetime.now(timezone.utc).isoformat()
        )
