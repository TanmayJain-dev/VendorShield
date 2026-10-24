import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .base import GstinProvider
from ...schemas.evidence import EvidenceItem
from ...schemas.enums import SourceMode
from ...config import settings

DEMO_FIXTURES = {
    "07AAAAA0000A1Z4": {
        "legal_name": "Apex Global Logistics Private Limited",
        "trade_name": "Apex Global Logistics",
        "status": "Active",
        "registration_date": "2018-07-01",
        "constitution_of_business": "Private Limited Company",
        "taxpayer_type": "Regular"
    },
    "07BSPCT9999C1ZE": {
        "legal_name": "Specter Technical Services Private Limited",
        "trade_name": "Specter Solutions",
        "status": "Cancelled",
        "registration_date": "2021-03-15",
        "constitution_of_business": "Private Limited Company",
        "taxpayer_type": "Regular"
    },
    "07AQKPS1111Q1ZH": {
        "legal_name": "QuickPrint Media Enterprise",
        "trade_name": "QuickPrint Express",
        "status": "Active",
        "registration_date": "2019-11-20",
        "constitution_of_business": "Proprietorship",
        "taxpayer_type": "Regular"
    }
}

class DemoProvider(GstinProvider):
    """
    Demo Provider: strictly isolated synthetic demonstration fixtures.
    Only active when DEMO_MODE=true and case.is_demo=true.
    """
    async def lookup(self, gstin: str, case_context: Optional[Dict[str, Any]] = None) -> EvidenceItem:
        ctx = case_context or {}
        is_demo_case = ctx.get("is_demo", False)
        
        # Invariant: Demo fixtures are never returned for real non-demo cases
        if not (settings.DEMO_MODE and is_demo_case):
            return EvidenceItem(
                evidence_id=f"ev_demo_{uuid.uuid4().hex[:8]}",
                source_url="https://services.gst.gov.in/services/searchtp",
                source_name="GST Search Taxpayer (Demo Provider)",
                claim_supported="Legal Entity and GST Status",
                source_type="SYNTHETIC_FIXTURE",
                source_mode=SourceMode.UNAVAILABLE,
                is_fallback=True,
                is_authoritative=False,
                facts={"status": "UNAVAILABLE", "detail": "Demo provider inactive for production cases"},
                retrieved_at=datetime.now(timezone.utc).isoformat()
            )

        clean_gstin = gstin.strip().upper()
        fixture = DEMO_FIXTURES.get(clean_gstin)
        if not fixture:
            # Fallback demo fixture
            fixture = {
                "legal_name": f"Demo Entity for {clean_gstin}",
                "trade_name": "Demo Trade Name",
                "status": "Active",
                "registration_date": "2020-01-01",
                "constitution_of_business": "Private Limited Company",
                "taxpayer_type": "Regular"
            }

        facts = dict(fixture)
        facts["gstin"] = clean_gstin

        return EvidenceItem(
            evidence_id=f"ev_demo_{uuid.uuid4().hex[:8]}",
            source_url="https://services.gst.gov.in/services/searchtp",
            source_name="GST Search Taxpayer (Demonstration Fixture)",
            claim_supported="Legal Entity and GST Status (Demo Data)",
            source_type="SYNTHETIC_FIXTURE",
            source_mode=SourceMode.SIMULATED,
            is_fallback=False,
            is_authoritative=False,
            facts=facts,
            retrieved_at=datetime.now(timezone.utc).isoformat()
        )
