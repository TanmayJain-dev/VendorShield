import pytest
import pymupdf as fitz
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from app.schemas.invoice import InvoiceClaim, FieldExtractionMeta
from app.schemas.enums import ExtractionStatus, CheckStatus, SourceMode, RecommendationOutcome
from app.schemas.case import Case, CaseStatus
from app.schemas.evidence import EvidenceItem
from app.services.rules.forensic_engine import ForensicRiskEngine
from app.services.validators.gstin_validator import validate_gstin_format
from app.services.validators.gstin_tools import make_gstin, compute_check_char
from app.services.tinyfish.orchestrator import MultiHopTinyFishOrchestrator
from app.services.reconciler.evidence_reconciler import EvidenceReconciler
from app.services.rules.assessment_service import assessment_service
from app.services.rules.itc_calculator import ITCExposureCalculator

def test_a1_forensic_engine_extraction_status_import():
    """A1: Ensure ExtractionStatus is imported and does not raise NameError in evaluate."""
    engine = ForensicRiskEngine()
    invoice = InvoiceClaim(
        invoice_number="INV-2026-REAL-01",
        supplier_name="Verified Real Logistics",
        gstin="07AAAAA0000A1Z4",
        total_amount=10000.0,
        taxable_amount=10000.0,
        tax_inferred=False,
        extraction_metadata={
            "supplier_name": FieldExtractionMeta(status=ExtractionStatus.EXTRACTED, confidence=0.95),
            "taxable_amount": FieldExtractionMeta(status=ExtractionStatus.EXTRACTED, confidence=0.95)
        }
    )
    # Must evaluate without NameError: name 'ExtractionStatus' is not defined
    assessment = engine.evaluate(
        case_id="case_a1_test",
        invoice=invoice,
        field_checks=[],
        directors=[],
        address_cluster=None,
        litigation_meta={},
        evidence_items=[]
    )
    assert assessment is not None
    assert assessment.ruleset_version == "2.0.0"

def test_a2_gstin_validator_no_backdoor_and_tools():
    """A2: 07AAAAA0000A1Z5 is invalid Modulo-36; 07AAAAA0000A1Z4 is valid. No 15-char backdoors."""
    # 07AAAAA0000A1Z5 has invalid 15th check char (expected '4')
    is_valid_z5, err_z5 = validate_gstin_format("07AAAAA0000A1Z5")
    assert is_valid_z5 is False
    assert "Checksum failure" in err_z5

    # 07AAAAA0000A1Z4 has valid 15th check char
    is_valid_z4, msg_z4 = validate_gstin_format("07AAAAA0000A1Z4")
    assert is_valid_z4 is True
    assert msg_z4 == "FORMAT_VALID"

    # Verify gstin_tools generates correct check character
    assert compute_check_char("07AAAAA0000A1Z") == "4"
    assert make_gstin("07", "AAAAA0000A", "1") == "07AAAAA0000A1Z4"

    # Scan gstin_validator.py source code for any hardcoded 15-character string literals (backdoor check)
    validator_path = Path("backend/app/services/validators/gstin_validator.py")
    source = validator_path.read_text(encoding="utf-8")
    import re
    # Check for pattern cleaned == "..." or gstin == "..."
    backdoor_matches = re.findall(r'(?:cleaned|gstin)\s*==\s*["\']([0-9A-Z]{15})["\']', source)
    assert len(backdoor_matches) == 0, f"Found hardcoded GSTIN backdoor: {backdoor_matches}"

    # Verify all sample_data JSON files have valid GSTINs
    sample_dir = Path("sample_data")
    if sample_dir.exists():
        for jf in sample_dir.glob("*.json"):
            data = json.loads(jf.read_text(encoding="utf-8"))
            gst = data.get("gstin")
            if gst:
                val, reason = validate_gstin_format(gst)
                assert val is True, f"File {jf.name} contains invalid GSTIN '{gst}': {reason}"

@pytest.mark.asyncio
async def test_a3_orchestrator_returns_unavailable_for_non_demo():
    """A3: Simulated orchestrator must return UNAVAILABLE for real cases, never Apex fixtures."""
    orchestrator = MultiHopTinyFishOrchestrator(api_key="")
    # Real vendor, is_demo=False
    evidence, directors, address, litigation = await orchestrator.execute_investigation(
        supplier_name="Real Independent Logistics Pvt Ltd",
        gstin="07AAAAA0000A1Z4",
        is_demo=False
    )
    assert orchestrator.source_mode == SourceMode.UNAVAILABLE
    assert len(evidence) == 1
    assert evidence[0].source_mode == SourceMode.UNAVAILABLE
    assert "No external registry provider" in evidence[0].raw_excerpt
    # Must NOT have returned Sanjay Singhal or Apex Courier fixtures!
    assert len(directors) == 0
    assert address.premises_type == "UNKNOWN"

@pytest.mark.asyncio
async def test_a3_orchestrator_demo_fixtures_when_demo_flagged():
    """A3: Simulated orchestrator returns demo fixtures only when DEMO_MODE=true and is_demo=true."""
    from app.config import settings
    orchestrator = MultiHopTinyFishOrchestrator(api_key="")
    with patch.object(settings, "DEMO_MODE", True):
        evidence, directors, address, litigation = await orchestrator.execute_investigation(
            supplier_name="Apex Courier",
            gstin="07AAAAA0000A1Z4",
            is_demo=True
        )
        assert orchestrator.source_mode == SourceMode.SIMULATED
        assert len(evidence) == 4
        assert directors[0].name == "Sanjay Singhal"
        assert any("DEMO FIXTURE" in ev.raw_excerpt for ev in evidence)

def test_a4_reconciler_outage_does_not_cause_false_block():
    """A4: Registry timeouts, HTTP errors, and composition status must not emit GST_STATUS_INACTIVE_CONFIRMED."""
    reconciler = EvidenceReconciler()
    invoice = InvoiceClaim(
        invoice_number="INV-2026-001",
        supplier_name="Reliable Vendor Ltd",
        gstin="07AAAAA0000A1Z4",
        total_amount=50000.0,
        taxable_amount=50000.0
    )

    # 1. Evidence with source_mode=UNAVAILABLE must be ignored
    unavail_ev = [
        EvidenceItem(
            evidence_id="ev_timeout",
            source_url="https://service.gst.gov.in",
            source_name="GSTN Registry",
            claim_supported="Legal Entity & GST Status",
            source_type="GOVERNMENT_REGISTRY",
            source_mode=SourceMode.UNAVAILABLE,
            raw_excerpt="HTTP 504 Gateway Timeout",
            facts={"status": "UNAVAILABLE"},
            is_authoritative=False
        )
    ]
    checks_timeout = reconciler.reconcile(invoice, unavail_ev)
    gst_check_timeout = next(c for c in checks_timeout if c.field_name == "GST Registration Status")
    assert gst_check_timeout.status == CheckStatus.UNAVAILABLE
    assert gst_check_timeout.reason_code == "GST_STATUS_UNKNOWN"
    assert gst_check_timeout.reason_code != "GST_STATUS_INACTIVE_CONFIRMED"

    # 2. Composition active status
    comp_ev = [
        EvidenceItem(
            evidence_id="ev_comp",
            source_url="https://service.gst.gov.in",
            source_name="GSTN Registry",
            claim_supported="Legal Entity",
            source_type="GOVERNMENT_REGISTRY",
            source_mode=SourceMode.LIVE,
            raw_excerpt="Status: Active (Composition Taxpayer)",
            facts={"status": "Active (Composition Taxpayer)", "legal_name": "Reliable Vendor Ltd"},
            is_authoritative=True
        )
    ]
    checks_comp = reconciler.reconcile(invoice, comp_ev)
    gst_check_comp = next(c for c in checks_comp if c.field_name == "GST Registration Status")
    assert gst_check_comp.status == CheckStatus.MATCH

    # 3. Confirmed cancelled suo-moto
    cancelled_ev = [
        EvidenceItem(
            evidence_id="ev_cancelled",
            source_url="https://service.gst.gov.in",
            source_name="GSTN Registry",
            claim_supported="Legal Entity",
            source_type="GOVERNMENT_REGISTRY",
            source_mode=SourceMode.LIVE,
            raw_excerpt="Status: Cancelled Suo-Moto",
            facts={"status": "Cancelled Suo-Moto", "legal_name": "Reliable Vendor Ltd"},
            is_authoritative=True
        )
    ]
    checks_canc = reconciler.reconcile(invoice, cancelled_ev)
    gst_check_canc = next(c for c in checks_canc if c.field_name == "GST Registration Status")
    assert gst_check_canc.status == CheckStatus.MISMATCH
    assert gst_check_canc.reason_code == "GST_STATUS_INACTIVE_CONFIRMED"

def test_a6_unified_assessment_service():
    """A6: Unified AssessmentService handles core rules and optional experimental forensics consistently."""
    invoice = InvoiceClaim(
        invoice_number="INV-2026-ASSESS",
        supplier_name="Verified Goods Corp",
        gstin="07AAAAA0000A1Z4",
        total_amount=11800.0,
        taxable_amount=10000.0,
        cgst=900.0,
        sgst=900.0,
        igst=0.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )
    case = Case(
        case_id="case_unified_test",
        case_reference="INV-2026-ASSESS",
        status=CaseStatus.PARSED,
        is_demo=False,
        invoice=invoice,
        evidence_items=[]
    )

    # Default non-demo case: forensic vectors are None
    assessment = assessment_service.assess(case)
    assert assessment.forensic_vectors is None
    assert assessment.itc_exposure is None
    assert assessment.entity_graph is None
    assert assessment.recommendation in (RecommendationOutcome.PASS, RecommendationOutcome.MANUAL_REVIEW)

    # Demo case: forensic vectors are computed
    case.is_demo = True
    demo_assessment = assessment_service.assess(case)
    assert demo_assessment.forensic_vectors is not None
    assert demo_assessment.itc_exposure is not None

def test_a12_itc_calculator_parameters_and_advisory():
    """A12: Verify ITC exposure calculator contains legal parameters, CA note, and ₹0 low-risk liability."""
    calc = ITCExposureCalculator()
    invoice = InvoiceClaim(
        invoice_number="INV-CLEAN-TAX",
        supplier_name="Clean Supplier Ltd",
        gstin="07AAAAA0000A1Z4",
        total_amount=118000.0,
        taxable_amount=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        igst=0.0
    )
    exposure = calc.calculate(
        invoice=invoice,
        director_contagion_score=0.0,
        address_ghost_hub=False,
        gst_inactive=False,
        filing_delay_months=0
    )
    assert exposure.risk_tier == "LOW"
    assert exposure.total_financial_liability_inr == 0.0
    assert "Chartered Accountant" in exposure.cfo_advisory
