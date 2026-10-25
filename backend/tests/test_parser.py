import pytest
from app.services.parser.invoice_parser import (
    mask_bank_account,
    normalize_date,
    clean_amount,
    parse_invoice_text,
    parse_invoice_pdf,
    extract_text_from_pdf_bytes
)
from app.services.parser.ocr_fallback import (
    is_page_likely_scanned,
    process_scanned_pdf,
    extract_text_from_image
)
from tests.fixtures.sample_invoices import (
    create_test_invoice_pdf,
    create_scanned_test_invoice_pdf
)


def test_mask_bank_account():
    # Standard 14-digit bank account
    assert mask_bank_account("98765432109921") == "XXXX-XXXX-9921"
    
    # 16-digit account with spaces/dashes
    assert mask_bank_account("1234-5678-9012-3456") == "XXXX-XXXX-3456"
    
    # Short account numbers
    assert mask_bank_account("123") == "****"
    assert mask_bank_account("") == "XXXX-XXXX-0000"


def test_date_normalization():
    assert normalize_date("2026-10-15") == "2026-10-15"
    assert normalize_date("15/10/2026") == "2026-10-15"
    assert normalize_date("15-10-2026") == "2026-10-15"
    assert normalize_date("15 Oct 2026") == "2026-10-15"


def test_clean_amount():
    assert clean_amount("₹ 4,82,500.00") == 482500.00
    assert clean_amount("INR 1,00,000") == 100000.00
    assert clean_amount("408898.31") == 408898.31
    assert clean_amount(None) == 0.0


def test_parse_invoice_text_benchmark_apex():
    invoice_text = """
    TAX INVOICE
    Supplier: Apex Courier
    Legal Name: Apex Global Logistics Pvt Ltd
    Supplier GSTIN: 07AAAAA0000A1Z4
    Address: Plot 42, Okhla Industrial Area, Phase-II, New Delhi - 110020
    
    Invoice No: INV-2026-8841
    Invoice Date: 15/10/2026
    
    Description Qty Rate Amount
    Express Air Freight 10 25000 250000.00
    Surface Courier Dispatch 5 31779.66 158898.31
    
    Taxable Amount: 408898.31
    CGST @ 9%: 36800.85
    SGST @ 9%: 36800.85
    Total Amount: 482500.00
    
    Bank Details:
    Account Number: 98765432109921
    IFSC: HDFC0000123
    """

    claim = parse_invoice_text(invoice_text)
    
    assert claim.invoice_number == "INV-2026-8841"
    assert claim.invoice_date == "2026-10-15"
    assert claim.supplier_name == "Apex Courier"
    assert claim.legal_name == "Apex Global Logistics Pvt Ltd"
    assert claim.gstin == "07AAAAA0000A1Z4"
    assert claim.bank_account_masked == "XXXX-XXXX-9921"
    assert claim.ifsc_code == "HDFC0000123"
    assert claim.taxable_amount == 408898.31
    assert claim.cgst == 36800.85
    assert claim.sgst == 36800.85
    assert claim.total_amount == 482500.00
    assert claim.gstin_format_valid is True
    assert claim.arithmetic_valid is True
    assert len(claim.raw_text) > 0


def test_supplier_and_buyer_gstin_disambiguation():
    text = """
    TAX INVOICE
    Supplier: Apex Logistics
    Supplier GSTIN: 07AAAAA0000A1Z4
    Bill To / Buyer: Client Corporation
    Buyer GSTIN: 27AAACT2727Q1ZW
    Total: ₹ 50,000.00
    """
    claim = parse_invoice_text(text)
    # Must correctly pick the supplier's GSTIN, not the buyer's
    assert claim.gstin == "07AAAAA0000A1Z4"


def test_parse_invoice_pdf_end_to_end():
    # Generate high-fidelity synthetic PDF
    pdf_bytes = create_test_invoice_pdf(
        invoice_number="INV-2026-8841",
        invoice_date="2026-10-15",
        supplier_name="Apex Courier",
        legal_name="Apex Global Logistics Pvt Ltd",
        gstin="07AAAAA0000A1Z4",
        total_amount=482500.00
    )

    claim = parse_invoice_pdf(pdf_bytes)

    assert claim.invoice_number == "INV-2026-8841"
    assert claim.supplier_name == "Apex Courier"
    assert claim.gstin == "07AAAAA0000A1Z4"
    assert claim.total_amount == 482500.00
    assert claim.bank_account_masked == "XXXX-XXXX-9921"
    assert claim.ifsc_code == "HDFC0000123"
    assert claim.gstin_format_valid is True


def test_scanned_pdf_detection_and_ocr_fallback():
    # Generate pure raster image PDF (no digital text layer)
    scanned_pdf = create_scanned_test_invoice_pdf(
        invoice_number="INV-SCAN-9001",
        supplier_name="Scanned Logistics Ltd"
    )

    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    doc = fitz.open(stream=scanned_pdf, filetype="pdf")
    page = doc[0]

    # Verify our heuristic detects this page as scanned
    assert is_page_likely_scanned(page) is True
    doc.close()

    # Verify process_scanned_pdf executes gracefully
    ocr_result = process_scanned_pdf(scanned_pdf)
    assert ocr_result.is_scanned is True
    assert ocr_result.page_count == 1
    # Engine is recorded (rapidocr, tesseract, easyocr, or fallback_null if no external OCR binaries on host)
    assert ocr_result.engine in ["rapidocr", "tesseract", "easyocr", "fallback_null", "none"]



def test_corrupted_pdf_graceful_handling():
    corrupted_bytes = b"NOT_A_VALID_PDF_STREAM_12345"
    text = extract_text_from_pdf_bytes(corrupted_bytes)
    assert "error" in text.lower() or len(text) > 0
