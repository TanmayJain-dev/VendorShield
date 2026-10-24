import pytest
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
