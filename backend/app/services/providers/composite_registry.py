import logging
from typing import Optional, Dict, Any, List
from .base import GstinProvider
from .manual_provider import ManualEntryProvider
from .http_kyc_provider import HttpKycProvider
from .tinyfish_provider import TinyFishProvider
from .demo_provider import DemoProvider
from ...schemas.evidence import EvidenceItem
from ...schemas.enums import SourceMode
from ...config import settings

logger = logging.getLogger(__name__)

class CompositeRegistryProvider:
    """
    Orchestrates GSTIN verification across configured pluggable providers.
    Sequence is governed by settings.GSTIN_PROVIDERS (e.g. 'http_kyc,manual', 'tinyfish,manual').
    If all configured providers return UNAVAILABLE, yields an explicit UNAVAILABLE evidence item.
    """
    def __init__(self, provider_names: Optional[str] = None):
        names_str = provider_names or settings.GSTIN_PROVIDERS or "manual"
        self.provider_names = [p.strip().lower() for p in names_str.split(",") if p.strip()]

    def _get_provider_instance(self, name: str) -> Optional[GstinProvider]:
        if name in ["http_kyc", "http", "kyc"]:
            return HttpKycProvider()
        elif name in ["tinyfish", "tf"]:
            return TinyFishProvider()
        elif name in ["demo", "simulated"]:
            return DemoProvider()
        elif name in ["manual", "reviewer"]:
            return ManualEntryProvider()
        return None

    async def lookup(self, gstin: str, case_context: Optional[Dict[str, Any]] = None) -> EvidenceItem:
        if not gstin or not gstin.strip():
            return EvidenceItem(
                evidence_id="ev_none",
                source_url="",
                source_name="Registry Provider",
                claim_supported="Legal Entity and GST Status",
                source_type="NONE",
                source_mode=SourceMode.UNAVAILABLE,
                is_fallback=True,
                is_authoritative=False,
                facts={"status": "UNAVAILABLE", "detail": "Missing GSTIN"}
            )

        last_evidence = None

        for name in self.provider_names:
            provider = self._get_provider_instance(name)
            if not provider:
                continue
            
            try:
                ev = await provider.lookup(gstin, case_context=case_context)
                last_evidence = ev
                # If provider returned valid live/manual or authorized demo data
                if ev.source_mode != SourceMode.UNAVAILABLE and ev.facts.get("status") != "UNAVAILABLE":
                    return ev
            except Exception as e:
                logger.warning(f"Provider {name} lookup failed: {e}")

        # If none succeeded, return the last UNAVAILABLE item or build a fresh one
        return last_evidence or EvidenceItem(
            evidence_id="ev_none",
            source_url="https://services.gst.gov.in/services/searchtp",
            source_name="Public GST Registry",
            claim_supported="Legal Entity and GST Status",
            source_type="PUBLIC_REGISTRY",
            source_mode=SourceMode.UNAVAILABLE,
            is_fallback=True,
            is_authoritative=False,
            facts={"status": "UNAVAILABLE", "detail": "No registry provider returned verified data"}
        )
