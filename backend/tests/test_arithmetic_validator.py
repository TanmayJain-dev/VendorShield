import pytest
from app.services.validators.arithmetic_validator import (
    validate_invoice_arithmetic,
    reconcile_invoice_components
)
from app.schemas.invoice import LineItem


def test_valid_intra_state_arithmetic():
    line_items = [
        LineItem(description="Courier Service A", quantity=10, unit_price=25000.00, total=250000.00),
        LineItem(description="Courier Service B", quantity=5, unit_price=31779.66, total=158898.31)
    ]
    taxable = 408898.31
    cgst = 36800.85
    sgst = 36800.85
    igst = 0.0
    total = 482500.01  # within standard 1.0 tolerance

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


def test_valid_inter_state_igst():
    line_items = [
        LineItem(description="Cloud Server Hosting", quantity=1, unit_price=100000.0, total=100000.0)
    ]
    taxable = 100000.0
    cgst = 0.0
    sgst = 0.0
    igst = 18000.0  # 18% IGST
    total = 118000.0

    report = reconcile_invoice_components(
        taxable_amount=taxable,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total,
        line_items=line_items
    )
    assert report["is_valid"] is True
    assert report["tax_type"] == "INTER_STATE"
    assert report["effective_tax_rate"] == 18.0
    assert report["standard_tax_rate_matched"] is True


def test_arithmetic_mismatch_tax():
    # Claimed total 500.0 does not match 100 + 9 + 9 = 118.0
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


def test_line_item_mismatch_with_taxable():
    line_items = [
        LineItem(description="Item A", quantity=1, unit_price=100.0, total=100.0),
        LineItem(description="Item B", quantity=1, unit_price=50.0, total=50.0)
    ]
    # Sum of items is 150, but declared taxable is 300
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


def test_line_item_unit_multiplication_error():
    line_items = [
        # 10 x 50 should be 500, but declared as 800
        LineItem(description="Faulty Multiplication", quantity=10.0, unit_price=50.0, total=800.0)
    ]
    report = reconcile_invoice_components(
        taxable_amount=800.0,
        cgst=72.0,
        sgst=72.0,
        igst=0.0,
        total_amount=944.0,
        line_items=line_items
    )
    assert report["is_valid"] is False
    assert any("Faulty Multiplication" in err for err in report["discrepancies"])


def test_intra_state_cgst_sgst_asymmetry():
    # Intra-state requires CGST == SGST
    report = reconcile_invoice_components(
        taxable_amount=10000.0,
        cgst=900.0,
        sgst=500.0,  # Asymmetric!
        igst=0.0,
        total_amount=11400.0
    )
    assert report["is_valid"] is False
    assert report["cgst_sgst_symmetric"] is False
    assert any("asymmetry" in d for d in report["discrepancies"])


def test_conflicting_taxes():
    # Both CGST and IGST simultaneously charged
    report = reconcile_invoice_components(
        taxable_amount=10000.0,
        cgst=900.0,
        sgst=900.0,
        igst=1800.0,
        total_amount=13600.0
    )
    assert report["is_valid"] is False
    assert report["tax_type"] == "CONFLICTING_TAX"


def test_rounding_tolerance_threshold():
    # 0.5 difference passes with tolerance=1.0
    is_valid, _ = validate_invoice_arithmetic(
        taxable_amount=100.0,
        cgst=9.0,
        sgst=9.0,
        igst=0.0,
        total_amount=118.5,
        tolerance=1.0
    )
    assert is_valid is True

    # 1.5 difference fails with tolerance=1.0
    is_valid_fail, _ = validate_invoice_arithmetic(
        taxable_amount=100.0,
        cgst=9.0,
        sgst=9.0,
        igst=0.0,
        total_amount=119.5,
        tolerance=1.0
    )
    assert is_valid_fail is False
