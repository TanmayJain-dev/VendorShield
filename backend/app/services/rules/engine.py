import re
import uuid
from typing import List, Tuple, Optional
from datetime import datetime, timezone, date
from ...schemas.invoice import InvoiceClaim
from ...schemas.evidence import FieldCheckResult
from ...schemas.assessment import RiskAssessment, RuleTrigger
from ...schemas.enums import RecommendationOutcome, CheckStatus, SourceMode, ExtractionStatus
from ...config import settings

VALID_PAN_HOLDERS = set("CPHFATBLJG")

class DeterministicRuleEngine:
    """
    Deterministic VendorShield Rule Engine:
    - Transparent, deterministic deductions based on explicit rules.
    - Explicitly NOT presented as a calibrated statistical fraud probability.
    - Granular rule trigger objects with severities, reason codes, weights, and evidence links.
    - Single source of truth for PASS / MANUAL_REVIEW / BLOCK verdicts.
    """
    def __init__(self, version: Optional[str] = None):
        self.version = version or settings.RULES_VERSION

    def evaluate(
        self,
        case_id: str,
        invoice: InvoiceClaim,
        field_checks: List[FieldCheckResult],
        gstr2b_entry: Optional[Any] = None,
        buyer_has_gstr2b: bool = False
    ) -> RiskAssessment:
        triggered_rules: List[RuleTrigger] = []
        reason_codes: List[str] = []
        hard_gates_triggered: List[str] = []
        missing_evidence_items: List[str] = []
        
        # Base policy compliance index (100 = full policy compliance)
        score = 100

        # --- Rule 1: GSTIN Presence & Format Checksum ---
        if not invoice.gstin:
            rule = RuleTrigger(
                rule_id="RULE_GSTIN_MISSING",
                rule_name="Supplier GSTIN Missing",
                severity="HIGH",
                weight=30,
                is_hard_gate=False,
                reason_code="GSTIN_MISSING",
                description="Supplier GSTIN is missing from invoice. Fail-closed policy requires manual invoice inspection."
            )
            triggered_rules.append(rule)
            reason_codes.append("GSTIN_MISSING")
            missing_evidence_items.append("Supplier GSTIN")
            score -= 30
        elif invoice.gstin_format_valid is False:
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

        # --- Rule 2: PAN Consistency & Entity Structure ---
        if invoice.gstin and len(invoice.gstin) >= 12:
            pan = invoice.gstin[2:12].upper()
            if len(pan) >= 4 and pan[3] not in VALID_PAN_HOLDERS:
                rule = RuleTrigger(
                    rule_id="RULE_PAN_FORMAT_INVALID",
                    rule_name="Invalid Embedded PAN Holder Type",
                    severity="HIGH",
                    weight=20,
                    is_hard_gate=False,
                    reason_code="PAN_FORMAT_INVALID",
                    description=f"4th character '{pan[3]}' of GSTIN PAN ({pan}) is not a valid taxpayer entity code (expected C, P, H, F, A, T, B, L, J, or G)."
                )
                triggered_rules.append(rule)
                reason_codes.append("PAN_FORMAT_INVALID")
                score -= 20

        # --- Rule 3: Invoice Mathematical Consistency ---
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

        # --- Rule 4: Buyer GSTIN Matching ---
        configured_buyers = [str(b).strip().upper() for b in (settings.BUYER_GSTINS or []) if str(b).strip()]
        if configured_buyers:
            if not invoice.buyer_gstin:
                rule = RuleTrigger(
                    rule_id="RULE_BUYER_GSTIN_MISSING",
                    rule_name="Missing Buyer GSTIN",
                    severity="HIGH",
                    weight=20,
                    is_hard_gate=False,
                    reason_code="BUYER_GSTIN_MISSING",
                    description="Buyer GSTIN is missing from invoice. Input Tax Credit cannot be claimed in an unverified entity's name."
                )
                triggered_rules.append(rule)
                reason_codes.append("BUYER_GSTIN_MISSING")
                missing_evidence_items.append("Billed Organization GSTIN")
                score -= 20
            elif invoice.buyer_gstin.strip().upper() not in configured_buyers:
                rule = RuleTrigger(
                    rule_id="RULE_BUYER_GSTIN_MISMATCH",
                    rule_name="Buyer GSTIN Mismatch",
                    severity="HIGH",
                    weight=25,
                    is_hard_gate=False,
                    reason_code="BUYER_GSTIN_MISMATCH",
                    description=f"Extracted Buyer GSTIN ({invoice.buyer_gstin}) does not match any registered company GSTIN."
                )
                triggered_rules.append(rule)
                reason_codes.append("BUYER_GSTIN_MISMATCH")
                score -= 25

        # --- Rule 5: Tax Type vs State Consistency ---
        if invoice.gstin and len(invoice.gstin) >= 2:
            sup_state = invoice.gstin[:2]
            buy_state = None
            if invoice.buyer_gstin and len(invoice.buyer_gstin) >= 2:
                buy_state = invoice.buyer_gstin[:2]
            elif invoice.place_of_supply and len(invoice.place_of_supply.strip()) == 2 and invoice.place_of_supply.strip().isdigit():
                buy_state = invoice.place_of_supply.strip()

            if sup_state and buy_state:
                if sup_state == buy_state:
                    # Intra-state: CGST + SGST expected
                    if invoice.igst > 1.0 and (invoice.cgst <= 0.0 or invoice.sgst <= 0.0):
                        rule = RuleTrigger(
                            rule_id="RULE_TAX_TYPE_STATE_MISMATCH",
                            rule_name="Tax Type vs State Mismatch",
                            severity="HIGH",
                            weight=20,
                            is_hard_gate=False,
                            reason_code="TAX_TYPE_STATE_MISMATCH",
                            description=f"Intra-state supply (State code {sup_state}) erroneously charged IGST instead of CGST + SGST."
                        )
                        triggered_rules.append(rule)
                        reason_codes.append("TAX_TYPE_STATE_MISMATCH")
                        score -= 20
                else:
                    # Inter-state: IGST expected
                    if (invoice.cgst > 1.0 or invoice.sgst > 1.0) and invoice.igst <= 0.0:
                        rule = RuleTrigger(
                            rule_id="RULE_TAX_TYPE_STATE_MISMATCH",
                            rule_name="Tax Type vs State Mismatch",
                            severity="HIGH",
                            weight=20,
                            is_hard_gate=False,
                            reason_code="TAX_TYPE_STATE_MISMATCH",
                            description=f"Inter-state supply (Supplier State {sup_state} -> Buyer State {buy_state}) charged CGST/SGST instead of IGST."
                        )
                        triggered_rules.append(rule)
                        reason_codes.append("TAX_TYPE_STATE_MISMATCH")
                        score -= 20

        # --- Rule 6: Invoice Number Format (Rule 46) ---
        if invoice.invoice_number and invoice.invoice_number != "UNKNOWN-INV":
            inv_str = invoice.invoice_number.strip()
            if len(inv_str) > 16 or re.search(r"[^A-Za-z0-9\-_/]", inv_str):
                rule = RuleTrigger(
                    rule_id="RULE_INVOICE_NUMBER_FORMAT_INVALID",
                    rule_name="Invoice Number Format Violation (Rule 46)",
                    severity="LOW",
                    weight=10,
                    is_hard_gate=False,
                    reason_code="INVOICE_NUMBER_FORMAT_INVALID",
                    description=f"Invoice number '{inv_str}' exceeds 16 characters or contains prohibited symbols under GST Rule 46."
                )
                triggered_rules.append(rule)
                reason_codes.append("INVOICE_NUMBER_FORMAT_INVALID")
                score -= 10

        # --- Rule 7: Date Sanity & Section 16(4) ITC Time Bar ---
        if invoice.invoice_date:
            try:
                inv_dt = datetime.strptime(invoice.invoice_date[:10], "%Y-%m-%d").date()
                today = date.today()
                if inv_dt > today:
                    rule = RuleTrigger(
                        rule_id="RULE_FUTURE_INVOICE_DATE",
                        rule_name="Future-Dated Invoice",
                        severity="HIGH",
                        weight=30,
                        is_hard_gate=False,
                        reason_code="FUTURE_INVOICE_DATE",
                        description=f"Invoice date ({invoice.invoice_date}) is in the future."
                    )
                    triggered_rules.append(rule)
                    reason_codes.append("FUTURE_INVOICE_DATE")
                    score -= 30
                else:
                    # FY runs Apr 1 to Mar 31. Cutoff is Nov 30 following FY end.
                    fy_end_year = inv_dt.year if inv_dt.month <= 3 else inv_dt.year + 1
                    itc_cutoff = date(fy_end_year, 11, 30)
                    if today > itc_cutoff:
                        rule = RuleTrigger(
                            rule_id="RULE_ITC_TIME_BAR_WARNING",
                            rule_name="ITC Section 16(4) Statutory Deadline Elapsed",
                            severity="LOW",
                            weight=10,
                            is_hard_gate=False,
                            reason_code="ITC_TIME_BAR_WARNING",
                            description=f"Invoice date ({invoice.invoice_date}) exceeds Section 16(4) cut-off ({itc_cutoff}). Verify with Chartered Accountant."
                        )
                        triggered_rules.append(rule)
                        reason_codes.append("ITC_TIME_BAR_WARNING")
                        score -= 10
            except Exception:
                pass

        # --- Rule 8: Extraction Conflicts & QR Discrepancy ---
        if invoice.extraction_conflicts:
            has_qr_conflict = any(
                c.get("source_a") == "QR" or c.get("source_b") == "QR" 
                for c in invoice.extraction_conflicts
            )
            if has_qr_conflict and getattr(invoice, "qr_signature_status", None) == "VERIFIED":
                rule = RuleTrigger(
                    rule_id="RULE_EINVOICE_QR_MISMATCH",
                    rule_name="Cryptographically Verified QR Mismatch",
                    severity="CRITICAL",
                    weight=50,
                    is_hard_gate=True,
                    reason_code="EINVOICE_QR_MISMATCH",
                    description="Tampering Warning: Verified-signature E-Invoice QR code payload contradicts printed invoice values."
                )
                triggered_rules.append(rule)
                hard_gates_triggered.append("EINVOICE_QR_MISMATCH")
                reason_codes.append("EINVOICE_QR_MISMATCH")
                score -= 50
            else:
                rule = RuleTrigger(
                    rule_id="RULE_EXTRACTION_CONFLICT",
                    rule_name="Layered Extraction Discrepancy",
                    severity="HIGH",
                    weight=25,
                    is_hard_gate=False,
                    reason_code="EXTRACTION_CONFLICT",
                    description="Invoice contains conflicting field extractions across QR, printed text, or OCR layers."
                )
                triggered_rules.append(rule)
                reason_codes.append("EXTRACTION_CONFLICT")
                score -= 25

        # --- Rule 9: Line Item Sum Consistency ---
        if invoice.line_items and len(invoice.line_items) > 1:
            line_sum = sum(li.total for li in invoice.line_items)
            ref_amt = invoice.taxable_amount if invoice.taxable_amount > 0 else invoice.total_amount
            if ref_amt > 0 and abs(line_sum - ref_amt) > 2.0 and abs(line_sum - invoice.total_amount) > 2.0:
                rule = RuleTrigger(
                    rule_id="RULE_LINE_ITEM_ARITHMETIC_MISMATCH",
                    rule_name="Line Item Aggregation Discrepancy",
                    severity="HIGH",
                    weight=20,
                    is_hard_gate=False,
                    reason_code="LINE_ITEM_ARITHMETIC_MISMATCH",
                    description=f"Sum of extracted line items (INR {line_sum:.2f}) does not match invoice total (INR {ref_amt:.2f})."
                )
                triggered_rules.append(rule)
                reason_codes.append("LINE_ITEM_ARITHMETIC_MISMATCH")
                score -= 20

        # --- Rule 10: Tax Breakdown Uncertainty / Inferred ---
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

        # --- Rule 11: Zero-Tax / Missing Tax Specification ---
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

        # --- Rule 12: Extraction Errors / Parsing Failures ---
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
        gst_status_active_verified = False
        has_critical_name_mismatch = False

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
                has_critical_name_mismatch = True
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

            elif check.reason_code == "IFSC_INVALID":
                rule = RuleTrigger(
                    rule_id="RULE_IFSC_INVALID",
                    rule_name="Invalid Bank IFSC Code",
                    severity="MEDIUM",
                    weight=20,
                    is_hard_gate=False,
                    reason_code="IFSC_INVALID",
                    description=check.explanation
                )
                triggered_rules.append(rule)
                score -= 20

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

            # Track verified active GST status
            if check.field_name == "gst_status" and check.status == CheckStatus.MATCH:
                gst_status_active_verified = True


        # --- Rule 13: GSTR-2B Reconciliation & ITC Eligibility ---
        if gstr2b_entry:
            # Check value mismatch
            if abs(invoice.total_amount - gstr2b_entry.invoice_value) > 2.0:
                rule = RuleTrigger(
                    rule_id="RULE_GSTR2B_VALUE_MISMATCH",
                    rule_name="GSTR-2B Filed Value Discrepancy",
                    severity="HIGH",
                    weight=25,
                    is_hard_gate=False,
                    reason_code="GSTR2B_VALUE_MISMATCH",
                    description=f"Invoice amount (INR {invoice.total_amount:.2f}) does not match GSTR-2B filed value (INR {gstr2b_entry.invoice_value:.2f})."
                )
                triggered_rules.append(rule)
                reason_codes.append("GSTR2B_VALUE_MISMATCH")
                score -= 25

            # Check ITC Availability flag
            if not getattr(gstr2b_entry, "itc_available", True):
                rule = RuleTrigger(
                    rule_id="RULE_GSTR2B_ITC_NOT_AVAILABLE",
                    rule_name="ITC Ineligible in GSTR-2B Return",
                    severity="MEDIUM",
                    weight=20,
                    is_hard_gate=False,
                    reason_code="GSTR2B_ITC_NOT_AVAILABLE",
                    description="Supplier flagged this invoice with ITC Available = 'No' in GSTR-2B filing."
                )
                triggered_rules.append(rule)
                reason_codes.append("GSTR2B_ITC_NOT_AVAILABLE")
                score -= 20
        elif buyer_has_gstr2b:
            rule = RuleTrigger(
                rule_id="RULE_ITC_NOT_IN_GSTR2B",
                rule_name="Invoice Missing From GSTR-2B Filing",
                severity="MEDIUM",
                weight=20,
                is_hard_gate=False,
                reason_code="ITC_NOT_IN_GSTR2B",
                description="Invoice not found in imported GSTR-2B return. Payment hold advised until supplier files GSTR-1."
            )
            triggered_rules.append(rule)
            reason_codes.append("ITC_NOT_IN_GSTR2B")
            score -= 20

        # Normalize score bounds
        score = max(0, min(100, score))

        # --- Recommendation Policy Routing (Fail-Closed Verdict Semantics) ---
        # 1. BLOCK: Only confirmed bad facts
        critical_block_gates = {
            "GST_STATUS_INACTIVE_CONFIRMED",
            "CRITICAL_NAME_MISMATCH",
            "EINVOICE_QR_MISMATCH",
            "GSTIN_FORMAT_INVALID"
        }
        
        has_block_gate = any(gate in critical_block_gates for gate in hard_gates_triggered)
        
        if has_block_gate:
            recommendation = RecommendationOutcome.BLOCK
        elif (
            len(hard_gates_triggered) > 0
            or len(reason_codes) > 0
            or score < 75
            or invoice.tax_inferred
            or (invoice.total_amount > 0 and total_tax == 0.0)
            or len(invoice.parsing_errors) > 0
            or len(invoice.extraction_conflicts) > 0
            or invoice.arithmetic_valid is not True
            or invoice.gstin_format_valid is not True
            or any(c.status in (CheckStatus.UNAVAILABLE, CheckStatus.NOT_FOUND) for c in field_checks)
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
