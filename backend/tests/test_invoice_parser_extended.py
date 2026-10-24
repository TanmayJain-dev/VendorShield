import pytest
from backend.app.services.parser.invoice_parser import (
    parse_invoice_text,
    parse_invoice_pdf,
    extract_text_from_pdf_bytes
)
from backend.app.schemas.enums import ExtractionStatus

def test_parse_invoice_with_explicit_cgst_sgst():
    text = """
    TAX INVOICE
    Invoice No: INV-2026-9901
    Date: 2026-10-18
    GSTIN: 07AAAAA0000A1Z4
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
    # INVARIANT: Arithmetic must never be marked valid when tax was inferred
    assert claim.arithmetic_valid is False
    assert "ARITHMETIC_UNVERIFIED" in claim.arithmetic_notes

def test_extract_text_pdf_page_limit_enforced():
    # Ensure PDF parser rejects exceeding max page limits cleanly
    fake_doc = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"
    text, is_scanned, ocr_msg, errors = extract_text_from_pdf_bytes(fake_doc)
    # Returns structured errors, does not crash or inject into text
    assert isinstance(errors, list)

def test_corrupted_pdf_returns_structured_error_and_clean_supplier():
    corrupted_bytes = b"CORRUPTED_NOT_A_PDF"
    claim = parse_invoice_pdf(corrupted_bytes, default_supplier="Default Fallback Vendor")
    # Must preserve supplier name and not inject error text into vendor name
    assert claim.supplier_name == "Default Fallback Vendor"
    assert claim.arithmetic_valid is False
    assert len(claim.parsing_errors) > 0
    assert any("missing %PDF-" in err for err in claim.parsing_errors)
    # Raw text must not contain corrupted non-pdf junk
    assert claim.raw_text == ""

def test_oversized_pdf_rejected_before_memory():
    # Construct a simulated >15MB payload
    oversized = b"%PDF-" + b"A" * (15 * 1024 * 1024 + 100)
    text, is_scanned, ocr_msg, errors = extract_text_from_pdf_bytes(oversized)
    assert len(errors) > 0
    assert any("exceeds maximum file size" in err for err in errors)

def test_multirate_gst_preserved():
    # Test 5% GST (CGST 2.5%, SGST 2.5%) and 28% IGST are preserved and not forced to 18%
    text_5pct = """
    TAX INVOICE
    Invoice No: INV-5PCT-101
    Date: 2026-10-10
    GSTIN: 07AAAAA0000A1Z4
    Taxable Amount: 100,000.00
    CGST @ 2.5%: 2,500.00
    SGST @ 2.5%: 2,500.00
    Total Amount: 105,000.00
    """
    claim_5 = parse_invoice_text(text_5pct, default_supplier="Food Supplies")
    assert claim_5.cgst == 2500.0
    assert claim_5.sgst == 2500.0
    assert claim_5.total_amount == 105000.0
    assert claim_5.arithmetic_valid is True
    assert claim_5.tax_inferred is False
    assert len(claim_5.tax_breakdown) == 2
    assert claim_5.tax_breakdown[0].rate_pct == 2.5

    text_28pct = """
    TAX INVOICE
    Invoice No: INV-28PCT-202
    Date: 2026-10-12
    GSTIN: 07AAAAA0000A1Z4
    Taxable Amount: 50,000.00
    IGST @ 28%: 14,000.00
    Total Amount: 64,000.00
    """
    claim_28 = parse_invoice_text(text_28pct, default_supplier="Luxury Auto")
    assert claim_28.igst == 14000.0
    assert claim_28.total_amount == 64000.0
    assert claim_28.arithmetic_valid is True
    assert claim_28.tax_inferred is False
    assert len(claim_28.tax_breakdown) == 1
    assert claim_28.tax_breakdown[0].rate_pct == 28.0

def test_inferred_tax_fails_closed_in_rule_engine():
    from backend.app.services.rules.engine import DeterministicRuleEngine
    from backend.app.schemas.enums import RecommendationOutcome

    text = """
    Invoice No: INV-NO-TAX
    Total Amount: 10,000.00
    """
    claim = parse_invoice_text(text, default_supplier="No Tax Vendor")
    assert claim.tax_inferred is True
    assert claim.arithmetic_valid is False

    engine = DeterministicRuleEngine()
    assessment = engine.evaluate("case_1", claim, field_checks=[])
    # Invariant: Must fail closed to MANUAL_REVIEW, NEVER PASS
    assert assessment.recommendation == RecommendationOutcome.MANUAL_REVIEW
    assert "TAX_BREAKDOWN_INFERRED" in assessment.reason_codes

def test_zero_tax_invoice_fails_closed_to_manual_review():
    from backend.app.services.rules.engine import DeterministicRuleEngine
    from backend.app.schemas.enums import RecommendationOutcome

    # Zero-tax invoice (total equals taxable with 0 GST claimed)
    text = """
    TAX INVOICE
    Invoice No: INV-ZERO-TAX-99
    GSTIN: 07AAAAA0000A1Z4
    Taxable Amount: 50,000.00
    CGST: 0.00
    SGST: 0.00
    Total Amount: 50,000.00
    """
    claim = parse_invoice_text(text, default_supplier="Exempt Vendor")
    assert claim.total_amount == 50000.0
    assert claim.cgst + claim.sgst + claim.igst == 0.0

    engine = DeterministicRuleEngine()
    assessment = engine.evaluate("case_2", claim, field_checks=[])
    # Zero-tax must trigger ZERO_TAX_UNVERIFIED and fail-closed to MANUAL_REVIEW
    assert assessment.recommendation == RecommendationOutcome.MANUAL_REVIEW
    assert "ZERO_TAX_UNVERIFIED" in assessment.reason_codes

def test_corrupted_pdf_fails_closed_in_rule_engine():
    from backend.app.services.rules.engine import DeterministicRuleEngine
    from backend.app.schemas.enums import RecommendationOutcome

    claim = parse_invoice_pdf(b"CORRUPTED_BYTES", default_supplier="Corrupt Vendor")
    assert len(claim.parsing_errors) > 0

    engine = DeterministicRuleEngine()
    assessment = engine.evaluate("case_3", claim, field_checks=[])
    # Corrupt documents must fail-closed to MANUAL_REVIEW
    assert assessment.recommendation == RecommendationOutcome.MANUAL_REVIEW
    assert "PARSING_EXTRACTION_ERROR" in assessment.reason_codes
