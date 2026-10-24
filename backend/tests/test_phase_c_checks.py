import pytest
import httpx
from datetime import datetime, timezone, timedelta

from app.config import settings
from app.schemas.invoice import InvoiceClaim, FieldExtractionMeta
from app.schemas.evidence import EvidenceItem, FieldCheckResult, ManualGstinEvidenceRequest
from app.schemas.case import Case
from app.schemas.enums import RecommendationOutcome, CheckStatus, SourceMode, ExtractionStatus
from app.services.rules.engine import DeterministicRuleEngine
from app.services.rules.assessment_service import assessment_service
from app.services.providers.manual_provider import ManualEntryProvider
from app.services.providers.http_kyc_provider import HttpKycProvider
from app.services.providers.composite_registry import CompositeRegistryProvider
from app.services.providers.ifsc_provider import IfscProvider
from app.db.database import get_db, SessionLocal
from app.db.repository import CaseRepository


@pytest.fixture
def clean_invoice():
    return InvoiceClaim(
        invoice_number="INV-2026-001",
        invoice_date=datetime.now().strftime("%Y-%m-%d"),
        supplier_name="Apex Global Logistics",
        gstin="07AAAAA0000A1Z4",
        buyer_gstin="27ABCDE1234F1Z5",
        taxable_amount=10000.0,
        cgst=0.0,
        sgst=0.0,
        igst=1800.0,
        total_amount=11800.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )


def test_buyer_gstin_mismatch(clean_invoice, monkeypatch):
    monkeypatch.setattr(settings, "BUYER_GSTINS", ["07AAAAA0000A1Z4", "29XYZAB1234C1Z1"])
    engine = DeterministicRuleEngine()
    
    # Buyer GSTIN is 27ABCDE1234F1Z5 which is not in BUYER_GSTINS
    assessment = engine.evaluate("case_1", clean_invoice, [])
    assert "BUYER_GSTIN_MISMATCH" in assessment.reason_codes
    assert any(r.reason_code == "BUYER_GSTIN_MISMATCH" for r in assessment.triggered_rules)

    # Buyer GSTIN matching
    clean_invoice.buyer_gstin = "07AAAAA0000A1Z4"
    assessment_match = engine.evaluate("case_1", clean_invoice, [])
    assert "BUYER_GSTIN_MISMATCH" not in assessment_match.reason_codes


def test_tax_type_state_mismatch(clean_invoice):
    engine = DeterministicRuleEngine()
    
    # Inter-state (Supplier 07 Delhi, Buyer 27 Maharashtra): IGST is expected.
    # If supplier erroneously charges CGST + SGST instead of IGST:
    clean_invoice.cgst = 900.0
    clean_invoice.sgst = 900.0
    clean_invoice.igst = 0.0
    
    assessment = engine.evaluate("case_2", clean_invoice, [])
    assert "TAX_TYPE_STATE_MISMATCH" in assessment.reason_codes
    assert any("Inter-state" in r.description for r in assessment.triggered_rules if r.reason_code == "TAX_TYPE_STATE_MISMATCH")


def test_pan_holder_validation(clean_invoice):
    engine = DeterministicRuleEngine()
    # 4th character of PAN is 'X' (invalid entity code)
    clean_invoice.gstin = "07AAAXA0000A1Z4"
    assessment = engine.evaluate("case_3", clean_invoice, [])
    assert "PAN_FORMAT_INVALID" in assessment.reason_codes


def test_invoice_number_rule46_violation(clean_invoice):
    engine = DeterministicRuleEngine()
    # Over 16 chars or with spaces
    clean_invoice.invoice_number = "INV-LONG-NUMBER-EXCEEDING-16"
    assessment = engine.evaluate("case_4", clean_invoice, [])
    assert "INVOICE_NUMBER_FORMAT_INVALID" in assessment.reason_codes


def test_future_invoice_date(clean_invoice):
    engine = DeterministicRuleEngine()
    clean_invoice.invoice_date = "2099-12-31"
    assessment = engine.evaluate("case_5", clean_invoice, [])
    assert "FUTURE_INVOICE_DATE" in assessment.reason_codes


def test_einvoice_qr_tampering_block(clean_invoice):
    engine = DeterministicRuleEngine()
    clean_invoice.extraction_conflicts = [
        {"field": "total_amount", "source_a": "QR", "value_a": 99999.0, "source_b": "REGEX", "value_b": 11800.0}
    ]
    clean_invoice.qr_signature_status = "VERIFIED"
    
    assessment = engine.evaluate("case_6", clean_invoice, [])
    assert "EINVOICE_QR_MISMATCH" in assessment.hard_gates_triggered
    assert assessment.recommendation == RecommendationOutcome.BLOCK


@pytest.mark.asyncio
async def test_manual_entry_provider():
    provider = ManualEntryProvider(attested_by="reviewer_garv")
    ev = await provider.lookup(
        gstin="07AAAAA0000A1Z4",
        case_context={
            "legal_name": "Apex Global Logistics Pvt Ltd",
            "status": "Active",
            "registration_date": "2018-07-01"
        }
    )
    assert ev.source_mode == SourceMode.MANUAL
    assert ev.is_authoritative is True
    assert ev.facts["legal_name"] == "Apex Global Logistics Pvt Ltd"
    assert ev.facts["status"] == "Active"


@pytest.mark.asyncio
async def test_http_kyc_provider_mock():
    mock_vendor_payload = {
        "lgnm": "Apex Global Logistics Private Limited",
        "tradeNam": "Apex Logistics",
        "sts": "Active",
        "rgdt": "01/07/2018"
    }

    def handler(request: httpx.Request):
        return httpx.Response(200, json=mock_vendor_payload)

    provider = HttpKycProvider(url_template="https://api.test/gstin/{gstin}")
    provider.transport = httpx.MockTransport(handler)

    ev = await provider.lookup("07AAAAA0000A1Z4")
    assert ev.source_mode == SourceMode.LIVE
    assert ev.facts["legal_name"] == "Apex Global Logistics Private Limited"
    assert ev.facts["status"] == "Active"


@pytest.mark.asyncio
async def test_ifsc_provider_lookup_and_cache():
    from app.db.database import init_db
    from app.db.models import IfscCacheModel
    init_db()
    db = SessionLocal()
    try:
        db.query(IfscCacheModel).filter(IfscCacheModel.ifsc == "HDFC0000128").delete()
        db.commit()

        mock_ifsc_payload = {
            "BANK": "HDFC Bank",
            "BRANCH": "Connaught Place",
            "CITY": "New Delhi",
            "STATE": "Delhi"
        }

        def handler(request: httpx.Request):
            return httpx.Response(200, json=mock_ifsc_payload)

        provider = IfscProvider()
        provider.transport = httpx.MockTransport(handler)

        res = await provider.lookup("HDFC0000128", db=db)
        assert res["valid"] is True
        assert res["bank"] == "HDFC Bank"
        assert res["source"] == "API"

        # Second lookup should hit cache
        res_cached = await provider.lookup("HDFC0000128", db=db)
        assert res_cached["valid"] is True
        assert res_cached["source"] == "CACHE"
    finally:
        db.close()


def test_explain_verdict_payload(clean_invoice):
    case = Case(
        case_id="case_explain_test",
        case_reference="INV-2026-001",
        invoice=clean_invoice,
        evidence_items=[
            EvidenceItem(
                evidence_id="ev_active",
                source_url="https://services.gst.gov.in/services/searchtp",
                source_name="GST Registry",
                claim_supported="Legal Entity and GST Status",
                source_mode=SourceMode.MANUAL,
                is_authoritative=True,
                facts={
                    "legal_name": "Apex Global Logistics",
                    "status": "Active"
                }
            )
        ]
    )
    assessment = assessment_service.assess(case)
    case.assessment = assessment

    explanation = assessment_service.explain_verdict(case)
    assert explanation["case_id"] == "case_explain_test"
    assert explanation["verdict"] in ["PASS", "MANUAL_REVIEW"]
    assert len(explanation["why_this_verdict"]) > 0
    assert len(explanation["what_would_change_it"]) > 0
