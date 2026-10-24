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
