import pytest
from app.services.tinyfish.client import TinyFishService
from app.schemas.enums import SourceMode

@pytest.mark.asyncio
async def test_tinyfish_simulated_mode():
    service = TinyFishService(api_key="")
    assert service.source_mode == SourceMode.SIMULATED

    evidence = await service.investigate_vendor(
        supplier_name="Apex Courier",
        gstin="07AAAAA0000A1Z5"
    )
    assert len(evidence) >= 2
    # Verify sources and facts
    gst_item = next((e for e in evidence if "gst" in e.source_name.lower()), None)
    assert gst_item is not None
    assert gst_item.facts.get("legal_name") == "Apex Global Logistics Private Limited"
    assert gst_item.facts.get("status") == "Active"
