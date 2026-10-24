import pytest
from app.services.validators.arithmetic_validator import validate_invoice_arithmetic
from app.schemas.invoice import LineItem

def test_valid_arithmetic():
    line_items = [
        LineItem(description="Courier Service", quantity=10, unit_price=40889.83, total=408898.31)
    ]
    taxable = 408898.31
    cgst = 36800.85
    sgst = 36800.85
    igst = 0.0
    total = 482500.01  # within tolerance

    is_valid, msg = validate_invoice_arithmetic(
        taxable_amount=taxable,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total,
        line_items=line_items,
        tolerance=1.0
    )
    assert is_valid is True
    assert msg == "ARITHMETIC_RECONCILED"

def test_arithmetic_mismatch_tax():
    # Line items add up to 100, but total claims 500 without proper tax breakdown
    is_valid, msg = validate_invoice_arithmetic(
        taxable_amount=100.0,
        cgst=9.0,
        sgst=9.0,
        igst=0.0,
        total_amount=500.0,
        tolerance=1.0
    )
    assert is_valid is False
    assert "Tax breakdown sum" in msg

def test_line_item_mismatch():
    line_items = [
        LineItem(description="Item A", quantity=1, unit_price=100.0, total=100.0),
        LineItem(description="Item B", quantity=1, unit_price=50.0, total=50.0)
    ]
    # Total of line items is 150, but declared taxable is 300
    is_valid, msg = validate_invoice_arithmetic(
        taxable_amount=300.0,
        cgst=27.0,
        sgst=27.0,
        igst=0.0,
        total_amount=354.0,
        line_items=line_items,
        tolerance=1.0
    )
    assert is_valid is False
    assert "Line items sum" in msg
