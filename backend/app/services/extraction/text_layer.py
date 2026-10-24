import re
import datetime
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from ...schemas.enums import ExtractionStatus
from ..validators.gstin_validator import validate_gstin_format
from ..validators.arithmetic_validator import validate_invoice_arithmetic

logger = logging.getLogger(__name__)

# Core Regex Patterns
GSTIN_REGEX = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b")
SUPPLIER_GSTIN_REGEX = re.compile(
    r"(?:Supplier|Seller|Vendor|From|Sold\s*By|Issued\s*By|Our)?\s*GSTIN(?:/UIN)?[\s:]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
    re.IGNORECASE
)
BUYER_GSTIN_REGEX = re.compile(
    r"(?:Buyer|Customer|Client|Bill\s*To|Billed\s*To|Consignee|Ship\s*To)\s*(?:Name)?[\s\S]{0,100}?GSTIN(?:/UIN)?[\s:]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
    re.IGNORECASE
)
INVOICE_NUM_REGEX = re.compile(
    r"(?:Tax\s*Invoice\s*No\.?|Invoice\s*(?:No|Number|#)[\s.:]*|Bill\s*(?:No|Number|#)[\s.:]*|INV[-/])\s*([A-Za-z0-9\-_/]+)",
    re.IGNORECASE
)
DATE_REGEX = re.compile(
    r"(?:Invoice\s*Date|Date\s*of\s*Invoice|Bill\s*Date|Dated?|Date)[\s.:]*"
    r"([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]{3,9}\s+[0-9]{4})",
    re.IGNORECASE
)
IFSC_REGEX = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")
ACCOUNT_NUM_REGEX = re.compile(r"(?:A/C|Account\s*(?:No|Number)?|Bank\s*A/c)[\s.:]*([0-9]{9,18})", re.IGNORECASE)

TOTAL_AMOUNT_REGEX = re.compile(
    r"(?<!Sub\s)(?<!Taxable\s)\b(?:Total\s*Invoice\s*Value|Grand\s*Total|Invoice\s*Total|Net\s*Payable|Total\s*Amount|Total\s*Due|Total)\b[\s.:]*"
    r"(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)
TAXABLE_AMOUNT_REGEX = re.compile(
    r"(?:Taxable\s*(?:Amount|Value)|Sub\s*Total|Subtotal|Total\s*Before\s*Tax)[\s.:]*"
    r"(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)
CGST_REGEX = re.compile(r"CGST(?:\s*(?:@|at)?\s*([0-9.]+)\s*%)?[\s.:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)
SGST_REGEX = re.compile(r"(?:SGST|UTGST|State\s*GST)(?:\s*(?:@|at)?\s*([0-9.]+)\s*%)?[\s.:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)
IGST_REGEX = re.compile(r"IGST(?:\s*(?:@|at)?\s*([0-9.]+)\s*%)?[\s.:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)
ROUND_OFF_REGEX = re.compile(r"(?:Round\s*Off|Rounding)[\s.:]*(?:₹|INR|Rs\.?)?\s*([+\-]?[\d,]+\.?\d*)", re.IGNORECASE)
DISCOUNT_REGEX = re.compile(r"(?:Discount)[\s.:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)

SUPPLIER_LABEL_REGEX = re.compile(
    r"(?:Supplier|Seller|Vendor|Sold\s*By|Issued\s*By)[\s.:]+([A-Za-z0-9&.,\-\s]{3,60}?)(?:\n|$|,)",
    re.IGNORECASE
)
BUYER_LABEL_REGEX = re.compile(
    r"(?:Buyer|Bill\s*To|Billed\s*To|Customer|Client|Consignee)[\s.:]+([A-Za-z0-9&.,\-\s]{3,60}?)(?:\n|$|,)",
    re.IGNORECASE
)

@dataclass
class TextLayerResult:
    raw_text: str = ""
    is_scanned: bool = False
    ocr_status_message: Optional[str] = None
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    field_sources: Dict[str, str] = field(default_factory=dict)
    parsing_errors: List[str] = field(default_factory=list)
    parsing_warnings: List[str] = field(default_factory=list)

def normalize_date(raw_date: Optional[str]) -> Optional[str]:
    if not raw_date:
        return None
    cleaned = raw_date.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%d %b %Y", "%d %B %Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return cleaned

def clean_amount(val_str: Optional[str]) -> float:
    if not val_str:
        return 0.0
    try:
        cleaned = re.sub(r"[^\d.]", "", str(val_str).strip())
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def mask_bank_account(account_num: Optional[str]) -> Optional[str]:
    if not account_num:
        return None
    cleaned = re.sub(r"\D", "", account_num)
    if len(cleaned) <= 4:
        return "****"
    return f"XXXX-XXXX-{cleaned[-4:]}"

def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, bool, Optional[str], List[str]]:
    """Extracts text from PDF bytes using PyMuPDF."""
    errors = []
    text = ""
    is_scanned = False
    ocr_msg = None

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        errors.append(f"PDF extraction error: {str(e)}")

    if not text.strip():
        is_scanned = True
        ocr_msg = "Document contains no extractable text layer (scanned or image PDF)."
    return text, is_scanned, ocr_msg, errors

def disambiguate_gstins(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Disambiguates supplier GSTIN vs buyer GSTIN based on section headings and positions.
    Returns (supplier_gstin, buyer_gstin).
    """
    all_gstins = list(dict.fromkeys(GSTIN_REGEX.findall(text)))  # Preserves first appearance order
    if not all_gstins:
        return None, None
    if len(all_gstins) == 1:
        # Check if explicitly buyer
        buyer_m = BUYER_GSTIN_REGEX.search(text)
        if buyer_m and buyer_m.group(1).upper() == all_gstins[0].upper():
            return None, all_gstins[0].upper()
        return all_gstins[0].upper(), None

    # Multiple GSTINs found
    supplier_gstin = None
    buyer_gstin = None

    # Check explicit patterns
    sup_m = SUPPLIER_GSTIN_REGEX.search(text)
    if sup_m:
        supplier_gstin = sup_m.group(1).upper()

    buy_m = BUYER_GSTIN_REGEX.search(text)
    if buy_m:
        buyer_gstin = buy_m.group(1).upper()

    # If both matched cleanly
    if supplier_gstin and buyer_gstin and supplier_gstin != buyer_gstin:
        return supplier_gstin, buyer_gstin

    # Split text roughly around "Bill To" / "Buyer"
    bill_to_idx = -1
    for marker in ["bill to", "billed to", "buyer", "customer", "consignee"]:
        idx = text.lower().find(marker)
        if idx != -1:
            bill_to_idx = idx
            break

    if bill_to_idx != -1:
        header_text = text[:bill_to_idx]
        body_text = text[bill_to_idx:]
        header_gstins = GSTIN_REGEX.findall(header_text)
        body_gstins = GSTIN_REGEX.findall(body_text)

        if header_gstins:
            supplier_gstin = header_gstins[0].upper()
        if body_gstins:
            buyer_gstin = body_gstins[0].upper()

    # Fallback to positional order
    if not supplier_gstin and all_gstins:
        supplier_gstin = all_gstins[0].upper()
    if not buyer_gstin and len(all_gstins) > 1:
        buyer_gstin = all_gstins[1].upper()

    return supplier_gstin, buyer_gstin

def extract_supplier_name(text: str, default_name: Optional[str] = None) -> Optional[str]:
    """Extracts supplier name without blindly defaulting to first line."""
    m = SUPPLIER_LABEL_REGEX.search(text)
    if m:
        candidate = m.group(1).strip()
        if len(candidate) > 2 and not candidate.lower().startswith(("gstin", "tax", "invoice", "date")):
            return candidate

    # Look for corporate suffixes in the first 10 lines
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    ignore_headers = {"tax invoice", "invoice", "original for recipient", "bill of supply", "cash memo", "quotation"}
    for line in lines[:8]:
        if line.lower() in ignore_headers:
            continue
        if re.search(r"\b(pvt|ltd|limited|llc|enterprises|logistics|corp|corporation|technologies|solutions|services|company)\b", line, re.IGNORECASE):
            return line

    return default_name

def extract_text_layer(text: str, is_scanned: bool = False, ocr_msg: Optional[str] = None) -> TextLayerResult:
    """Parses invoice fields from extracted text using regex rules."""
    result = TextLayerResult(
        raw_text=text,
        is_scanned=is_scanned,
        ocr_status_message=ocr_msg
    )
    
    if not text.strip():
        return result

    fields = {}

    # Disambiguate GSTINs
    sup_gstin, buy_gstin = disambiguate_gstins(text)
    if sup_gstin:
        fields["supplier_gstin"] = sup_gstin
    if buy_gstin:
        fields["buyer_gstin"] = buy_gstin

    # Supplier name
    sup_name = extract_supplier_name(text)
    if sup_name:
        fields["supplier_name"] = sup_name

    # Buyer name
    buy_m = BUYER_LABEL_REGEX.search(text)
    if buy_m:
        cand_buyer = buy_m.group(1).strip()
        if len(cand_buyer) > 2 and not cand_buyer.lower().startswith(("gstin", "invoice", "date")):
            fields["buyer_name"] = cand_buyer

    # Invoice number
    inv_m = INVOICE_NUM_REGEX.search(text)
    if inv_m:
        fields["invoice_number"] = inv_m.group(1).strip().strip(".,-")

    # Date
    date_m = DATE_REGEX.search(text)
    if date_m:
        norm_date = normalize_date(date_m.group(1))
        if norm_date:
            fields["invoice_date"] = norm_date

    # Amounts
    tot_m = TOTAL_AMOUNT_REGEX.search(text)
    if tot_m:
        fields["total_amount"] = clean_amount(tot_m.group(1))

    taxable_m = TAXABLE_AMOUNT_REGEX.search(text)
    if taxable_m:
        fields["taxable_amount"] = clean_amount(taxable_m.group(1))

    cgst_m = CGST_REGEX.search(text)
    if cgst_m:
        fields["cgst"] = clean_amount(cgst_m.group(2))

    sgst_m = SGST_REGEX.search(text)
    if sgst_m:
        fields["sgst"] = clean_amount(sgst_m.group(2))

    igst_m = IGST_REGEX.search(text)
    if igst_m:
        fields["igst"] = clean_amount(igst_m.group(2))

    round_m = ROUND_OFF_REGEX.search(text)
    if round_m:
        fields["round_off"] = clean_amount(round_m.group(1))

    disc_m = DISCOUNT_REGEX.search(text)
    if disc_m:
        fields["discount_amount"] = clean_amount(disc_m.group(1))

    # Bank Details
    ifsc_m = IFSC_REGEX.search(text)
    if ifsc_m:
        fields["ifsc_code"] = ifsc_m.group(1).upper()

    acc_m = ACCOUNT_NUM_REGEX.search(text)
    if acc_m:
        fields["bank_account_masked"] = mask_bank_account(acc_m.group(1))

    result.extracted_fields = fields
    result.field_sources = {k: "REGEX" for k in fields.keys()}
    return result
