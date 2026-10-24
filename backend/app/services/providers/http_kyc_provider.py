import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import httpx

from .base import GstinProvider
from ...schemas.evidence import EvidenceItem
from ...schemas.enums import SourceMode
from ...config import settings

logger = logging.getLogger(__name__)

class HttpKycProvider(GstinProvider):
    """
    Generic configurable HTTP KYC / GSP provider.
    Enables instant plug-and-play with external taxpayer verification APIs
    (Vayana, Signzy, Masters India, Sovos, etc.) via environment settings.
    """
    def __init__(
        self,
        url_template: Optional[str] = None,
        auth_header: Optional[str] = None,
        auth_value: Optional[str] = None,
        field_map_json: Optional[str] = None
    ):
        self.url_template = url_template or settings.GSTIN_API_URL_TEMPLATE
        self.auth_header = auth_header or settings.GSTIN_API_AUTH_HEADER
        self.auth_value = auth_value or settings.GSTIN_API_AUTH_VALUE
        self.field_map = {}
        raw_map = field_map_json or settings.GSTIN_API_FIELD_MAP
        if raw_map:
            try:
                self.field_map = json.loads(raw_map)
            except Exception:
                pass
        self.transport: Optional[httpx.AsyncBaseTransport] = None

    async def lookup(self, gstin: str, case_context: Optional[Dict[str, Any]] = None) -> EvidenceItem:
        if not self.url_template or "{gstin}" not in self.url_template:
            return EvidenceItem(
                evidence_id=f"ev_http_{uuid.uuid4().hex[:8]}",
                source_url="",
                source_name="HTTP KYC Provider",
                claim_supported="Legal Entity and GST Status",
                source_type="REGISTRY_API",
                source_mode=SourceMode.UNAVAILABLE,
                is_fallback=True,
                is_authoritative=False,
                facts={"status": "UNAVAILABLE", "detail": "HTTP KYC provider template not configured"},
                retrieved_at=datetime.now(timezone.utc).isoformat()
            )

        url = self.url_template.replace("{gstin}", gstin.strip().upper())
        headers = {}
        if self.auth_header and self.auth_value:
            headers[self.auth_header] = self.auth_value

        try:
            async with httpx.AsyncClient(timeout=8.0, transport=self.transport) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"HTTP KYC lookup returned status {resp.status_code}")
                    return self._unavailable(gstin, f"HTTP {resp.status_code}")
                
                raw_data = resp.json()
                mapped = self._map_fields(raw_data)
                mapped["gstin"] = gstin.upper()

                return EvidenceItem(
                    evidence_id=f"ev_http_{uuid.uuid4().hex[:8]}",
                    source_url=url,
                    source_name="Configured GST Registry API",
                    claim_supported="Legal Entity and GST Status from Official Registry API",
                    source_type="REGISTRY_API",
                    source_mode=SourceMode.LIVE,
                    is_fallback=False,
                    is_authoritative=True,
                    facts=mapped,
                    retrieved_at=datetime.now(timezone.utc).isoformat()
                )
        except Exception as e:
            logger.warning(f"HTTP KYC provider request failed: {e}")
            return self._unavailable(gstin, str(e))

    def _map_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Maps vendor response fields according to configured field map."""
        if not self.field_map:
            # Tolerant default mapping
            return {
                "legal_name": data.get("legal_name") or data.get("lgnm") or data.get("trade_name") or "",
                "trade_name": data.get("trade_name") or data.get("tradeNam") or "",
                "status": data.get("status") or data.get("sts") or "Active",
                "registration_date": data.get("registration_date") or data.get("rgdt"),
                "constitution_of_business": data.get("constitution_of_business") or data.get("ctb")
            }
        
        mapped = {}
        for target_key, src_path in self.field_map.items():
            val = data
            for part in src_path.split("."):
                if isinstance(val, dict):
                    val = val.get(part)
                else:
                    val = None
                    break
            mapped[target_key] = val
        return mapped

    def _unavailable(self, gstin: str, reason: str) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=f"ev_http_{uuid.uuid4().hex[:8]}",
            source_url=self.url_template.replace("{gstin}", gstin),
            source_name="Configured GST Registry API",
            claim_supported="Legal Entity and GST Status",
            source_type="REGISTRY_API",
            source_mode=SourceMode.UNAVAILABLE,
            is_fallback=True,
            is_authoritative=False,
            facts={"status": "UNAVAILABLE", "detail": reason},
            retrieved_at=datetime.now(timezone.utc).isoformat()
        )
