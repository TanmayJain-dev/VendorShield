import uuid
from typing import List, Tuple
from ...schemas.invoice import InvoiceClaim
from ...schemas.evidence import FieldCheckResult
from ...schemas.assessment import RiskAssessment
from ...schemas.enums import RecommendationOutcome, CheckStatus

class DeterministicRuleEngine:
    """
    VendorShield Rule Engine:
    - Layer 1: Hard Safety Gates (cannot be overridden by score)
    - Layer 2: Transparent, testable risk score points
    - Layer 3: Fail-closed outcome routing
    """
    def __init__(self, version: str = "1.0.0"):
        self.version = version

    def evaluate(
        self,
        case_id: str,
        invoice: InvoiceClaim,
        field_checks: List[FieldCheckResult]
    ) -> RiskAssessment:
        reason_codes = []
        hard_gates_triggered = []
        
        # Start with clean score (100 = low risk / perfect match)
        score = 100

        # --- Check Local Invoice Integrity ---
        if invoice.gstin_format_valid is False:
            hard_gates_triggered.append("GSTIN_FORMAT_INVALID")
            reason_codes.append("GSTIN_FORMAT_INVALID")
            score -= 30

        if invoice.arithmetic_valid is False:
            reason_codes.append("INVOICE_ARITHMETIC_MISMATCH")
            score -= 20

        # --- Check Discovered Evidence Reconciliations ---
        for check in field_checks:
            if check.reason_code:
                if check.reason_code not in reason_codes:
                    reason_codes.append(check.reason_code)

            if check.reason_code == "GST_STATUS_INACTIVE_CONFIRMED":
                hard_gates_triggered.append("GST_STATUS_INACTIVE_CONFIRMED")
                score -= 50

            elif check.reason_code == "LEGAL_NAME_MISMATCH":
                # Illustrative deduction for trade name vs legal entity
                score -= 20

            elif check.reason_code == "BANK_OWNERSHIP_UNVERIFIED":
                # Unverified beneficiary deduction
                score -= 12

            elif check.reason_code == "CRITICAL_NAME_MISMATCH":
                hard_gates_triggered.append("CRITICAL_NAME_MISMATCH")
                score -= 40

            elif check.reason_code == "EVIDENCE_INSUFFICIENT":
                hard_gates_triggered.append("EVIDENCE_INSUFFICIENT")
                score -= 25

        # Normalize score
        score = max(0, min(100, score))

        # --- Recommendation Logic (Fail Closed) ---
        if "GST_STATUS_INACTIVE_CONFIRMED" in hard_gates_triggered or "CRITICAL_NAME_MISMATCH" in hard_gates_triggered:
            recommendation = RecommendationOutcome.BLOCK
        elif hard_gates_triggered or len(reason_codes) > 0 or score < 75:
            recommendation = RecommendationOutcome.MANUAL_REVIEW
        else:
            recommendation = RecommendationOutcome.PASS

        # Evidence completeness assessment
        has_unavailable = any(c.status == CheckStatus.UNAVAILABLE for c in field_checks)
        completeness = "PARTIAL" if has_unavailable else "COMPLETE"

        return RiskAssessment(
            assessment_id=f"assess_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            ruleset_version=self.version,
            recommendation=recommendation,
            risk_score=score,
            reason_codes=reason_codes,
            field_checks=field_checks,
            hard_gates_triggered=hard_gates_triggered,
            evidence_completeness=completeness,
            human_signoff_required=True
        )
