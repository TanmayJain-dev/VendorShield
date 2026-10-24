import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .base import GstinProvider
from ...schemas.evidence import EvidenceItem
from ...schemas.enums import SourceMode

class ManualEntryProvider(GstinProvider):
    """
    Manual Entry Provider: Reviewer submits public portal taxpayer verification
    details. Stored as authoritative evidence because attested by a named human reviewer.
    """
    def __init__(self, attested_by: str = "reviewer"):
        self.attested_by = attested_by

    async def lookup(self, gstin: str, case_context: Optional[Dict[str, Any]] = None) -> EvidenceItem:
        ctx = case_context or {}
        legal_name = ctx.get("legal_name", "")
        trade_name = ctx.get("trade_name", "")
        status = ctx.get("status", "Active")
        reg_date = ctx.get("registration_date")
        source_url = ctx.get("source_url", "https://services.gst.gov.in/services/searchtp")
        taxpayer_type = ctx.get("taxpayer_type", "Regular")
        constitution = ctx.get("constitution_of_business", "")

        facts = {
            "gstin": gstin.upper(),
            "legal_name": legal_name,
            "trade_name": trade_name,
            "status": status,
            "registration_date": reg_date,
            "taxpayer_type": taxpayer_type,
            "constitution_of_business": constitution,
            "attested_by": self.attested_by,
            "attested_at": datetime.now(timezone.utc).isoformat()
        }

        return EvidenceItem(
            evidence_id=f"ev_man_{uuid.uuid4().hex[:8]}",
            source_url=source_url,
            source_name="GST Public Search Portal (Attested by Reviewer)",
            claim_supported=f"Legal Entity and GST Registration Details (Manual Entry by {self.attested_by})",
            source_type="PUBLIC_REGISTRY_ATTESTED",
            source_mode=SourceMode.MANUAL,
            is_fallback=False,
            is_authoritative=True,
            facts=facts,
            retrieved_at=datetime.now(timezone.utc).isoformat()
        )
