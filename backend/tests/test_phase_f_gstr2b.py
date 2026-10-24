import json
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import get_db, init_db, SessionLocal
from backend.app.db.models import Gstr2bEntryModel
from backend.app.db.repository import CaseRepository
from backend.app.services.reconciler.gstr2b_parser import parse_gstr2b_json
from backend.app.schemas.invoice import InvoiceClaim
from backend.app.schemas.evidence import FieldCheckResult
from backend.app.schemas.enums import CheckStatus
from backend.app.services.rules.engine import DeterministicRuleEngine
from backend.app.schemas.case import Case
from backend.app.services.rules.assessment_service import AssessmentService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def create_synthetic_gstr2b_json(buyer_gstin="07AAAAA0000A1Z4", supplier_gstin="07BBBBB1111B1Z2", invoice_num="INV-2026-9001", total_val=118000.0, itcavl="Y"):
    return {
        "gstin": buyer_gstin,
        "fp": "102026",
        "data": {
            "b2b": [
                {
                    "ctin": supplier_gstin,
                    "cname": "Bharat Tech Supplies Private Limited",
                    "inv": [
                        {
                            "inum": invoice_num,
                            "dt": "12-10-2026",
                            "val": total_val,
                            "pos": "07",
                            "itcavl": itcavl,
                            "items": [
                                {
                                    "num": 1,
                                    "txval": 100000.0,
                                    "rt": 18.0,
                                    "iamt": 0.0,
                                    "camt": 9000.0,
                                    "samt": 9000.0,
                                    "csamt": 0.0
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

def test_gstr2b_json_parsing_tolerant():
    data = create_synthetic_gstr2b_json()
    raw = json.dumps(data).encode("utf-8")
    entries, summary = parse_gstr2b_json(raw)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.buyer_gstin == "07AAAAA0000A1Z4"
    assert entry.supplier_gstin == "07BBBBB1111B1Z2"
    assert entry.invoice_number == "INV-2026-9001"
    assert entry.invoice_value == 118000.0
    assert entry.taxable_value == 100000.0
    assert entry.cgst == 9000.0
    assert entry.sgst == 9000.0
    assert entry.itc_available is True

def test_gstr2b_import_endpoint():
    uid = uuid.uuid4().hex[:6]
    supp_gstin = f"07TST{uid.upper()}1Z2"[:15]
    inv_num = f"INV-GSTR2B-{uid}"

    data = create_synthetic_gstr2b_json(supplier_gstin=supp_gstin, invoice_num=inv_num)
    content = json.dumps(data).encode("utf-8")

    res = client.post(
        "/api/gstr2b/import",
        files={"file": ("gstr2b_test.json", content, "application/json")},
        headers={"Authorization": "Bearer garv-reviewer-token-2026"}
    )
    assert res.status_code == 201
    body = res.json()
    assert body["total_records"] == 1
    assert body["imported_records"] == 1

def test_gstr2b_clean_match_rule():
    engine = DeterministicRuleEngine()
    inv = InvoiceClaim(
        supplier_name="Bharat Tech Supplies",
        gstin="07BBBBB1111B1Z2",
        invoice_number="INV-2026-9001",
        total_amount=118000.0,
        taxable_amount=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        igst=0.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )

    gstr2b_mock = Gstr2bEntryModel(
        period="102026",
        buyer_gstin="07AAAAA0000A1Z4",
        supplier_gstin="07BBBBB1111B1Z2",
        invoice_number="INV-2026-9001",
        invoice_value=118000.0,
        itc_available=True,
        imported_at="2026-10-24"
    )

    assessment = engine.evaluate(
        case_id="case_test_match",
        invoice=inv,
        field_checks=[],
        gstr2b_entry=gstr2b_mock,
        buyer_has_gstr2b=True
    )

    assert "GSTR2B_VALUE_MISMATCH" not in assessment.reason_codes
    assert "GSTR2B_ITC_NOT_AVAILABLE" not in assessment.reason_codes
    assert "ITC_NOT_IN_GSTR2B" not in assessment.reason_codes

def test_gstr2b_value_mismatch_rule():
    engine = DeterministicRuleEngine()
    inv = InvoiceClaim(
        supplier_name="Bharat Tech Supplies",
        gstin="07BBBBB1111B1Z2",
        invoice_number="INV-2026-9001",
        total_amount=150000.0,  # Differs from 118,000
        taxable_amount=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        igst=0.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )

    gstr2b_mock = Gstr2bEntryModel(
        period="102026",
        buyer_gstin="07AAAAA0000A1Z4",
        supplier_gstin="07BBBBB1111B1Z2",
        invoice_number="INV-2026-9001",
        invoice_value=118000.0,
        itc_available=True,
        imported_at="2026-10-24"
    )

    assessment = engine.evaluate(
        case_id="case_test_mismatch",
        invoice=inv,
        field_checks=[],
        gstr2b_entry=gstr2b_mock,
        buyer_has_gstr2b=True
    )

    assert "GSTR2B_VALUE_MISMATCH" in assessment.reason_codes
    rule = next(r for r in assessment.triggered_rules if r.reason_code == "GSTR2B_VALUE_MISMATCH")
    assert rule.severity == "HIGH"

def test_gstr2b_itc_ineligible_rule():
    engine = DeterministicRuleEngine()
    inv = InvoiceClaim(
        supplier_name="Bharat Tech Supplies",
        gstin="07BBBBB1111B1Z2",
        invoice_number="INV-2026-9001",
        total_amount=118000.0,
        taxable_amount=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        igst=0.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )

    gstr2b_mock = Gstr2bEntryModel(
        period="102026",
        buyer_gstin="07AAAAA0000A1Z4",
        supplier_gstin="07BBBBB1111B1Z2",
        invoice_number="INV-2026-9001",
        invoice_value=118000.0,
        itc_available=False,  # Supplier marked ineligible
        imported_at="2026-10-24"
    )

    assessment = engine.evaluate(
        case_id="case_test_itc_no",
        invoice=inv,
        field_checks=[],
        gstr2b_entry=gstr2b_mock,
        buyer_has_gstr2b=True
    )

    assert "GSTR2B_ITC_NOT_AVAILABLE" in assessment.reason_codes
    rule = next(r for r in assessment.triggered_rules if r.reason_code == "GSTR2B_ITC_NOT_AVAILABLE")
    assert rule.severity == "MEDIUM"

def test_gstr2b_missing_invoice_hold_advice():
    engine = DeterministicRuleEngine()
    inv = InvoiceClaim(
        supplier_name="Bharat Tech Supplies",
        gstin="07BBBBB1111B1Z2",
        invoice_number="INV-2026-MISSING",
        total_amount=118000.0,
        taxable_amount=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        igst=0.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )

    assessment = engine.evaluate(
        case_id="case_test_hold",
        invoice=inv,
        field_checks=[],
        gstr2b_entry=None,
        buyer_has_gstr2b=True  # GSTR-2B exists for buyer, but invoice wasn't filed
    )

    assert "ITC_NOT_IN_GSTR2B" in assessment.reason_codes
    rule = next(r for r in assessment.triggered_rules if r.reason_code == "ITC_NOT_IN_GSTR2B")
    assert rule.severity == "MEDIUM"
    assert "Payment hold" in rule.description

def test_unmatched_gstr2b_endpoint():
    uid = uuid.uuid4().hex[:6]
    supp_gstin = f"07UNM{uid.upper()}1Z2"[:15]
    inv_num = f"INV-UNMATCHED-{uid}"

    data = create_synthetic_gstr2b_json(supplier_gstin=supp_gstin, invoice_num=inv_num)
    content = json.dumps(data).encode("utf-8")

    # Import GSTR-2B
    client.post(
        "/api/gstr2b/import",
        files={"file": ("unmatched_test.json", content, "application/json")},
        headers={"Authorization": "Bearer garv-reviewer-token-2026"}
    )

    # Check unmatched endpoint
    res = client.get(
        "/api/gstr2b/unmatched",
        headers={"Authorization": "Bearer garv-reviewer-token-2026"}
    )
    assert res.status_code == 200
    rows = res.json()
    assert any(r["invoice_number"] == inv_num for r in rows)
