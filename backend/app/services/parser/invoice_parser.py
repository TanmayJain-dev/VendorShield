import re
import datetime
from typing import Optional, Dict, Any, List, Tuple
from ...schemas.invoice import InvoiceClaim, LineItem
from ..validators.gstin_validator import validate_gstin_format
from ..validators.arithmetic_validator import validate_invoice_arithmetic
from .ocr_fallback import process_scanned_pdf, is_page_likely_scanned

# Regex Patterns
GSTIN_PATTERN = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b")
SUPPLIER_GSTIN_PATTERN = re.compile(
    r"(?:Supplier|Seller|Vendor|From|Our)?\s*GSTIN(?:/UIN)?[\s:]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
    re.IGNORECASE
)
BUYER_GSTIN_PATTERN = re.compile(
    r"(?:Buyer|Customer|Client|Bill\s*To|Consignee)\s*GSTIN(?:/UIN)?[\s:]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
    re.IGNORECASE
)

INVOICE_NUM_PATTERN = re.compile(
    r"(?:Tax\s*Invoice\s*No\.?|Invoice\s*(?:No|Number|#)[\s.:]*|Bill\s*No\.?[\s.:]*|INV[-/])\s*([A-Z0-9\-_/]+)",
    re.IGNORECASE
)

DATE_PATTERN = re.compile(
    r"(?:Invoice\s*Date|Date\s*of\s*Invoice|Bill\s*Date|Dated?|Date)[\s.:]*"
    r"([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]{3,9}\s+[0-9]{4})",
    re.IGNORECASE
)

IFSC_PATTERN = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")
ACCOUNT_NUM_PATTERN = re.compile(
    r"(?:A/C|Account\s*(?:No|Number)?|Bank\s*A/c)[\s.:]*([0-9]{9,18})",
    re.IGNORECASE
)

# Amount patterns
TOTAL_AMOUNT_PATTERN = re.compile(
    r"(?:Grand\s*Total|Invoice\s*Total|Total\s*Amount|Net\s*Payable|Total\s*Due|Total)[\s.:]*"
    r"(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)

TAXABLE_AMOUNT_PATTERN = re.compile(
    r"(?:Taxable\s*(?:Amount|Value)|Sub\s*Total|Subtotal|Total\s*Before\s*Tax)[\s.:]*"
    r"(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)

CGST_PATTERN = re.compile(
    r"(?:CGST|Central\s*GST)[\s:]*(?:@\s*[\d.]+\s*%)?[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)

SGST_PATTERN = re.compile(
    r"(?:SGST|State\s*GST)[\s:]*(?:@\s*[\d.]+\s*%)?[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)

IGST_PATTERN = re.compile(
    r"(?:IGST|Integrated\s*GST)[\s:]*(?:@\s*[\d.]+\s*%)?[\s:]*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE
)

LEGAL_NAME_PATTERN = re.compile(
    r"(?:Legal\s*Name|Registered\s*Name|Company\s*Name|M/s\.?)[\s.:]+([A-Za-z0-9&.,\-\s]{3,60}?)(?:\n|$|,\s*GSTIN)",
    re.IGNORECASE
)

SUPPLIER_LABEL_PATTERN = re.compile(
    r"(?:Supplier|Seller|Vendor|Sold\s*By|Issued\s*By)[\s.:]+([A-Za-z0-9&.,\-\s]{3,60}?)(?:\n|$|,)",
    re.IGNORECASE
)

ADDRESS_PATTERN = re.compile(
    r"(?:Address|Supplier\s*Address|Vendor\s*Address|Billing\s*Address)[\s.:]+([^\n]+(?:\n[^\n]+){0,2})",
    re.IGNORECASE
)


def mask_bank_account(account_num: str) -> str:
    """Masks all except the last 4 digits of a bank account number (XXXX-XXXX-1234)."""
    if not account_num:
        return "XXXX-XXXX-0000"
    cleaned = re.sub(r"\D", "", account_num)
    if len(cleaned) <= 4:
        return "****"
    return f"XXXX-XXXX-{cleaned[-4:]}"


def normalize_date(raw_date: str) -> Optional[str]:
    """Attempts to normalize various date formats to ISO YYYY-MM-DD."""
    if not raw_date:
        return None
    cleaned = raw_date.strip()
    
    # Try ISO
    try:
        return datetime.datetime.strptime(cleaned, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
        
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%d %b %Y", "%d %B %Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    return cleaned


def clean_amount(val_str: Optional[str]) -> float:
    """Parses numeric amount from string, cleaning commas and symbols."""
    if not val_str:
        return 0.0
    try:
        cleaned = re.sub(r"[^\d.]", "", val_str.strip())
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts text using PyMuPDF (fitz) or falls back to OCR if scanned,
    or UTF-8 decoding as last resort.
    """
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        is_scanned = True
        
        for page in doc:
            page_text = page.get_text()
            if len(page_text.strip()) > 30:
                is_scanned = False
            text += page_text + "\n"

        # If PDF has no digital text layer or is scanned image
        if is_scanned or len(text.strip()) < 30:
            ocr_res = process_scanned_pdf(pdf_bytes)
            if ocr_res.text:
                return ocr_res.text
                
        return text
    except ImportError:
        return pdf_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Extraction error: {str(e)}"


def extract_tables_from_pdf(pdf_bytes: bytes) -> List[LineItem]:
    """
    Extracts tabular line items directly from PDF using PyMuPDF table finder.
    """
    line_items: List[LineItem] = []
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            try:
                tables = page.find_tables()
                for table in tables:
                    df = table.extract()
                    if not df or len(df) < 2:
                        continue
                    
                    header = [str(col).lower() if col else "" for col in df[0]]
                    desc_idx, qty_idx, price_idx, total_idx = -1, -1, -1, -1
                    
                    for idx, col_name in enumerate(header):
                        if any(k in col_name for k in ["desc", "item", "particular", "service"]):
                            desc_idx = idx
                        elif any(k in col_name for k in ["qty", "quantity"]):
                            qty_idx = idx
                        elif any(k in col_name for k in ["rate", "price", "unit"]):
                            price_idx = idx
                        elif any(k in col_name for k in ["amount", "total", "net"]):
                            total_idx = idx

                    # If table structure identified
                    if total_idx != -1 or desc_idx != -1:
                        for row in df[1:]:
                            if not row or len(row) <= max(desc_idx, total_idx):
                                continue
                            desc = str(row[desc_idx]).strip() if desc_idx != -1 and row[desc_idx] else "Item"
                            # Skip totals row
                            if any(k in desc.lower() for k in ["total", "subtotal", "tax", "gst"]):
                                continue
                                
                            qty = clean_amount(str(row[qty_idx])) if qty_idx != -1 and row[qty_idx] else 1.0
                            price = clean_amount(str(row[price_idx])) if price_idx != -1 and row[price_idx] else 0.0
                            tot = clean_amount(str(row[total_idx])) if total_idx != -1 and row[total_idx] else (qty * price)
                            
                            if tot > 0 or price > 0:
                                line_items.append(LineItem(
                                    description=desc,
                                    quantity=qty if qty > 0 else 1.0,
                                    unit_price=price if price > 0 else tot,
                                    total=tot if tot > 0 else (qty * price)
                                ))
            except Exception:
                continue
    except Exception:
        pass
    return line_items


def extract_line_items_from_text(text: str) -> List[LineItem]:
    """
    Regex heuristic line item extractor for text-only invoices.
    Detects rows of format: [Description] [Quantity] [Unit Price] [Total]
    """
    line_items: List[LineItem] = []
    # Pattern: Description followed by numbers (qty, price, total)
    line_pattern = re.compile(
        r"^(?:\d+[\s.)]+)?([A-Za-z0-9\s&/\-_]{3,40}?)\s+([0-9]{1,5}(?:\.[0-9]+)?)\s+([\d,]+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)$",
        re.MULTILINE
    )
    for match in line_pattern.finditer(text):
        desc = match.group(1).strip()
        if any(w in desc.lower() for w in ["total", "sub total", "tax", "cgst", "sgst", "igst", "balance"]):
            continue
        qty = clean_amount(match.group(2))
        price = clean_amount(match.group(3))
        total = clean_amount(match.group(4))
        if total > 0:
            line_items.append(LineItem(
                description=desc,
                quantity=qty if qty > 0 else 1.0,
                unit_price=price if price > 0 else total,
                total=total
            ))
    return line_items


def parse_invoice_text(text: str, default_supplier: str = "Unknown Supplier") -> InvoiceClaim:
    """Extracts structured invoice claims from raw text."""
    # 1. GSTIN (prioritize explicit supplier GSTIN over buyer)
    buyer_match = BUYER_GSTIN_PATTERN.search(text)
    buyer_gstin = buyer_match.group(1) if buyer_match else None
    
    supp_match = SUPPLIER_GSTIN_PATTERN.search(text)
    if supp_match:
        gstin = supp_match.group(1)
    else:
        # All occurrences
        all_gstins = GSTIN_PATTERN.findall(text)
        if all_gstins:
            # If buyer detected, pick the other one if available
            if buyer_gstin and len(all_gstins) > 1:
                filtered = [g for g in all_gstins if g != buyer_gstin]
                gstin = filtered[0] if filtered else all_gstins[0]
            else:
                gstin = all_gstins[0]
        else:
            gstin = None

    # 2. Invoice Number
    inv_match = INVOICE_NUM_PATTERN.search(text)
    invoice_number = inv_match.group(1).strip() if inv_match else "INV-2026-UNKNOWN"

    # 3. Invoice Date
    date_match = DATE_PATTERN.search(text)
    invoice_date = normalize_date(date_match.group(1)) if date_match else None

    # 4. Supplier Trade Name & Legal Name
    supplier_name = default_supplier
    legal_name = None
    
    legal_match = LEGAL_NAME_PATTERN.search(text)
    if legal_match:
        legal_name = legal_match.group(1).strip()

    supp_label_match = SUPPLIER_LABEL_PATTERN.search(text)
    if supp_label_match and default_supplier == "Unknown Supplier":
        supplier_name = supp_label_match.group(1).strip()
    elif default_supplier == "Unknown Supplier":
        # Heuristic: inspect top lines of invoice text
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:5]:
            if not any(k in line.lower() for k in ["tax invoice", "invoice", "gstin", "original", "bill"]):
                if len(line) > 3 and len(line) < 50:
                    supplier_name = line
                    break

    # 5. Billing Address
    addr_match = ADDRESS_PATTERN.search(text)
    billing_address = re.sub(r"\s+", " ", addr_match.group(1).strip()) if addr_match else None

    # 6. Bank Account & IFSC
    acc_match = ACCOUNT_NUM_PATTERN.search(text)
    bank_account_masked = mask_bank_account(acc_match.group(1)) if acc_match else None

    ifsc_match = IFSC_PATTERN.search(text)
    ifsc_code = ifsc_match.group(1) if ifsc_match else None

    # 7. Financial Totals & Taxes
    tot_match = TOTAL_AMOUNT_PATTERN.search(text)
    total_amount = clean_amount(tot_match.group(1)) if tot_match else 0.0

    taxable_match = TAXABLE_AMOUNT_PATTERN.search(text)
    taxable_amount = clean_amount(taxable_match.group(1)) if taxable_match else 0.0

    cgst_match = CGST_PATTERN.search(text)
    cgst = clean_amount(cgst_match.group(1)) if cgst_match else 0.0

    sgst_match = SGST_PATTERN.search(text)
    sgst = clean_amount(sgst_match.group(1)) if sgst_match else 0.0

    igst_match = IGST_PATTERN.search(text)
    igst = clean_amount(igst_match.group(1)) if igst_match else 0.0

    # Fallback tax derivation if total present but tax components missing from OCR/text
    if total_amount > 0 and taxable_amount == 0.0 and cgst == 0.0 and sgst == 0.0 and igst == 0.0:
        taxable_amount = round(total_amount / 1.18, 2)
        cgst = round((total_amount - taxable_amount) / 2, 2)
        sgst = cgst
        igst = 0.0
    elif taxable_amount > 0 and total_amount == 0.0:
        total_amount = round(taxable_amount + cgst + sgst + igst, 2)

    # 8. Line Items from text
    line_items = extract_line_items_from_text(text)

    # 9. Format & Arithmetic Validations
    gstin_valid, _ = validate_gstin_format(gstin) if gstin else (False, "Missing GSTIN")
    arith_valid, _ = validate_invoice_arithmetic(
        taxable_amount=taxable_amount,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total_amount,
        line_items=line_items
    )

    return InvoiceClaim(
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        supplier_name=supplier_name,
        legal_name=legal_name,
        gstin=gstin,
        billing_address=billing_address,
        taxable_amount=taxable_amount,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total_amount,
        bank_account_masked=bank_account_masked,
        ifsc_code=ifsc_code,
        line_items=line_items,
        gstin_format_valid=gstin_valid,
        arithmetic_valid=arith_valid,
        raw_text=text[:3000]
    )


def parse_invoice_pdf(pdf_bytes: bytes, default_supplier: str = "Unknown Supplier") -> InvoiceClaim:
    """
    End-to-end PDF parser:
    1. Extracts text layer (with OCR fallback for scanned PDFs)
    2. Extracts structured table line items via PyMuPDF
    3. Merges claims and executes deterministic validators
    """
    text = extract_text_from_pdf_bytes(pdf_bytes)
    claim = parse_invoice_text(text, default_supplier=default_supplier)
    
    # Try table extraction directly from PDF
    pdf_tables = extract_tables_from_pdf(pdf_bytes)
    if pdf_tables:
        claim.line_items = pdf_tables
        # Re-verify arithmetic with the table line items
        claim.arithmetic_valid, _ = validate_invoice_arithmetic(
            taxable_amount=claim.taxable_amount,
            cgst=claim.cgst,
            sgst=claim.sgst,
            igst=claim.igst,
            total_amount=claim.total_amount,
            line_items=claim.line_items
        )
        
    return claim
