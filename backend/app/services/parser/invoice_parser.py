import re
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from ...schemas.invoice import (
    InvoiceClaim, LineItem, TaxBreakdownItem, FieldExtractionMeta
)
from ...schemas.enums import ExtractionStatus
from ..validators.gstin_validator import validate_gstin_format
from ..validators.arithmetic_validator import validate_invoice_arithmetic

GSTIN_PATTERN = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b")
INVOICE_NUM_PATTERN = re.compile(
    r"(?:Invoice\s*(?:No|Number|#)[\s:]*|Bill\s*(?:No|Number|#)[\s:]*|INV[-/])([A-Z0-9\-_/]+)",
    re.IGNORECASE
)
INVOICE_DATE_PATTERN = re.compile(
    r"(?:Invoice\s*Date|Date\s*of\s*Invoice|Date)[\s:]*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{2}[-/][0-9]{2}[-/][0-9]{4})",
    re.IGNORECASE
)
IFSC_PATTERN = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")
ACCOUNT_NUM_PATTERN = re.compile(r"(?:A/C|Account\s*(?:No|Number)?)[\s:]*([0-9]{9,18})", re.IGNORECASE)
TOTAL_AMOUNT_PATTERN = re.compile(
    r"(?<!Sub)\b(?:Total\s*Invoice\s*Value|Grand\s*Total|Invoice\s*Total|Net\s*Payable|Total\s*Amount|Total)\b[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)
TAXABLE_AMOUNT_PATTERN = re.compile(
    r"(?:Taxable\s*(?:Value|Amount)|Subtotal|Total\s*Before\s*Tax)[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)

# Explicit Tax Patterns
CGST_PATTERN = re.compile(r"CGST(?:\s*(?:@|at)?\s*([0-9.]+)\s*%)?[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)
SGST_PATTERN = re.compile(r"(?:SGST|UTGST)(?:\s*(?:@|at)?\s*([0-9.]+)\s*%)?[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)
IGST_PATTERN = re.compile(r"IGST(?:\s*(?:@|at)?\s*([0-9.]+)\s*%)?[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)
ROUND_OFF_PATTERN = re.compile(r"(?:Round\s*Off|Rounding)[\s:]*(?:₹|INR|Rs\.?)?\s*([+\-]?[\d,]+\.?\d*)", re.IGNORECASE)
DISCOUNT_PATTERN = re.compile(r"(?:Discount)[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)

def mask_bank_account(account_num: str) -> str:
    cleaned = re.sub(r"\D", "", account_num)
    if len(cleaned) <= 4:
        return "****"
    return f"XXXX-XXXX-{cleaned[-4:]}"

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> Tuple[str, bool, Optional[str], List[str]]:
    """
    Extracts text from PDF bytes safely.
    Returns:
        (extracted_text, is_scanned_image, ocr_status_message, errors)
    """
    errors = []
    text = ""
    is_scanned_image = False
    ocr_status_message = None

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Check page count
        if doc.page_count > 25:
            errors.append(f"PDF exceeds maximum page limit of 25 (detected {doc.page_count} pages)")
            return "", False, None, errors

        for page in doc:
            text += page.get_text() + "\n"

        # Detect scanned/empty text PDF
        stripped_text = text.strip()
        if len(stripped_text) < 30 and doc.page_count > 0:
            is_scanned_image = True
            # Attempt OCR with pytesseract if available
            ocr_text = ""
            try:
                import pytesseract
                from PIL import Image
                import io
                for page in doc:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    ocr_text += pytesseract.image_to_string(img) + "\n"
                if ocr_text.strip():
                    text = ocr_text
                    ocr_status_message = "OCR text extracted successfully from scanned image."
            except Exception:
                ocr_status_message = (
                    "Scanned document / image detected with no embedded text layer. "
                    "OCR runtime unavailable. Please use the manual correction panel to verify claims."
                )

        doc.close()
        return text, is_scanned_image, ocr_status_message, errors

    except Exception as e:
        # Fallback to UTF-8 decoding if not a valid PDF or fitz fails
        errors.append(f"PDF parsing error: {str(e)}")
        try:
            fallback_text = pdf_bytes.decode("utf-8", errors="ignore")
            return fallback_text, False, None, errors
        except Exception:
            return "", False, None, errors

def parse_invoice_text(
    text: str,
    default_supplier: str = "Unknown Supplier",
    file_bytes: Optional[bytes] = None,
    is_scanned_image: bool = False,
    ocr_status_message: Optional[str] = None,
    parsing_errors: Optional[List[str]] = None
) -> InvoiceClaim:
    """
    Extracts structured invoice claims from raw text.
    Strictly labels values as EXTRACTED, CALCULATED, INFERRED, or UNAVAILABLE.
    Does NOT assume 18% GST by default.
    """
    errors = list(parsing_errors or [])
    warnings: List[str] = []
    extraction_meta: Dict[str, FieldExtractionMeta] = {}
    tax_breakdown: List[TaxBreakdownItem] = []

    file_sha256 = None
    if file_bytes:
        file_sha256 = hashlib.sha256(file_bytes).hexdigest()

    # 1. GSTIN
    gstin_match = GSTIN_PATTERN.search(text)
    if gstin_match:
        gstin = gstin_match.group(1).upper()
        extraction_meta["gstin"] = FieldExtractionMeta(
            status=ExtractionStatus.EXTRACTED,
            confidence=0.95,
            source_text=gstin
        )
    else:
        gstin = None
        extraction_meta["gstin"] = FieldExtractionMeta(
            status=ExtractionStatus.UNAVAILABLE,
            confidence=0.0,
            notes="No GSTIN found in document"
        )
        warnings.append("No GSTIN found in invoice text")

    # 2. Invoice Number
    inv_match = INVOICE_NUM_PATTERN.search(text)
    if inv_match:
        invoice_number = inv_match.group(1).strip()
        extraction_meta["invoice_number"] = FieldExtractionMeta(
            status=ExtractionStatus.EXTRACTED,
            confidence=0.9,
            source_text=inv_match.group(0)
        )
    else:
        invoice_number = "INV-UNKNOWN"
        extraction_meta["invoice_number"] = FieldExtractionMeta(
            status=ExtractionStatus.UNAVAILABLE,
            confidence=0.0,
            notes="Invoice number pattern not found"
        )
        warnings.append("Invoice number could not be extracted; placeholder assigned")

    # 3. Invoice Date
    date_match = INVOICE_DATE_PATTERN.search(text)
    invoice_date = date_match.group(1).strip() if date_match else None
    if invoice_date:
        extraction_meta["invoice_date"] = FieldExtractionMeta(
            status=ExtractionStatus.EXTRACTED,
            confidence=0.85,
            source_text=date_match.group(0)
        )
    else:
        extraction_meta["invoice_date"] = FieldExtractionMeta(
            status=ExtractionStatus.UNAVAILABLE,
            confidence=0.0
        )

    # 4. Bank Account & IFSC
    acc_match = ACCOUNT_NUM_PATTERN.search(text)
    bank_account_masked = mask_bank_account(acc_match.group(1)) if acc_match else None
    if bank_account_masked:
        extraction_meta["bank_account"] = FieldExtractionMeta(
            status=ExtractionStatus.EXTRACTED,
            confidence=0.85,
            notes="Bank account extracted and masked"
        )
    else:
        extraction_meta["bank_account"] = FieldExtractionMeta(
            status=ExtractionStatus.UNAVAILABLE,
            confidence=0.0
        )

    ifsc_match = IFSC_PATTERN.search(text)
    ifsc_code = ifsc_match.group(1).upper() if ifsc_match else None
    if ifsc_code:
        extraction_meta["ifsc_code"] = FieldExtractionMeta(
            status=ExtractionStatus.EXTRACTED,
            confidence=0.9,
            source_text=ifsc_code
        )
    else:
        extraction_meta["ifsc_code"] = FieldExtractionMeta(
            status=ExtractionStatus.UNAVAILABLE,
            confidence=0.0
        )

    # 5. Total Amount
    amt_match = TOTAL_AMOUNT_PATTERN.search(text)
    total_amount = 0.0
    if amt_match:
        try:
            total_amount = float(amt_match.group(1).replace(",", ""))
            extraction_meta["total_amount"] = FieldExtractionMeta(
                status=ExtractionStatus.EXTRACTED,
                confidence=0.9,
                source_text=amt_match.group(0)
            )
        except ValueError:
            total_amount = 0.0
            errors.append(f"Failed to parse total amount '{amt_match.group(1)}'")
    else:
        extraction_meta["total_amount"] = FieldExtractionMeta(
            status=ExtractionStatus.UNAVAILABLE,
            confidence=0.0,
            notes="Total amount not found"
        )
        warnings.append("Total amount not found in document")

    # 6. Taxable Amount
    taxable_match = TAXABLE_AMOUNT_PATTERN.search(text)
    taxable_amount = 0.0
    taxable_extracted = False
    if taxable_match:
        try:
            taxable_amount = float(taxable_match.group(1).replace(",", ""))
            taxable_extracted = True
            extraction_meta["taxable_amount"] = FieldExtractionMeta(
                status=ExtractionStatus.EXTRACTED,
                confidence=0.85,
                source_text=taxable_match.group(0)
            )
        except ValueError:
            taxable_amount = 0.0

    # 7. Explicit Tax Breakdowns (CGST, SGST, IGST)
    cgst = 0.0
    sgst = 0.0
    igst = 0.0
    cgst_extracted = False
    sgst_extracted = False
    igst_extracted = False

    cgst_match = CGST_PATTERN.search(text)
    if cgst_match:
        try:
            cgst_rate = float(cgst_match.group(1)) if cgst_match.group(1) else 9.0
            cgst = float(cgst_match.group(2).replace(",", ""))
            cgst_extracted = True
            tax_breakdown.append(TaxBreakdownItem(
                tax_type="CGST",
                rate_pct=cgst_rate,
                taxable_amount=taxable_amount,
                tax_amount=cgst,
                status=ExtractionStatus.EXTRACTED
            ))
            extraction_meta["cgst"] = FieldExtractionMeta(
                status=ExtractionStatus.EXTRACTED,
                confidence=0.9,
                source_text=cgst_match.group(0)
            )
        except Exception:
            pass

    sgst_match = SGST_PATTERN.search(text)
    if sgst_match:
        try:
            sgst_rate = float(sgst_match.group(1)) if sgst_match.group(1) else 9.0
            sgst = float(sgst_match.group(2).replace(",", ""))
            sgst_extracted = True
            tax_breakdown.append(TaxBreakdownItem(
                tax_type="SGST",
                rate_pct=sgst_rate,
                taxable_amount=taxable_amount,
                tax_amount=sgst,
                status=ExtractionStatus.EXTRACTED
            ))
            extraction_meta["sgst"] = FieldExtractionMeta(
                status=ExtractionStatus.EXTRACTED,
                confidence=0.9,
                source_text=sgst_match.group(0)
            )
        except Exception:
            pass

    igst_match = IGST_PATTERN.search(text)
    if igst_match:
        try:
            igst_rate = float(igst_match.group(1)) if igst_match.group(1) else 18.0
            igst = float(igst_match.group(2).replace(",", ""))
            igst_extracted = True
            tax_breakdown.append(TaxBreakdownItem(
                tax_type="IGST",
                rate_pct=igst_rate,
                taxable_amount=taxable_amount,
                tax_amount=igst,
                status=ExtractionStatus.EXTRACTED
            ))
            extraction_meta["igst"] = FieldExtractionMeta(
                status=ExtractionStatus.EXTRACTED,
                confidence=0.9,
                source_text=igst_match.group(0)
            )
        except Exception:
            pass

    # Round off & discounts
    round_off = 0.0
    ro_match = ROUND_OFF_PATTERN.search(text)
    if ro_match:
        try:
            round_off = float(ro_match.group(1).replace(",", ""))
        except Exception:
            round_off = 0.0

    discount_amount = 0.0
    disc_match = DISCOUNT_PATTERN.search(text)
    if disc_match:
        try:
            discount_amount = float(disc_match.group(1).replace(",", ""))
        except Exception:
            discount_amount = 0.0

    # 8. Handling Un-extracted Tax: DO NOT SILENTLY ASSUME 18% GST AS GROUND TRUTH
    if not (cgst_extracted or sgst_extracted or igst_extracted):
        if taxable_extracted and total_amount > taxable_amount:
            # Remaining difference is tax, but rate/split is not stated
            diff_tax = round(total_amount - taxable_amount - round_off + discount_amount, 2)
            warnings.append(
                f"Tax breakdown is not explicitly detailed in invoice text. Residual tax amount: ₹{diff_tax:.2f}."
            )
            extraction_meta["cgst"] = FieldExtractionMeta(
                status=ExtractionStatus.UNAVAILABLE,
                confidence=0.0,
                notes="Tax rate / split unstated in document"
            )
            extraction_meta["sgst"] = FieldExtractionMeta(
                status=ExtractionStatus.UNAVAILABLE,
                confidence=0.0,
                notes="Tax rate / split unstated in document"
            )
            extraction_meta["igst"] = FieldExtractionMeta(
                status=ExtractionStatus.UNAVAILABLE,
                confidence=0.0,
                notes="Tax rate / split unstated in document"
            )
        elif total_amount > 0 and not taxable_extracted:
            # Total only: Mark taxable and tax as INFERRED estimate, never as ground truth!
            taxable_amount = round(total_amount / 1.18, 2)
            inferred_tax = round(total_amount - taxable_amount, 2)
            cgst = round(inferred_tax / 2, 2)
            sgst = cgst
            igst = 0.0
            warnings.append(
                "Neither taxable amount nor tax breakdown was found in document. "
                "Tax figures are rough 18% estimations for guidance only; human confirmation required."
            )
            extraction_meta["taxable_amount"] = FieldExtractionMeta(
                status=ExtractionStatus.INFERRED,
                confidence=0.3,
                notes="Inferred approximation; not an extracted fact."
            )
            extraction_meta["cgst"] = FieldExtractionMeta(
                status=ExtractionStatus.INFERRED,
                confidence=0.3,
                notes="Inferred 9% approximation; not an extracted fact."
            )
            extraction_meta["sgst"] = FieldExtractionMeta(
                status=ExtractionStatus.INFERRED,
                confidence=0.3,
                notes="Inferred 9% approximation; not an extracted fact."
            )
            extraction_meta["igst"] = FieldExtractionMeta(
                status=ExtractionStatus.UNAVAILABLE,
                confidence=0.0
            )

    # 9. Format & Arithmetic Validations
    gstin_valid, _ = validate_gstin_format(gstin) if gstin else (False, "Missing GSTIN")
    arith_valid, arith_notes = validate_invoice_arithmetic(
        taxable_amount=taxable_amount,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total_amount,
        round_off=round_off,
        discount_amount=discount_amount
    )

    return InvoiceClaim(
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        supplier_name=default_supplier,
        gstin=gstin,
        discount_amount=discount_amount,
        round_off=round_off,
        taxable_amount=taxable_amount,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total_amount,
        tax_breakdown=tax_breakdown,
        bank_account_masked=bank_account_masked,
        ifsc_code=ifsc_code,
        gstin_format_valid=gstin_valid,
        arithmetic_valid=arith_valid,
        arithmetic_notes=arith_notes,
        raw_text=text[:3000],
        extraction_metadata=extraction_meta,
        parsing_errors=errors,
        parsing_warnings=warnings,
        is_scanned_image=is_scanned_image,
        ocr_applied=bool(ocr_status_message and "successfully" in ocr_status_message),
        ocr_status_message=ocr_status_message,
        file_sha256=file_sha256
    )
