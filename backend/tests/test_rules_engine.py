import pytest
from app.services.rules.engine import DeterministicRuleEngine
from app.schemas.invoice import InvoiceClaim
from app.schemas.evidence import FieldCheckResult
from app.schemas.enums import RecommendationOutcome, CheckStatus

def test_rule_engine_clean_pass():
    engine = DeterministicRuleEngine()
    invoice = InvoiceClaim(
        invoice_number="INV-001",
        supplier_name="Genuine Vendor Pvt Ltd",
        gstin="07AAAAA0000A1Z4",
        taxable_amount=8474.58,
        cgst=762.71,
        sgst=762.71,
        total_amount=10000.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )
    checks = [
        FieldCheckResult(
            check_id="1",
            field_name="Supplier Identity",
            status=CheckStatus.MATCH,
            explanation="Exact match"
        )
    ]
    assessment = engine.evaluate("case_1", invoice, checks)
    assert assessment.recommendation == RecommendationOutcome.PASS
    assert assessment.risk_score == 100
    assert len(assessment.hard_gates_triggered) == 0

def test_rule_engine_hard_gate_gst_inactive():
    engine = DeterministicRuleEngine()
    invoice = InvoiceClaim(
        invoice_number="INV-002",
        supplier_name="Suspended Vendor",
        gstin="07AAAAA0000A1Z4",
        taxable_amount=42372.88,
        cgst=3813.56,
        sgst=3813.56,
        total_amount=50000.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )
    checks = [
        FieldCheckResult(
            check_id="2",
            field_name="GST Registration Status",
            status=CheckStatus.MISMATCH,
            reason_code="GST_STATUS_INACTIVE_CONFIRMED",
            explanation="GST is suspended/inactive"
        )
    ]
    assessment = engine.evaluate("case_2", invoice, checks)
    assert assessment.recommendation == RecommendationOutcome.BLOCK
    assert "GST_STATUS_INACTIVE_CONFIRMED" in assessment.hard_gates_triggered

def test_rule_engine_benchmark_apex_courier():
    engine = DeterministicRuleEngine()
    invoice = InvoiceClaim(
        invoice_number="INV-2026-8841",
        supplier_name="Apex Courier",
        gstin="07AAAAA0000A1Z4",
        taxable_amount=408898.31,
        cgst=36800.85,
        sgst=36800.85,
        total_amount=482500.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )
    checks = [
        FieldCheckResult(
            check_id="chk_name",
            field_name="Trade vs Legal Name",
            status=CheckStatus.POSSIBLE_MATCH,
            reason_code="LEGAL_NAME_MISMATCH",
            explanation="Trade name vs legal entity"
        ),
        FieldCheckResult(
            check_id="chk_bank",
            field_name="Bank Beneficiary Ownership",
            status=CheckStatus.POSSIBLE_MATCH,
            reason_code="BANK_OWNERSHIP_UNVERIFIED",
            explanation="IFSC verified; account unverified"
        )
    ]
    assessment = engine.evaluate("case_demo", invoice, checks)
    assert assessment.recommendation == RecommendationOutcome.MANUAL_REVIEW
    assert "LEGAL_NAME_MISMATCH" in assessment.reason_codes
    assert "BANK_OWNERSHIP_UNVERIFIED" in assessment.reason_codes
    assert assessment.risk_score == 68  # 100 - 20 (legal name) - 12 (bank ownership) = 68
