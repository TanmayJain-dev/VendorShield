import re
from typing import List, Optional, Tuple, Set
from ...schemas.invoice import InvoiceClaim
from ...schemas.evidence import EvidenceItem, FieldCheckResult
from ...schemas.enums import CheckStatus, SourceMode

BUSINESS_SUFFIX_PATTERNS = [
    r"\bprivate\s+limited\b",
    r"\bpvt\.?\s*ltd\.?\b",
    r"\bpublic\s+limited\b",
    r"\blimited\b",
    r"\bltd\.?\b",
    r"\bllp\b",
    r"\bllc\b",
    r"\binc\.?\b",
    r"\bincorporated\b",
    r"\bcorp\.?\b",
    r"\bcorporation\b",
    r"\bco\.?\b",
    r"\bcompany\b",
    r"\benterprises\b",
    r"\bservices\b",
    r"\bsolutions\b",
    r"\btechnologies\b",
    r"\bindia\b",
]

def normalize_business_name(name: Optional[str]) -> str:
    """
    Normalizes legal and trade names by:
    - Lowercasing and trimming
    - Expanding '&' to 'and'
    - Removing punctuation and special characters
    - Stripping common corporate suffixes (Pvt Ltd, LLC, Inc, etc.)
    - Collapsing multiple whitespace
    """
    if not name:
        return ""
    
    cleaned = name.lower().strip()
    cleaned = re.sub(r"&", " and ", cleaned)
    # Remove punctuation
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    
    # Strip business suffixes
    for pat in BUSINESS_SUFFIX_PATTERNS:
        cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE)
    
    # Collapse whitespace
    tokens = [t for t in cleaned.split() if t]
    return " ".join(tokens)

def get_name_tokens(norm_name: str) -> Set[str]:
    return set(norm_name.split())

class EvidenceReconciler:
    """
    Deterministically compares invoice claims against discovered public evidence.
    Produces granular field-by-field check results with explicit confidence and provenance.
    Strict Invariants:
    - Never mark a match merely because a trade_name field exists.
    - Missing evidence is UNAVAILABLE, never fabricated or treated as proof of fraud.
    - All comparisons use normalized corporate identifiers.
    """
    def reconcile(
        self,
        invoice: InvoiceClaim,
        evidence_items: List[EvidenceItem]
    ) -> List[FieldCheckResult]:
        checks = []

        # Find GST/Legal registry evidence (excluding UNAVAILABLE evidence)
        gst_evidence = next(
            (e for e in evidence_items if e.source_mode != SourceMode.UNAVAILABLE and ("gst" in e.source_name.lower() or "legal" in e.claim_supported.lower())),
            None
        )

        # -------------------------------------------------------------
        # 1. Trade Name vs Legal Entity Check (Strict Normalization)
        # -------------------------------------------------------------
        if gst_evidence and ("legal_name" in gst_evidence.facts or "trade_name" in gst_evidence.facts):
            evidence_legal = gst_evidence.facts.get("legal_name") or ""
            evidence_trade = gst_evidence.facts.get("trade_name") or ""
            inv_supplier = invoice.supplier_name or ""
            inv_legal = invoice.legal_name or ""

            norm_inv_supplier = normalize_business_name(inv_supplier)
            norm_inv_legal = normalize_business_name(inv_legal)
            norm_ev_legal = normalize_business_name(evidence_legal)
            norm_ev_trade = normalize_business_name(evidence_trade)

            tokens_inv = get_name_tokens(norm_inv_supplier)
            tokens_ev_legal = get_name_tokens(norm_ev_legal)
            tokens_ev_trade = get_name_tokens(norm_ev_trade) if norm_ev_trade else set()

            # Check for exact legal entity match
            if norm_inv_supplier and norm_inv_supplier == norm_ev_legal:
                checks.append(FieldCheckResult(
                    check_id="chk_name_match",
                    field_name="Supplier Identity",
                    invoice_value=inv_supplier,
                    evidence_value=evidence_legal,
                    status=CheckStatus.MATCH,
                    explanation=f"Invoice trade name '{inv_supplier}' matches registered corporate legal entity name exactly.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url,
                    source_mode=gst_evidence.source_mode,
                    is_fallback=gst_evidence.is_fallback
                ))
            elif norm_inv_legal and norm_inv_legal == norm_ev_legal:
                checks.append(FieldCheckResult(
                    check_id="chk_name_match",
                    field_name="Supplier Identity",
                    invoice_value=inv_legal,
                    evidence_value=evidence_legal,
                    status=CheckStatus.MATCH,
                    explanation=f"Invoice legal name '{inv_legal}' matches registered corporate legal entity name exactly.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url,
                    source_mode=gst_evidence.source_mode,
                    is_fallback=gst_evidence.is_fallback
                ))
            elif norm_ev_trade and norm_inv_supplier == norm_ev_trade:
                # Registered trade alias match, but differs from corporate legal entity
                checks.append(FieldCheckResult(
                    check_id="chk_legal_name_discrepancy",
                    field_name="Trade vs Legal Name",
                    invoice_value=inv_supplier,
                    evidence_value=evidence_legal,
                    status=CheckStatus.POSSIBLE_MATCH,
                    reason_code="LEGAL_NAME_MISMATCH",
                    explanation=(
                        f"Invoice uses registered trade name '{inv_supplier}', whereas public registry lists corporate entity "
                        f"'{evidence_legal}'. Corroborated registered trade alias requires verification of bank beneficiary."
                    ),
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url,
                    source_mode=gst_evidence.source_mode,
                    is_fallback=gst_evidence.is_fallback
                ))
            else:
                # Check for possible match / trade alias overlap
                overlap_legal = tokens_inv.intersection(tokens_ev_legal)
                overlap_trade = tokens_inv.intersection(tokens_ev_trade) if tokens_ev_trade else set()

                if overlap_trade or (overlap_legal and len(overlap_legal) >= 1 and (norm_inv_supplier in norm_ev_legal or norm_ev_legal in norm_inv_supplier)):
                    matched_alias = evidence_trade if overlap_trade else evidence_legal
                    checks.append(FieldCheckResult(
                        check_id="chk_legal_name_discrepancy",
                        field_name="Trade vs Legal Name",
                        invoice_value=inv_supplier,
                        evidence_value=evidence_legal,
                        status=CheckStatus.POSSIBLE_MATCH,
                        reason_code="LEGAL_NAME_MISMATCH",
                        explanation=(
                            f"Invoice cites trade name '{inv_supplier}', whereas public registry lists legal entity "
                            f"'{evidence_legal}' (registered trade alias: '{evidence_trade or 'None'}'). "
                            f"Shared root tokens: {sorted(list(overlap_legal | overlap_trade))}. Reviewer should verify DBA / alias documentation."
                        ),
                        evidence_id=gst_evidence.evidence_id,
                        source_url=gst_evidence.source_url,
                        source_mode=gst_evidence.source_mode,
                        is_fallback=gst_evidence.is_fallback
                    ))
                else:
                    # Clear conflict / mismatch
                    checks.append(FieldCheckResult(
                        check_id="chk_name_mismatch",
                        field_name="Supplier Identity",
                        invoice_value=inv_supplier,
                        evidence_value=evidence_legal or "Unregistered",
                        status=CheckStatus.MISMATCH,
                        reason_code="CRITICAL_NAME_MISMATCH",
                        explanation=(
                            f"Invoice supplier '{inv_supplier}' does not match legal entity '{evidence_legal}' "
                            f"or trade name '{evidence_trade}' found in authoritative GST records."
                        ),
                        evidence_id=gst_evidence.evidence_id,
                        source_url=gst_evidence.source_url,
                        source_mode=gst_evidence.source_mode,
                        is_fallback=gst_evidence.is_fallback
                    ))
        else:
            # Evidence was not found or unavailable
            source_mode = gst_evidence.source_mode if gst_evidence else SourceMode.UNAVAILABLE
            checks.append(FieldCheckResult(
                check_id="chk_name_unknown",
                field_name="Supplier Identity",
                invoice_value=invoice.supplier_name,
                evidence_value=None,
                status=CheckStatus.UNAVAILABLE,
                reason_code="EVIDENCE_INSUFFICIENT",
                explanation="No authoritative public registry record found to verify legal entity. Does NOT prove fraud; secondary intake required.",
                source_mode=source_mode
            ))

        # -------------------------------------------------------------
        # 2. GST Registration Status
        # -------------------------------------------------------------
        if gst_evidence and "status" in gst_evidence.facts:
            reg_status = str(gst_evidence.facts["status"]).strip()
            norm_status = reg_status.lower()
            if "active" in norm_status:
                checks.append(FieldCheckResult(
                    check_id="chk_gst_active",
                    field_name="GST Registration Status",
                    invoice_value=invoice.gstin,
                    evidence_value=reg_status,
                    status=CheckStatus.MATCH,
                    explanation=f"Authoritative registry confirms GST registration is {reg_status}.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url,
                    source_mode=gst_evidence.source_mode,
                    is_fallback=gst_evidence.is_fallback
                ))
            elif any(s in norm_status for s in ["cancelled", "suspended", "inactive", "cancelled suo-moto", "cancelled suo moto"]):
                checks.append(FieldCheckResult(
                    check_id="chk_gst_inactive",
                    field_name="GST Registration Status",
                    invoice_value=invoice.gstin,
                    evidence_value=reg_status,
                    status=CheckStatus.MISMATCH,
                    reason_code="GST_STATUS_INACTIVE_CONFIRMED",
                    explanation=f"GST registration is listed as {reg_status}. Input Tax Credit (ITC) may be invalid or disallowed.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url,
                    source_mode=gst_evidence.source_mode,
                    is_fallback=gst_evidence.is_fallback
                ))
            else:
                checks.append(FieldCheckResult(
                    check_id="chk_gst_unknown",
                    field_name="GST Registration Status",
                    invoice_value=invoice.gstin,
                    evidence_value=reg_status,
                    status=CheckStatus.UNAVAILABLE,
                    reason_code="GST_STATUS_UNKNOWN",
                    explanation=f"GST registration status '{reg_status}' could not be definitively verified as active or inactive. Secondary verification required.",
                    evidence_id=gst_evidence.evidence_id,
                    source_url=gst_evidence.source_url,
                    source_mode=gst_evidence.source_mode,
                    is_fallback=gst_evidence.is_fallback
                ))
        else:
            source_mode = gst_evidence.source_mode if gst_evidence else SourceMode.UNAVAILABLE
            checks.append(FieldCheckResult(
                check_id="chk_gst_unknown",
                field_name="GST Registration Status",
                invoice_value=invoice.gstin,
                evidence_value=None,
                status=CheckStatus.UNAVAILABLE,
                reason_code="GST_STATUS_UNKNOWN",
                explanation="Could not confirm active registration from current accessible records. Secondary verification required.",
                source_mode=source_mode
            ))

        # -------------------------------------------------------------
        # 3. Bank Beneficiary Ownership Check (Strict Truth Invariant)
        # -------------------------------------------------------------
        bank_evidence = next(
            (e for e in evidence_items if "bank" in e.source_name.lower() or "ifsc" in e.claim_supported.lower()),
            None
        )
        if invoice.ifsc_code:
            bank_mode = bank_evidence.source_mode if bank_evidence else SourceMode.UNAVAILABLE
            checks.append(FieldCheckResult(
                check_id="chk_bank_ownership",
                field_name="Bank Beneficiary Ownership",
                invoice_value=f"IFSC: {invoice.ifsc_code} | A/C: {invoice.bank_account_masked or 'Not specified'}",
                evidence_value="Branch verified; Account Ownership Unverified",
                status=CheckStatus.POSSIBLE_MATCH,
                reason_code="BANK_OWNERSHIP_UNVERIFIED",
                explanation=(
                    "Public IFSC registry confirms bank branch validity, but CANNOT verify beneficiary account ownership. "
                    "Requires cancelled cheque verification, vendor master match, or penny-drop confirmation."
                ),
                evidence_id=bank_evidence.evidence_id if bank_evidence else None,
                source_url=bank_evidence.source_url if bank_evidence else None,
                source_mode=bank_mode,
                is_fallback=bank_evidence.is_fallback if bank_evidence else False
            ))

        # -------------------------------------------------------------
        # 4. Duplicate Invoice Check
        # -------------------------------------------------------------
        if invoice.duplicate_status:
            is_exact = "EXACT" in invoice.duplicate_status
            checks.append(FieldCheckResult(
                check_id="chk_duplicate_invoice",
                field_name="Duplicate Invoice Detection",
                invoice_value=f"Inv: {invoice.invoice_number} | SHA256: {invoice.file_sha256[:12] if invoice.file_sha256 else 'N/A'}",
                evidence_value=f"Status: {invoice.duplicate_status} (Ref: {invoice.duplicate_case_id or 'Previous intake'})",
                status=CheckStatus.MISMATCH if is_exact else CheckStatus.POSSIBLE_MATCH,
                reason_code="RULE_DUPLICATE_INVOICE_EXACT" if is_exact else "RULE_DUPLICATE_INVOICE_SUSPECT",
                explanation=(
                    f"Duplicate invoice detected: {invoice.duplicate_status}. "
                    f"Associated case reference: {invoice.duplicate_case_id or 'System records'}. "
                    "Reviewer must verify if this is an intentional resubmission, corrected bill, or duplicate billing."
                )
            ))

        return checks
