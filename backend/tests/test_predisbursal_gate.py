import pytest
from app.services.parser.vendor_master import (
    check_bank_mutation,
    calculate_beneficiary_match,
    hash_bank_account
)
from app.services.rules.forensic_engine import ForensicRiskEngine
from app.services.tinyfish.orchestrator import MultiHopTinyFishOrchestrator
from app.schemas.invoice import InvoiceClaim
from app.schemas.evidence import FieldCheckResult
from app.schemas.forensic_graph import DirectorProfile, AddressClusterProfile
from app.schemas.enums import RecommendationOutcome, CheckStatus

def test_bank_mutation_bec_detection():
    """
    Bank Account Mutation & Penny-Drop Guard (Anti-BEC Fraud):
    When invoice bank account differs from verified historical remittance account,
    bank_mutation_detected must be True.
    """
    # 1. Registered demo account for Apex Courier (07AAAAA0000A1Z5)
    known_account = "98765432109921"
    is_mutation, known_masked, msg = check_bank_mutation("07AAAAA0000A1Z5", known_account, "HDFC0001234")
    assert is_mutation is False  # False means NO mutation detected

    # 2. Altered BEC account on invoice
    compromised_account = "919020099999999"
    is_mutation_bec, known_masked_bec, msg_bec = check_bank_mutation("07AAAAA0000A1Z5", compromised_account, "UTIB0000040")
    assert is_mutation_bec is True  # Mutation detected!
    assert known_masked_bec == "XXXX-XXXX-9921"
    assert "CRITICAL BEC ALERT" in msg_bec

    # 3. Beneficiary name match score
    score_clean = calculate_beneficiary_match("Apex Courier", "Apex Global Logistics Private Limited", "Apex Courier")
    assert score_clean >= 0.70

    score_divergent = calculate_beneficiary_match("Specter Mules LLC", "Apex Global Logistics Private Limited", "Apex Courier")
    assert score_divergent < 0.40

def test_statutory_split_settlement_and_ims_action():
    """
    Pre-Disbursal Payment Gate & Dynamic GST Split-Settlement Engine:
    Validates 3-Tier Settlement recommendations:
    - Clean: FULL_DISBURSAL (IMS: ACCEPT)
    - Moderate risk/MSME 43B(h): STATUTORY_GST_ESCROW (IMS: PENDING_HOLD)
    - Critical Risk/Insolvency/BEC: FORENSIC_FREEZE (IMS: REJECT)
    """
    engine = ForensicRiskEngine()

    # 1. Moderate risk vendor (Trade name discrepancy -> STATUTORY_GST_ESCROW)
    inv_split = InvoiceClaim(
        invoice_number="INV-2026-7001",
        supplier_name="Apex Logistics Hub",
        legal_name="Apex Global Logistics Pvt Ltd",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=400000.0,
        cgst=36000.0,
        sgst=36000.0,
        total_amount=472000.0,
        gstin_format_valid=True,
        arithmetic_valid=True
    )
    directors = [
        DirectorProfile(din="02341908", name="Sanjay Singhal", associated_companies_count=2, struck_off_companies_count=0)
    ]
    address = AddressClusterProfile(raw_address="Plot 44, Okhla Industrial Area", collocated_gstins_count=1, premises_type="INDUSTRIAL_WAREHOUSE")
    field_checks = [
        FieldCheckResult(
            check_id="chk_name",
            field_name="Trade vs Legal Name",
            status=CheckStatus.POSSIBLE_MATCH,
            reason_code="LEGAL_NAME_MISMATCH",
            explanation="Trade alias difference"
        )
    ]

    ass_split = engine.evaluate(
        case_id="case_split_demo",
        invoice=inv_split,
        field_checks=field_checks,
        directors=directors,
        address_cluster=address,
        litigation_meta={"active_cases": 0},
        evidence_items=[]
    )

    assert ass_split.recommendation == RecommendationOutcome.MANUAL_REVIEW
    assert ass_split.treasury_settlement is not None
    assert ass_split.treasury_settlement.recommendation == "STATUTORY_GST_ESCROW"
    # Base released immediately for MSME Sec 43B(h) compliance
    assert ass_split.treasury_settlement.release_now_inr == 400000.0
    # GST tax held in automated escrow for Sec 16(2)(c) safeguard
    assert ass_split.treasury_settlement.escrow_hold_gst_inr == 72000.0
    assert ass_split.treasury_settlement.gstn_ims_action == "PENDING_HOLD"
    # Clawback risk avoided: 72000 * 2.18 = 156960.0
    assert ass_split.treasury_settlement.statutory_clawback_risk_avoided_inr == 156960.0
    assert ass_split.gstn_ims_action == "PENDING_HOLD"
    assert ass_split.ims_action_json["ims_action"] == "PENDING_HOLD"

    # 2. Critical Bank Account Mutation -> FORENSIC_FREEZE (IMS: REJECT)
    inv_freeze = InvoiceClaim(
        invoice_number="INV-2026-9002",
        supplier_name="Apex Courier",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        total_amount=118000.0,
        gstin_format_valid=True,
        arithmetic_valid=True,
        bank_mutation_detected=True  # Trigger BEC guard!
    )
    ass_freeze = engine.evaluate(
        case_id="case_freeze_demo",
        invoice=inv_freeze,
        field_checks=[],
        directors=directors,
        address_cluster=address,
        litigation_meta={"active_cases": 0},
        evidence_items=[]
    )
    assert ass_freeze.recommendation == RecommendationOutcome.BLOCK
    assert "CRITICAL_BANK_ACCOUNT_MUTATION" in ass_freeze.hard_gates_triggered
    assert ass_freeze.treasury_settlement.recommendation == "FORENSIC_FREEZE"
    assert ass_freeze.treasury_settlement.release_now_inr == 0.0
    assert ass_freeze.treasury_settlement.escrow_hold_gst_inr == 118000.0
    assert ass_freeze.treasury_settlement.gstn_ims_action == "REJECT"

@pytest.mark.asyncio
async def test_havells_live_demo_orchestrator_fixture():
    """
    Validates the 4-Hop TinyFish Havells India Limited Enterprise demo scenario.
    """
    orchestrator = MultiHopTinyFishOrchestrator()
    evidence, directors, address, litigation = await orchestrator.execute_investigation(
        supplier_name="Havells Industrial Electricals",
        gstin="07AAACH0828A1ZE",
        primary_item="Havells 3 Core 4 sqmm Copper Armoured Cable",
        billed_unit_price=422500.0
    )

    assert len(evidence) == 4
    hop1 = next(e for e in evidence if e.hop_number == 1)
    hop2 = next(e for e in evidence if e.hop_number == 2)
    hop3 = next(e for e in evidence if e.hop_number == 3)
    hop4 = next(e for e in evidence if e.hop_number == 4)

    assert "Havells" in hop1.facts.get("legal_name", "")
    assert hop2.facts.get("insolvency_or_tax_fraud_flag") is False
    assert hop3.facts.get("enforcement_hit") is False
    assert litigation["procurement_benchmark"].market_median_price_inr == 82000.0
    assert litigation["procurement_benchmark"].price_inflation_pct == 3.0
