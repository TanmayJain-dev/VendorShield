import re
from typing import Optional, Dict, Any, List
from ...schemas.invoice import InvoiceClaim, LineItem
from ..validators.gstin_validator import validate_gstin_format
from ..validators.arithmetic_validator import validate_invoice_arithmetic

GSTIN_PATTERN = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b")
INVOICE_NUM_PATTERN = re.compile(r"(?:Invoice\s*(?:No|Number|#)[\s:]*|INV[-/])([A-Z0-9\-_/]+)", re.IGNORECASE)
IFSC_PATTERN = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")
AMOUNT_PATTERN = re.compile(r"(?:Total|Grand\s*Total|Invoice\s*Total)[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)", re.IGNORECASE)
ACCOUNT_NUM_PATTERN = re.compile(r"(?:A/C|Account\s*(?:No|Number)?)[\s:]*([0-9]{9,18})", re.IGNORECASE)

def mask_bank_account(account_num: str) -> str:
    """Masks all except the last 4 digits of a bank account number."""
    cleaned = re.sub(r"\D", "", account_num)
    if len(cleaned) <= 4:
        return "****"
    return f"XXXX-XXXX-{cleaned[-4:]}"

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts text using PyMuPDF (fitz) or falls back to UTF-8 decoding."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text
    except ImportError:
        # Fallback if PyMuPDF is not installed yet
        return pdf_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Extraction error: {str(e)}"

def parse_invoice_text(text: str, default_supplier: str = "Unknown Supplier") -> InvoiceClaim:
    """Extracts structured invoice claims from raw text."""
    # 1. GSTIN
    gstin_match = GSTIN_PATTERN.search(text)
    gstin = gstin_match.group(1) if gstin_match else None
    
    # 2. Invoice Number
    inv_match = INVOICE_NUM_PATTERN.search(text)
    invoice_number = inv_match.group(1) if inv_match else "INV-2026-UNKNOWN"
    
    # 3. Bank Account & IFSC
    acc_match = ACCOUNT_NUM_PATTERN.search(text)
    bank_account_masked = mask_bank_account(acc_match.group(1)) if acc_match else None
    
    ifsc_match = IFSC_PATTERN.search(text)
    ifsc_code = ifsc_match.group(1) if ifsc_match else None
    
    # 4. Total Amount
    amt_match = AMOUNT_PATTERN.search(text)
    total_amount = 0.0
    if amt_match:
        try:
            total_amount = float(amt_match.group(1).replace(",", ""))
        except ValueError:
            total_amount = 0.0
            
    # Derive tax and taxable assuming standard 18% GST if not separately identified
    taxable_amount = round(total_amount / 1.18, 2) if total_amount > 0 else 0.0
    cgst = round((total_amount - taxable_amount) / 2, 2)
    sgst = cgst
    igst = 0.0
    
    # Validate format and arithmetic
    gstin_valid, _ = validate_gstin_format(gstin) if gstin else (False, "Missing GSTIN")
    arith_valid, _ = validate_invoice_arithmetic(taxable_amount, cgst, sgst, igst, total_amount)
    
    return InvoiceClaim(
        invoice_number=invoice_number,
        supplier_name=default_supplier,
        gstin=gstin,
        taxable_amount=taxable_amount,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total_amount,
        bank_account_masked=bank_account_masked,
        ifsc_code=ifsc_code,
        gstin_format_valid=gstin_valid,
        arithmetic_valid=arith_valid,
        raw_text=text[:2000]  # Store excerpt
    )
