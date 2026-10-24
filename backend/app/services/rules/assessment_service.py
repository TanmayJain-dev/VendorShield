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
        litigation_meta: Optional[Dict[str, Any]] = None
    ) -> RiskAssessment:
        if not case.invoice:
            raise ValueError(f"Cannot assess case {case.case_id}: invoice claims are missing")

        # 1. Reconcile invoice against all current evidence items
        field_checks = self.reconciler.reconcile(case.invoice, case.evidence_items)

        # 2. Run core deterministic rules engine
        assessment = self.rule_engine.evaluate(case.case_id, case.invoice, field_checks)

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

assessment_service = AssessmentService()
