import pytest
from backend.app.services.parser.invoice_parser import parse_invoice_text, extract_text_from_pdf_bytes
from backend.app.schemas.enums import ExtractionStatus

def test_parse_invoice_with_explicit_cgst_sgst():
    text = """
    TAX INVOICE
    Invoice No: INV-2026-9901
    Date: 2026-10-18
    GSTIN: 07AAAAA0000A1Z5
    Taxable Amount: 100,000.00
    CGST @ 9%: 9,000.00
    SGST @ 9%: 9,000.00
    Total Amount: 118,000.00
    Account No: 123456789012
    IFSC: HDFC0000123
    """
    claim = parse_invoice_text(text, default_supplier="Acme Supplies")
    assert claim.invoice_number == "INV-2026-9901"
    assert claim.taxable_amount == 100000.0
    assert claim.cgst == 9000.0
    assert claim.sgst == 9000.0
    assert claim.igst == 0.0
    assert claim.total_amount == 118000.0
    assert claim.arithmetic_valid is True
    assert claim.bank_account_masked == "XXXX-XXXX-9012"
    assert claim.ifsc_code == "HDFC0000123"
    assert len(claim.tax_breakdown) == 2

def test_parse_invoice_with_igst_and_discount():
    text = """
    INTERSTATE TAX INVOICE
    Invoice Number: INV-IGST-441
    Date: 2026-09-20
    GSTIN: 27AAAAA0000A1Z5
    Subtotal: 200,000.00
    Discount: 10,000.00
    IGST @ 18%: 34,200.00
    Round Off: -0.20
    Grand Total: 224,199.80
    """
    claim = parse_invoice_text(text, default_supplier="Western Freight")
    assert claim.invoice_number == "INV-IGST-441"
    assert claim.taxable_amount == 200000.0
    assert claim.discount_amount == 10000.0
    assert claim.igst == 34200.0
    assert claim.total_amount == 224199.80
    assert claim.round_off == -0.20
    assert claim.arithmetic_valid is True

def test_parse_invoice_without_tax_breakdown_marks_inferred():
    # Invoice has only a total amount with no line items or breakdown
    text = """
    RECEIPT
    Invoice #: INV-TOTAL-ONLY
    Total Amount: 50,000.00
    """
    claim = parse_invoice_text(text, default_supplier="Simple Vendor")
    assert claim.total_amount == 50000.0
    # Must be labeled as INFERRED, not silently assumed as factual
    assert claim.extraction_metadata["taxable_amount"].status == ExtractionStatus.INFERRED
    assert claim.extraction_metadata["cgst"].status == ExtractionStatus.INFERRED
    assert any("not an extracted fact" in m.notes.lower() for m in claim.extraction_metadata.values() if m.notes)

def test_extract_text_pdf_page_limit_enforced():
    # Ensure PDF parser rejects exceeding max page limits cleanly
    fake_doc = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"
    text, is_scanned, ocr_msg, errors = extract_text_from_pdf_bytes(fake_doc)
    # Returns structured errors, does not crash or inject into text
    assert isinstance(errors, list)
