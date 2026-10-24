import pytest
from app.services.rules.forensic_engine import ForensicRiskEngine
from app.schemas.invoice import InvoiceClaim
from app.schemas.evidence import FieldCheckResult, EvidenceItem
from app.schemas.forensic_graph import DirectorProfile, AddressClusterProfile
from app.schemas.enums import RecommendationOutcome, CheckStatus, SourceMode

def test_forensic_engine_apex_courier():
    engine = ForensicRiskEngine()
    invoice = InvoiceClaim(
        invoice_number="INV-2026-8841",
        supplier_name="Apex Courier",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=408898.31,
        cgst=36800.85,
        sgst=36800.85,
        igst=0.0,
        total_amount=482500.00,
        gstin_format_valid=True,
        arithmetic_valid=True
    )
    directors = [
        DirectorProfile(
            din="02341908",
            name="Sanjay Singhal",
            associated_companies_count=2,
            struck_off_companies_count=0,
            contagion_ratio=0.0
        )
    ]
    address_cluster = AddressClusterProfile(
        raw_address="Okhla Industrial Area Phase II, Delhi",
        collocated_gstins_count=1,
        premises_type="INDUSTRIAL_WAREHOUSE",
        is_ghost_hub=False
    )
    litigation_meta = {"active_cases": 0, "nclt_petitions": []}
    field_checks = [
        FieldCheckResult(
            check_id="chk_name",
            field_name="Trade vs Legal Name",
            status=CheckStatus.POSSIBLE_MATCH,
            reason_code="LEGAL_NAME_MISMATCH",
            explanation="Trade name Apex Courier vs legal entity Apex Global Logistics Pvt Ltd"
        ),
        FieldCheckResult(
            check_id="chk_bank",
            field_name="Bank Beneficiary Ownership",
            status=CheckStatus.POSSIBLE_MATCH,
            reason_code="BANK_OWNERSHIP_UNVERIFIED",
            explanation="IFSC branch confirmed; account ownership unverified"
        )
    ]

    assessment = engine.evaluate(
        case_id="case_apex_demo",
        invoice=invoice,
        field_checks=field_checks,
        directors=directors,
        address_cluster=address_cluster,
        litigation_meta=litigation_meta,
        evidence_items=[]
    )

    assert assessment.recommendation == RecommendationOutcome.MANUAL_REVIEW
    assert assessment.forensic_vectors is not None
    assert assessment.forensic_vectors.director_shell_contagion_score == 0.0
    assert assessment.forensic_vectors.address_collocation_density == 1
    assert assessment.forensic_vectors.operational_grounding_score == 1.0
    assert assessment.itc_exposure.risk_tier in ["LOW", "MODERATE"]
    assert assessment.entity_graph.total_nodes >= 3

def test_forensic_engine_specter_shell_mill_blocks():
    engine = ForensicRiskEngine()
    invoice = InvoiceClaim(
        invoice_number="INV-2026-8842",
        supplier_name="Specter Cloud Technologies",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=250000.0,
        cgst=22500.0,
        sgst=22500.0,
        igst=0.0,
        total_amount=295000.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )
    directors = [
        DirectorProfile(
            din="08992144",
            name="Ramesh Kumar (Nominee)",
            associated_companies_count=14,
            struck_off_companies_count=6,
            contagion_ratio=0.43,
            is_benami_flagged=True
        )
    ]
    address_cluster = AddressClusterProfile(
        raw_address="Room 104, Shakarpur Complex",
        collocated_gstins_count=38,
        premises_type="VIRTUAL_OFFICE",
        is_ghost_hub=True
    )
    litigation_meta = {
        "active_cases": 1,
        "nclt_petitions": ["CP(IB)/412/ND/2026 under IBC Section 9"]
    }

    assessment = engine.evaluate(
        case_id="case_specter_shell",
        invoice=invoice,
        field_checks=[],
        directors=directors,
        address_cluster=address_cluster,
        litigation_meta=litigation_meta,
        evidence_items=[]
    )

    # Shell contagion + Ghost hub + NCLT petition MUST BLOCK
    assert assessment.recommendation == RecommendationOutcome.BLOCK
    assert "DIRECTOR_SHELL_CONTAGION_CRITICAL" in assessment.hard_gates_triggered
    assert "GHOST_HUB_ADDRESS_DETECTED" in assessment.hard_gates_triggered
    assert "ACTIVE_INSOLVENCY_PROCEEDING" in assessment.hard_gates_triggered
    assert assessment.itc_exposure.risk_tier == "CRITICAL"
    assert "DO NOT RELEASE PAYMENT" in assessment.itc_exposure.cfo_advisory
    assert assessment.entity_graph.total_flagged_edges >= 2

def test_forensic_engine_incomplete_evidence_fails_closed():
    """Missing or unavailable evidence must fail closed to MANUAL_REVIEW, never PASS."""
    engine = ForensicRiskEngine()
    invoice = InvoiceClaim(
        invoice_number="INV-2026-9999",
        supplier_name="Clean Looking Vendor",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=10000.0,
        cgst=900.0,
        sgst=900.0,
        igst=0.0,
        total_amount=11800.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )
    directors = [
        DirectorProfile(din="01111111", name="Clean Director", associated_companies_count=1, struck_off_companies_count=0)
    ]
    address_cluster = AddressClusterProfile(
        raw_address="Clean Warehouse",
        collocated_gstins_count=1,
        premises_type="COMMERCIAL_HUB",
        is_ghost_hub=False
    )
    # Check is UNAVAILABLE because live registry call timed out
    field_checks = [
        FieldCheckResult(
            check_id="chk_gst",
            field_name="GST Registration Status",
            status=CheckStatus.UNAVAILABLE,
            reason_code="GST_STATUS_UNAVAILABLE",
            explanation="Registry service timed out"
        )
    ]
    unavailable_evidence = [
        EvidenceItem(
            evidence_id="ev_unavailable",
            source_url="https://service.gst.gov.in",
            source_name="GSTN Statutory Registry",
            claim_supported="Status",
            source_type="GOVERNMENT_REGISTRY",
            source_mode=SourceMode.UNAVAILABLE,
            raw_excerpt="Live lookup timed out",
            facts={"status": "UNAVAILABLE"},
            is_authoritative=False
        )
    ]

    assessment = engine.evaluate(
        case_id="case_partial",
        invoice=invoice,
        field_checks=field_checks,
        directors=directors,
        address_cluster=address_cluster,
        litigation_meta={"active_cases": 0},
        evidence_items=unavailable_evidence
    )

    # Must fail closed: cannot be PASS!
    assert assessment.recommendation == RecommendationOutcome.MANUAL_REVIEW
    assert assessment.evidence_completeness in ("PARTIAL", "INSUFFICIENT")
    assert "INCOMPLETE_EVIDENCE_FAIL_CLOSED" in assessment.reason_codes
