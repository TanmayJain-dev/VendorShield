import pytest
from app.services.rules.itc_calculator import ITCExposureCalculator
from app.schemas.invoice import InvoiceClaim

def test_itc_calculator_clean_vendor():
    calc = ITCExposureCalculator()
    invoice = InvoiceClaim(
        invoice_number="INV-CLEAN-01",
        supplier_name="Clean Logistics Ltd",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        igst=0.0,
        total_amount=118000.0
    )
    # Clean promoter (0 contagion), normal address (not ghost hub), GST active
    exposure = calc.calculate(
        invoice=invoice,
        director_contagion_score=0.0,
        address_ghost_hub=False,
        gst_inactive=False,
        filing_delay_months=0
    )
    assert exposure.risk_tier == "LOW"
    assert exposure.tax_amount_claimed == 18000.0
    assert exposure.statutory_penalty_inr == 0.0
    assert exposure.estimated_interest_inr == 0.0
    # For low risk, estimated liability is nominal (0.0), matching the advisory
    assert exposure.total_financial_liability_inr == 0.0
    assert exposure.itc_clawback_probability < 0.2
    assert "PROCEED WITH NORMAL CYCLE" in exposure.cfo_advisory
    assert "nominal (₹0.00)" in exposure.cfo_advisory
    assert "Decision-support projection" in exposure.cfo_advisory

def test_itc_calculator_shell_contagion_clawback():
    calc = ITCExposureCalculator()
    # ₹50 Lakh invoice with ₹9 Lakh GST
    invoice = InvoiceClaim(
        invoice_number="INV-SHELL-99",
        supplier_name="Bogus Trading Pvt Ltd",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=5000000.0,
        cgst=450000.0,
        sgst=450000.0,
        igst=0.0,
        total_amount=5900000.0
    )
    # Severe shell contagion (0.43) + Ghost hub address
    exposure = calc.calculate(
        invoice=invoice,
        director_contagion_score=0.43,
        address_ghost_hub=True,
        gst_inactive=False,
        filing_delay_months=2
    )
    assert exposure.risk_tier == "CRITICAL"
    assert exposure.tax_amount_claimed == 900000.0
    # Under Sec 74, illustrative 100% statutory penalty applies
    assert exposure.statutory_penalty_inr == 900000.0
    # Statutory interest at 18% p.a.
    assert exposure.estimated_interest_inr == 162000.0
    assert exposure.total_financial_liability_inr == (900000.0 + 900000.0 + 162000.0)
    assert "DO NOT RELEASE PAYMENT" in exposure.cfo_advisory
    assert any("Sec 74" in sec for sec in exposure.applicable_sections)

def test_itc_calculator_moderate_risk():
    calc = ITCExposureCalculator()
    invoice = InvoiceClaim(
        invoice_number="INV-MOD-01",
        supplier_name="Moderate Logistics Pvt Ltd",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=200000.0,
        cgst=18000.0,
        sgst=18000.0,
        igst=0.0,
        total_amount=236000.0
    )
    # Slight director contagion (0.15), not ghost hub, GST active -> prob = 0.05 + 0.20 = 0.25 (MODERATE)
    exposure = calc.calculate(
        invoice=invoice,
        director_contagion_score=0.15,
        address_ghost_hub=False,
        gst_inactive=False,
        filing_delay_months=0
    )
    assert exposure.risk_tier == "MODERATE"
    assert exposure.tax_amount_claimed == 36000.0
    assert exposure.statutory_penalty_inr == 0.0
    assert exposure.estimated_interest_inr == 0.0
    assert exposure.total_financial_liability_inr == 36000.0
    assert "VERIFY GSTR-1 REFLECTION" in exposure.cfo_advisory

def test_itc_calculator_zero_tax_invoice():
    calc = ITCExposureCalculator()
    invoice = InvoiceClaim(
        invoice_number="INV-ZERO-01",
        supplier_name="Exempt Supply Vendor",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=50000.0,
        cgst=0.0,
        sgst=0.0,
        igst=0.0,
        total_amount=50000.0
    )
    exposure = calc.calculate(
        invoice=invoice,
        director_contagion_score=0.0,
        address_ghost_hub=False,
        gst_inactive=False,
        filing_delay_months=0
    )
    assert exposure.risk_tier == "LOW"
    assert exposure.tax_amount_claimed == 0.0
    assert exposure.total_financial_liability_inr == 0.0
    assert exposure.statutory_penalty_inr == 0.0
