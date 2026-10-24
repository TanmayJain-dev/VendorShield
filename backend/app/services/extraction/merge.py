import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from ...schemas.invoice import InvoiceClaim, FieldExtractionMeta, TaxBreakdownItem, LineItem
from ...schemas.enums import ExtractionStatus
from ..validators.gstin_validator import validate_gstin_format
from ..validators.arithmetic_validator import validate_invoice_arithmetic
from .qr_einvoice import QrExtractionResult
from .text_layer import TextLayerResult

logger = logging.getLogger(__name__)

MATERIAL_FIELDS = ["supplier_gstin", "invoice_number", "total_amount", "invoice_date"]

def _normalize_str(val: Any) -> str:
    if val is None:
        return ""
    return re.sub(r"[\s\-_/.,]", "", str(val)).lower()

def _are_values_conflicting(field_name: str, val1: Any, val2: Any) -> bool:
    if val1 is None or val2 is None:
        return False
    if field_name in ["total_amount", "taxable_amount", "cgst", "sgst", "igst"]:
        try:
            f1 = float(val1)
            f2 = float(val2)
            if f1 > 0 and f2 > 0:
                return abs(f1 - f2) > 1.0
            return False
        except (ValueError, TypeError):
            return True
    
    # String normalization for GSTIN, invoice number, date
    s1 = _normalize_str(val1)
    s2 = _normalize_str(val2)
    if s1 and s2:
        return s1 != s2
    return False

def merge_extractions(
    qr_result: QrExtractionResult,
    text_result: TextLayerResult,
    llm_fields: Optional[Dict[str, Any]] = None,
    raw_file_bytes: Optional[bytes] = None,
    file_sha256: Optional[str] = None
) -> InvoiceClaim:
    """
    Merges layered extraction results with precedence QR > LLM > REGEX.
    Detects conflicts, constructs FieldExtractionMeta provenance, and runs validations.
    """
    llm_data = llm_fields or {}
    qr_data = qr_result.extracted_fields if qr_result.found else {}
    regex_data = text_result.extracted_fields

    merged: Dict[str, Any] = {}
    sources: Dict[str, str] = {}
    statuses: Dict[str, ExtractionStatus] = {}
    confidences: Dict[str, float] = {}
    conflicts: List[Dict[str, Any]] = []
    warnings: List[str] = list(text_result.parsing_warnings)
    errors: List[str] = list(text_result.parsing_errors)

    if qr_result.errors:
        warnings.extend(qr_result.errors)

    # All candidate keys
    all_keys = set(qr_data.keys()) | set(llm_data.keys()) | set(regex_data.keys())
    
    # Priority order: QR > LLM > REGEX
    for key in all_keys:
        val_qr = qr_data.get(key)
        val_llm = llm_data.get(key)
        val_regex = regex_data.get(key)

        # Detect material conflict
        has_conflict = False
        conflict_detail = None

        if key in MATERIAL_FIELDS:
            # Check pairwise conflicts among non-null values
            pairs = []
            if val_qr is not None:
                pairs.append(("QR", val_qr))
            if val_llm is not None:
                pairs.append(("LLM", val_llm))
            if val_regex is not None:
                pairs.append(("REGEX", val_regex))

            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    src_a, v_a = pairs[i]
                    src_b, v_b = pairs[j]
                    if _are_values_conflicting(key, v_a, v_b):
                        has_conflict = True
                        conflict_detail = {
                            "field": key,
                            "source_a": src_a,
                            "value_a": v_a,
                            "source_b": src_b,
                            "value_b": v_b,
                            "severity": "CRITICAL" if key in ["supplier_gstin", "invoice_number"] else "HIGH"
                        }
                        conflicts.append(conflict_detail)
                        warnings.append(f"EXTRACTION_CONFLICT: {key} disagrees between {src_a} ({v_a}) and {src_b} ({v_b})")
                        break
                if has_conflict:
                    break

        # Select winning value by precedence
        if val_qr is not None:
            merged[key] = val_qr
            sources[key] = "QR"
            statuses[key] = ExtractionStatus.CONFLICT if has_conflict else ExtractionStatus.EXTRACTED_QR
            confidences[key] = 0.7 if has_conflict else 1.0
        elif val_llm is not None:
            merged[key] = val_llm
            sources[key] = "LLM"
            statuses[key] = ExtractionStatus.CONFLICT if has_conflict else ExtractionStatus.EXTRACTED_LLM
            confidences[key] = 0.6 if has_conflict else 0.90
        elif val_regex is not None:
            merged[key] = val_regex
            sources[key] = "REGEX"
            statuses[key] = ExtractionStatus.CONFLICT if has_conflict else ExtractionStatus.EXTRACTED_REGEX
            confidences[key] = 0.5 if has_conflict else 0.85

    # Build FieldExtractionMeta map
    metadata: Dict[str, FieldExtractionMeta] = {}
    for k, v in merged.items():
        metadata[k] = FieldExtractionMeta(
            status=statuses.get(k, ExtractionStatus.EXTRACTED),
            confidence=confidences.get(k, 1.0),
            source=sources.get(k),
            extracted_value=v,
            source_text=str(v),
            notes="Extraction conflict detected" if statuses.get(k) == ExtractionStatus.CONFLICT else None
        )

    # Defaults for core fields
    # Ensure gstin alias exists in metadata
    if "supplier_gstin" in metadata and "gstin" not in metadata:
        metadata["gstin"] = metadata["supplier_gstin"]
    invoice_number = str(merged.get("invoice_number") or "UNKNOWN-INV").strip()
    supplier_name = str(merged.get("supplier_name") or "Unknown Supplier").strip()
    gstin = merged.get("supplier_gstin")
    buyer_gstin = merged.get("buyer_gstin")
    buyer_name = merged.get("buyer_name")
    total_amount = float(merged.get("total_amount") or 0.0)
    taxable_amount = float(merged.get("taxable_amount") or 0.0)
    cgst = float(merged.get("cgst") or 0.0)
    sgst = float(merged.get("sgst") or 0.0)
    igst = float(merged.get("igst") or 0.0)
    round_off = float(merged.get("round_off") or 0.0)
    discount = float(merged.get("discount_amount") or 0.0)

    # Validate GSTIN format
    gstin_valid = None
    if gstin:
        gstin_valid, _ = validate_gstin_format(gstin)

    # Validate arithmetic only if we have non-zero total or taxable
    arith_valid = None
    arith_notes = "ARITHMETIC_UNVERIFIED"
    if total_amount > 0 or taxable_amount > 0:
        arith_valid, arith_notes = validate_invoice_arithmetic(
            taxable_amount=taxable_amount,
            cgst=cgst,
            sgst=sgst,
            igst=igst,
            total_amount=total_amount,
            round_off=round_off,
            discount_amount=discount
        )

    # Construct tax breakdown
    tax_breakdown: List[TaxBreakdownItem] = []
    if cgst > 0:
        rate = round((cgst / taxable_amount * 100), 1) if taxable_amount > 0 else 9.0
        tax_breakdown.append(TaxBreakdownItem(
            tax_type="CGST",
            rate_pct=rate,
            taxable_amount=taxable_amount,
            tax_amount=cgst,
            status=statuses.get("cgst", ExtractionStatus.EXTRACTED)
        ))
    if sgst > 0:
        rate = round((sgst / taxable_amount * 100), 1) if taxable_amount > 0 else 9.0
        tax_breakdown.append(TaxBreakdownItem(
            tax_type="SGST",
            rate_pct=rate,
            taxable_amount=taxable_amount,
            tax_amount=sgst,
            status=statuses.get("sgst", ExtractionStatus.EXTRACTED)
        ))
    if igst > 0:
        rate = round((igst / taxable_amount * 100), 1) if taxable_amount > 0 else 18.0
        tax_breakdown.append(TaxBreakdownItem(
            tax_type="IGST",
            rate_pct=rate,
            taxable_amount=taxable_amount,
            tax_amount=igst,
            status=statuses.get("igst", ExtractionStatus.EXTRACTED)
        ))

    # Parse line items from LLM if available
    line_items: List[LineItem] = []
    raw_lines = llm_data.get("line_items", [])
    if isinstance(raw_lines, list):
        for li in raw_lines:
            if isinstance(li, dict) and "description" in li:
                line_items.append(LineItem(
                    description=str(li.get("description", "Item")),
                    quantity=float(li.get("quantity", 1.0)),
                    unit_price=float(li.get("unit_price", 0.0)),
                    total=float(li.get("total", li.get("taxable_value", 0.0))),
                    tax_rate=float(li.get("tax_rate", 0.0)) if li.get("tax_rate") is not None else None
                ))

    claim = InvoiceClaim(
        invoice_number=invoice_number,
        invoice_date=merged.get("invoice_date"),
        supplier_name=supplier_name,
        legal_name=merged.get("legal_name"),
        gstin=gstin,
        buyer_gstin=buyer_gstin,
        buyer_name=buyer_name,
        billing_address=merged.get("billing_address"),
        place_of_supply=merged.get("place_of_supply"),
        discount_amount=discount,
        round_off=round_off,
        taxable_amount=taxable_amount,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total_amount,
        tax_breakdown=tax_breakdown,
        bank_account_masked=merged.get("bank_account_masked"),
        ifsc_code=merged.get("ifsc_code"),
        line_items=line_items,
        gstin_format_valid=gstin_valid,
        arithmetic_valid=arith_valid,
        arithmetic_notes=arith_notes,
        raw_text=text_result.raw_text[:2000] if text_result.raw_text else None,
        tax_inferred=False,
        extraction_metadata=metadata,
        parsing_errors=errors,
        parsing_warnings=warnings,
        is_scanned_image=text_result.is_scanned,
        ocr_applied=text_result.is_scanned,
        ocr_status_message=text_result.ocr_status_message,
        file_sha256=file_sha256,
        irn=merged.get("irn"),
        qr_data=qr_result.raw_claims if qr_result.found else None,
        qr_signature_status=qr_result.qr_signature_status,
        extraction_conflicts=conflicts
    )

    return claim
