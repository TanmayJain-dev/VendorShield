import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from app.services.tinyfish.orchestrator import MultiHopTinyFishOrchestrator
from app.schemas.enums import SourceMode

@pytest.mark.asyncio
async def test_multihop_orchestrator_apex_courier():
    orchestrator = MultiHopTinyFishOrchestrator(api_key="")
    assert orchestrator.source_mode == SourceMode.SIMULATED

    evidence, directors, address, litigation = await orchestrator.execute_investigation(
        supplier_name="Apex Courier",
        gstin="07AAAAA0000A1Z5"
    )

    # 4 Hops executed
    assert len(evidence) == 4
    assert len(directors) >= 1
    assert directors[0].name == "Sanjay Singhal"
    assert directors[0].struck_off_companies_count == 0
    assert address.is_ghost_hub is False
    assert litigation["active_cases"] == 0

@pytest.mark.asyncio
async def test_multihop_orchestrator_simulated_provenance_truth_invariants():
    """Verify simulation mode never claims to be live authoritative evidence."""
    orchestrator = MultiHopTinyFishOrchestrator(api_key="")
    evidence, directors, address, litigation = await orchestrator.execute_investigation(
        supplier_name="Apex Courier",
        gstin="07AAAAA0000A1Z5"
    )

    assert orchestrator.source_mode == SourceMode.SIMULATED
    for ev in evidence:
        assert ev.source_mode == SourceMode.SIMULATED
        assert ev.is_fallback is True
        assert ev.is_authoritative is False
        assert ev.fallback_reason is not None
        assert "DEMO" in ev.source_name
        assert "demo://" in ev.source_url

@pytest.mark.asyncio
async def test_multihop_orchestrator_specter_shell():
    orchestrator = MultiHopTinyFishOrchestrator(api_key="")
    evidence, directors, address, litigation = await orchestrator.execute_investigation(
        supplier_name="Specter Cloud Technologies",
        gstin="07AAAAA0000A1Z5"
    )

    assert len(evidence) == 4
    # Director shell contagion detected in Hop 2
    assert len(directors) >= 1
    assert directors[0].struck_off_companies_count == 6
    assert directors[0].contagion_ratio > 0.4
    # Ghost hub detected in Hop 3
    assert address.collocated_gstins_count == 38
    assert address.is_ghost_hub is True
    # NCLT petition detected in Hop 4
    assert litigation["active_cases"] == 1

@pytest.mark.asyncio
async def test_multihop_orchestrator_live_all_fail_records_unavailable():
    """When live API calls fail, record as UNAVAILABLE; never silently substitute fixtures."""
    orchestrator = MultiHopTinyFishOrchestrator(api_key="tf_live_test_key_123")
    
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("Connection timed out to TinyFish")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        evidence, directors, address, litigation = await orchestrator.execute_investigation(
            supplier_name="Acme Corp",
            gstin="07AAAAA0000A1Z5",
            address="123 Industrial Area"
        )

    # Must be marked UNAVAILABLE, not SIMULATED and not LIVE
    assert orchestrator.source_mode == SourceMode.UNAVAILABLE
    assert len(evidence) >= 1
    for ev in evidence:
        assert ev.source_mode == SourceMode.UNAVAILABLE
        assert ev.is_authoritative is False
        assert "failed or timed out" in ev.raw_excerpt.lower()
    # Unqueried director/litigation data must not be assumed clean
    assert len(directors) == 0

@pytest.mark.asyncio
async def test_multihop_orchestrator_live_partial_success():
    """When some hops succeed and others fail, results must remain explicitly partial."""
    orchestrator = MultiHopTinyFishOrchestrator(api_key="tf_live_test_key_123")

    mock_resp_success = MagicMock()
    mock_resp_success.status_code = 200
    mock_resp_success.json.return_value = {
        "result": "GSTIN 07AAAAA0000A1Z5 Active",
        "extracted_facts": {"status": "Active", "legal_name": "Acme Corp Private Limited"}
    }

    mock_resp_fail = MagicMock()
    mock_resp_fail.status_code = 502
    mock_resp_fail.text = "Bad Gateway"

    mock_client = AsyncMock()
    # Hop 1 succeeds, Hops 2-4 fail
    mock_client.post.side_effect = [mock_resp_success, mock_resp_fail, mock_resp_fail, mock_resp_fail]

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        evidence, directors, address, litigation = await orchestrator.execute_investigation(
            supplier_name="Acme Corp",
            gstin="07AAAAA0000A1Z5",
            address="123 Industrial Area"
        )

    assert orchestrator.source_mode == SourceMode.LIVE
    hop1 = next(e for e in evidence if "ev_hop1" in e.evidence_id)
    assert hop1.source_mode == SourceMode.LIVE
    assert hop1.is_authoritative is True

    hop2 = next(e for e in evidence if "ev_hop2" in e.evidence_id)
    assert hop2.source_mode == SourceMode.UNAVAILABLE
    assert hop2.is_authoritative is False
    assert len(directors) == 0

@pytest.mark.asyncio
async def test_multihop_orchestrator_malformed_live_response():
    """Defensively handle malformed or unexpected JSON from live responses."""
    orchestrator = MultiHopTinyFishOrchestrator(api_key="tf_live_test_key_123")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = "Not a dict, just a plain string"

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        evidence, directors, address, litigation = await orchestrator.execute_investigation(
            supplier_name="Acme Corp",
            gstin="07AAAAA0000A1Z5",
            address="123 Industrial Area"
        )

    assert len(evidence) >= 1

@pytest.mark.asyncio
async def test_hop1_succeeds_hops_2_to_4_fail_downgrades_pass_to_manual_review():
    """
    Evidence Completeness Rule Invariant:
    When Hop 1 succeeds but Hops 2-4 fail, all unavailable dimensions must be
    explicitly recorded, evidence_completeness must be PARTIAL (never COMPLETE),
    and the final policy recommendation must fail closed to MANUAL_REVIEW (never PASS).
    """
    from backend.app.services.rules.forensic_engine import ForensicRiskEngine
    from backend.app.schemas.invoice import InvoiceClaim
    from backend.app.schemas.enums import RecommendationOutcome

    orchestrator = MultiHopTinyFishOrchestrator(api_key="tf_live_test_key_123")

    mock_resp_success = MagicMock()
    mock_resp_success.status_code = 200
    mock_resp_success.json.return_value = {
        "result": "GSTIN 07AAAAA0000A1Z5 Active",
        "extracted_facts": {
            "status": "Active",
            "legal_name": "Apex Courier Private Limited",
            "trade_name": "Apex Courier",
            "filing_delay_months": 0
        }
    }

    mock_resp_fail = MagicMock()
    mock_resp_fail.status_code = 503
    mock_resp_fail.text = "Service Unavailable"

    mock_client = AsyncMock()
    # Hop 1 succeeds, Hops 2, 3, 4 fail
    mock_client.post.side_effect = [mock_resp_success, mock_resp_fail, mock_resp_fail, mock_resp_fail]

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        evidence, directors, address, litigation = await orchestrator.execute_investigation(
            supplier_name="Apex Courier",
            gstin="07AAAAA0000A1Z5",
            address="Plot 44, Okhla Phase 3, New Delhi"
        )

    # 1. Verify all 4 research dimensions are explicitly represented
    assert len(evidence) == 4
    hop1 = next(e for e in evidence if "ev_hop1" in e.evidence_id)
    hop2 = next(e for e in evidence if "ev_hop2" in e.evidence_id)
    hop3 = next(e for e in evidence if "ev_hop3" in e.evidence_id)
    hop4 = next(e for e in evidence if "ev_hop4" in e.evidence_id)

    assert hop1.source_mode == SourceMode.LIVE
    assert hop1.is_authoritative is True

    assert hop2.source_mode == SourceMode.UNAVAILABLE
    assert hop3.source_mode == SourceMode.UNAVAILABLE
    assert hop4.source_mode == SourceMode.UNAVAILABLE

    # 2. Evaluate with ForensicRiskEngine
    invoice = InvoiceClaim(
        invoice_number="INV-2026-001",
        invoice_date="2026-10-20",
        supplier_name="Apex Courier",
        legal_name="Apex Courier Private Limited",
        gstin="07AAAAA0000A1Z5",
        taxable_amount=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        total_amount=118000.0,
        gstin_format_valid=True,
        arithmetic_valid=True,
        raw_text="Sample clean invoice text"
    )

    forensic_engine = ForensicRiskEngine()
    assessment = forensic_engine.evaluate(
        case_id="case_multihop_partial",
        invoice=invoice,
        field_checks=[],
        directors=directors,
        address_cluster=address,
        litigation_meta=litigation,
        evidence_items=evidence
    )

    # 3. Assert evidence completeness is PARTIAL, not COMPLETE
    assert assessment.evidence_completeness == "PARTIAL"
    # 4. Invariant: Recommendation MUST be MANUAL_REVIEW, NEVER PASS
    assert assessment.recommendation == RecommendationOutcome.MANUAL_REVIEW
    assert "INCOMPLETE_EVIDENCE_FAIL_CLOSED" in assessment.reason_codes
