from typing import List, Optional
from ...schemas.invoice import InvoiceClaim
from ...schemas.evidence import EvidenceItem, FieldCheckResult
from ...schemas.enums import CheckStatus

class EvidenceReconciler:
    """
    Deterministically compares invoice claims against discovered evidence.
    Produces granular field-by-field check results with explicit confidence and provenance.
    """
    def reconcile(
        self,
        invoice: InvoiceClaim,
        evidence_items: List[EvidenceItem]
    ) -> List[FieldCheckResult]:
        checks = []

        # Find GST/Legal evidence
        gst_evidence = next(
            (e for e in evidence_items if "gst" in e.source_name.lower() or "legal" in e.claim_supported.lower()),
            None
        )

        # 1. Trade Name vs Legal Name Check
        if gst_evidence and "legal_name" in gst_evidence.facts:
            legal_name = gst_evidence.facts["legal_name"]
            trade_name = invoice.supplier_name
            
            if trade_name.lower() == legal_name.lower():
                checks.append(FieldCheckResult(
                    check_id="chk_name_match",
                    field_name="Supplier Identity",
                    invoice_value=trade_name,
                    evidence_value=legal_name,
                    status=CheckStatus.MATCH,
                    explanation="Invoice trade name matches registered legal entity name exactly.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url
                ))
            elif trade_name.lower() in legal_name.lower() or "trade_name" in gst_evidence.facts:
                checks.append(FieldCheckResult(
                    check_id="chk_legal_name_discrepancy",
                    field_name="Trade vs Legal Name",
                    invoice_value=trade_name,
                    evidence_value=legal_name,
                    status=CheckStatus.POSSIBLE_MATCH,
                    reason_code="LEGAL_NAME_MISMATCH",
                    explanation=(
                        f"Invoice uses trade name '{trade_name}', whereas public registry lists legal entity "
                        f"'{legal_name}'. Requires verification of registered trade alias."
                    ),
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url
                ))
            else:
                checks.append(FieldCheckResult(
                    check_id="chk_name_mismatch",
                    field_name="Supplier Identity",
                    invoice_value=trade_name,
                    evidence_value=legal_name,
                    status=CheckStatus.MISMATCH,
                    reason_code="CRITICAL_NAME_MISMATCH",
                    explanation="Invoice supplier name does not match legal entity found in public registry.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url
                ))
        else:
            checks.append(FieldCheckResult(
                check_id="chk_name_unknown",
                field_name="Supplier Identity",
                invoice_value=invoice.supplier_name,
                evidence_value=None,
                status=CheckStatus.UNAVAILABLE,
                reason_code="EVIDENCE_INSUFFICIENT",
                explanation="No authoritative public registry record found to verify legal entity."
            ))

        # 2. GST Registration Status
        if gst_evidence and "status" in gst_evidence.facts:
            reg_status = gst_evidence.facts["status"]
            if reg_status.lower() == "active":
                checks.append(FieldCheckResult(
                    check_id="chk_gst_active",
                    field_name="GST Registration Status",
                    invoice_value=invoice.gstin,
                    evidence_value="Active",
                    status=CheckStatus.MATCH,
                    explanation="Authoritative registry confirms GST registration is currently Active.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url
                ))
            else:
                checks.append(FieldCheckResult(
                    check_id="chk_gst_inactive",
                    field_name="GST Registration Status",
                    invoice_value=invoice.gstin,
                    evidence_value=reg_status,
                    status=CheckStatus.MISMATCH,
                    reason_code="GST_STATUS_INACTIVE_CONFIRMED",
                    explanation=f"GST registration is listed as {reg_status}. Input Tax Credit (ITC) may be invalid.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url
                ))
        else:
            checks.append(FieldCheckResult(
                check_id="chk_gst_unknown",
                field_name="GST Registration Status",
                invoice_value=invoice.gstin,
                evidence_value=None,
                status=CheckStatus.UNAVAILABLE,
                reason_code="GST_STATUS_UNKNOWN",
                explanation="Could not confirm active registration from current accessible records."
            ))

        # 3. Bank Account Ownership Check (Strict Truth Invariant)
        bank_evidence = next(
            (e for e in evidence_items if "bank" in e.source_name.lower() or "ifsc" in e.claim_supported.lower()),
            None
        )
        if invoice.ifsc_code:
            checks.append(FieldCheckResult(
                check_id="chk_bank_ownership",
                field_name="Bank Beneficiary Ownership",
                invoice_value=f"IFSC: {invoice.ifsc_code} | A/C: {invoice.bank_account_masked or 'Not specified'}",
                evidence_value="Branch verified; Account Ownership Unverified",
                status=CheckStatus.POSSIBLE_MATCH,
                reason_code="BANK_OWNERSHIP_UNVERIFIED",
                explanation=(
                    "Public IFSC lookup verifies bank branch validity, but CANNOT verify beneficiary account ownership. "
                    "Requires offline cancelled cheque or penny-drop verification."
                ),
                evidence_id=bank_evidence.evidence_id if bank_evidence else None,
                source_url=bank_evidence.source_url if bank_evidence else None
            ))

        return checks
