import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .base import GstinProvider
from ...schemas.evidence import EvidenceItem
from ...schemas.enums import SourceMode
from ...config import settings
from ..tinyfish.client import TinyFishClient

logger = logging.getLogger(__name__)

class TinyFishProvider(GstinProvider):
    """TinyFish automated public portal web research provider."""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TINYFISH_API_KEY
        self.client = TinyFishClient(api_key=self.api_key)

    async def lookup(self, gstin: str, case_context: Optional[Dict[str, Any]] = None) -> EvidenceItem:
        if not self.api_key:
            return EvidenceItem(
                evidence_id=f"ev_tf_{uuid.uuid4().hex[:8]}",
                source_url="https://services.gst.gov.in/services/searchtp",
                source_name="GST Search Taxpayer via TinyFish",
                claim_supported="Legal Entity and GST Status",
                source_type="WEB_AUTOMATION",
                source_mode=SourceMode.UNAVAILABLE,
                is_fallback=True,
                is_authoritative=False,
                facts={"status": "UNAVAILABLE", "detail": "TinyFish API key not configured"},
                retrieved_at=datetime.now(timezone.utc).isoformat()
            )

        try:
            schema = {
                "type": "object",
                "properties": {
                    "legal_name": {"type": "string"},
                    "trade_name": {"type": "string"},
                    "status": {"type": "string"},
                    "registration_date": {"type": "string"},
                    "constitution_of_business": {"type": "string"}
                },
                "required": ["legal_name", "status"]
            }
            res = await self.client.run_and_poll(
                url=f"https://services.gst.gov.in/services/searchtp",
                goal=f"Look up GSTIN {gstin} on the taxpayer search page and extract legal entity name, trade name, and active status.",
                output_schema=schema,
                max_steps=12,
                max_duration_seconds=45
            )
            if res.get("status") == "COMPLETED" and res.get("result"):
                facts = res["result"]
                facts["gstin"] = gstin.upper()
                return EvidenceItem(
                    evidence_id=f"ev_tf_{uuid.uuid4().hex[:8]}",
                    source_url="https://services.gst.gov.in/services/searchtp",
                    source_name="GST Search Taxpayer via TinyFish",
                    claim_supported="Legal Entity and GST Status from GST Portal Automation",
                    source_type="WEB_AUTOMATION",
                    source_mode=SourceMode.LIVE,
                    is_fallback=False,
                    is_authoritative=True,
                    facts=facts,
                    retrieved_at=datetime.now(timezone.utc).isoformat()
                )
            else:
                return EvidenceItem(
                    evidence_id=f"ev_tf_{uuid.uuid4().hex[:8]}",
                    source_url="https://services.gst.gov.in/services/searchtp",
                    source_name="GST Search Taxpayer via TinyFish",
                    claim_supported="Legal Entity and GST Status",
                    source_type="WEB_AUTOMATION",
                    source_mode=SourceMode.UNAVAILABLE,
                    is_fallback=True,
                    is_authoritative=False,
                    facts={"status": "UNAVAILABLE", "detail": res.get("error", "Web automation timed out or hit captcha")},
                    retrieved_at=datetime.now(timezone.utc).isoformat()
                )
        except Exception as e:
            logger.warning(f"TinyFish lookup exception: {e}")
            return EvidenceItem(
                evidence_id=f"ev_tf_{uuid.uuid4().hex[:8]}",
                source_url="https://services.gst.gov.in/services/searchtp",
                source_name="GST Search Taxpayer via TinyFish",
                claim_supported="Legal Entity and GST Status",
                source_type="WEB_AUTOMATION",
                source_mode=SourceMode.UNAVAILABLE,
                is_fallback=True,
                is_authoritative=False,
                facts={"status": "UNAVAILABLE", "detail": str(e)},
                retrieved_at=datetime.now(timezone.utc).isoformat()
            )
