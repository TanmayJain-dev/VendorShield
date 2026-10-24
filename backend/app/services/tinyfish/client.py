import httpx
import logging
import urllib.parse
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ValidationError

from ...schemas.evidence import EvidenceItem
from ...schemas.enums import SourceMode
from ...config import settings

logger = logging.getLogger(__name__)

# Schema for external TinyFish API validation
class TinyFishRunResponse(BaseModel):
    result: Optional[Any] = None
    extracted_facts: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: Optional[str] = None
    error: Optional[str] = None

def sanitize_untrusted_web_content(content: str) -> str:
    """
    Sanitizes external web content:
    - Strips raw HTML and script tags.
    - Truncates excessive payloads.
    - Mitigates prompt injection / instruction-injection artifacts.
    """
    if not content:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]*>", " ", str(content))
    # Strip dangerous instruction keywords
    cleaned = re.sub(r"(?i)(ignore (all|previous) instructions|system prompt|developer mode)", "[REDACTED_PROMPT_INJECTION]", cleaned)
    # Collapse whitespace
    tokens = [t for t in cleaned.split() if t]
    sanitized = " ".join(tokens)
    return sanitized[:1200]

class TinyFishService:
    """
    Client for TinyFish Browser Automation & Web Research API.
    Axiom: TinyFish researches; VendorShield decides.
    Ensures safe encoding, strict schema validation, timeout/rate-limit resilience,
    and unforgeable provenance labeling (LIVE vs SIMULATED vs UNAVAILABLE).
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TINYFISH_API_KEY
        self.api_url = settings.TINYFISH_API_URL
        self.configured_mode = SourceMode.LIVE if self.api_key else SourceMode.SIMULATED
        self.last_effective_mode = self.configured_mode

    @property
    def source_mode(self) -> SourceMode:
        return self.configured_mode

    async def investigate_vendor(
        self,
        supplier_name: str,
        gstin: Optional[str] = None
    ) -> List[EvidenceItem]:
        """
        Runs bounded public-web investigation for a vendor.
        Returns source-linked evidence items with raw excerpts and timestamps.
        Sets self.last_effective_mode to LIVE or SIMULATED.
        """
        if self.configured_mode == SourceMode.LIVE:
            items, mode = await self._run_live_investigation(supplier_name, gstin)
            self.last_effective_mode = mode
            return items
        else:
            items = self._run_simulated_investigation(supplier_name, gstin, is_fallback=False)
            self.last_effective_mode = SourceMode.SIMULATED
            return items

    async def _run_live_investigation(
        self,
        supplier_name: str,
        gstin: Optional[str]
    ) -> Tuple[List[EvidenceItem], SourceMode]:
        """Calls the real TinyFish API with robust schema validation and failure fallbacks."""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        evidence_items: List[EvidenceItem] = []
        live_errors: List[str] = []
        now = datetime.now(timezone.utc).isoformat()

        # 1. Investigate GST Registration if GSTIN provided
        if gstin:
            safe_gstin = urllib.parse.quote_plus(gstin.strip())
            payload = {
                "url": "https://service.gst.gov.in/services/searchtp",
                "goal": f"Search for GSTIN {safe_gstin} and extract legal entity name, trade name, and registration status."
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(self.api_url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        raw_json = resp.json()
                        validated = TinyFishRunResponse(**raw_json)
                        excerpt = sanitize_untrusted_web_content(str(validated.result or raw_json))
                        evidence_items.append(
                            EvidenceItem(
                                evidence_id="ev_live_gst",
                                source_url="https://service.gst.gov.in/services/searchtp",
                                source_name="GST Public Search Portal (Live via TinyFish)",
                                claim_supported="GSTIN & Legal Entity Registration",
                                source_type="PUBLIC_REGISTRY",
                                source_mode=SourceMode.LIVE,
                                is_fallback=False,
                                raw_excerpt=excerpt,
                                facts=validated.extracted_facts or {},
                                is_authoritative=True,
                                retrieved_at=now,
                                match_rationale="Live browser automation retrieval from official GST portal."
                            )
                        )
                    elif resp.status_code == 429:
                        live_errors.append("TinyFish API rate limit exceeded (HTTP 429)")
                    else:
                        live_errors.append(f"TinyFish GST lookup returned HTTP {resp.status_code}")
            except httpx.TimeoutException:
                live_errors.append("TinyFish live GST query timed out (>30s)")
            except ValidationError as ve:
                live_errors.append(f"TinyFish GST response schema validation error: {ve}")
            except Exception as e:
                live_errors.append(f"Live TinyFish GST lookup failed: {str(e)}")

        # 2. General corporate web footprint
        encoded_query = urllib.parse.quote_plus(f"{supplier_name} headquarters office India")
        query_url = f"https://www.google.com/search?q={encoded_query}"
        payload = {
            "url": query_url,
            "goal": f"Find official website, registered office address, and parent company for {supplier_name}."
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.api_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    raw_json = resp.json()
                    validated = TinyFishRunResponse(**raw_json)
                    excerpt = sanitize_untrusted_web_content(str(validated.result or raw_json))
                    evidence_items.append(
                        EvidenceItem(
                            evidence_id="ev_live_web",
                            source_url=query_url,
                            source_name="Web Search Footprint (Live via TinyFish)",
                            claim_supported="Business Footprint & Operational Presence",
                            source_type="PUBLIC_WEB",
                            source_mode=SourceMode.LIVE,
                            is_fallback=False,
                            raw_excerpt=excerpt,
                            facts=validated.extracted_facts or {},
                            is_authoritative=False,
                            retrieved_at=now,
                            match_rationale="Live browser automation search for operational web footprint."
                        )
                    )
                elif resp.status_code == 429:
                    live_errors.append("TinyFish API rate limit exceeded (HTTP 429) on web search")
                else:
                    live_errors.append(f"TinyFish web research returned HTTP {resp.status_code}")
        except httpx.TimeoutException:
            live_errors.append("TinyFish live web search query timed out (>30s)")
        except ValidationError as ve:
            live_errors.append(f"TinyFish web response schema validation error: {ve}")
        except Exception as e:
            live_errors.append(f"Live TinyFish web research failed: {str(e)}")

        # If live calls yielded evidence, return them with LIVE mode
        if evidence_items:
            return evidence_items, SourceMode.LIVE

        # If live calls failed, fallback to simulated fixture with explicit fallback warnings
        fallback_reason = "; ".join(live_errors) or "Live TinyFish lookup produced no data"
        logger.warning(f"Live research failed ({fallback_reason}). Falling back to transparent SIMULATED evidence.")
        fallback_items = self._run_simulated_investigation(supplier_name, gstin, is_fallback=True, fallback_reason=fallback_reason)
        return fallback_items, SourceMode.SIMULATED

    def _run_simulated_investigation(
        self,
        supplier_name: str,
        gstin: Optional[str],
        is_fallback: bool = False,
        fallback_reason: Optional[str] = None
    ) -> List[EvidenceItem]:
        """
        Deterministic, transparent simulation fixtures for development, testing, and hackathon demos.
        Explicitly marked with SourceMode.SIMULATED.
        """
        now = datetime.now(timezone.utc).isoformat()
        supp_lower = (supplier_name or "").lower()

        # Benchmark Case: Apex Courier
        if "apex" in supp_lower:
            return [
                EvidenceItem(
                    evidence_id="ev_sim_gst_01",
                    source_url="https://service.gst.gov.in/services/searchtp",
                    source_name="GST Portal Public Registry [Simulated]",
                    claim_supported="Legal Entity & Registration Status",
                    source_type="PUBLIC_REGISTRY",
                    source_mode=SourceMode.SIMULATED,
                    is_fallback=is_fallback,
                    fallback_reason=fallback_reason,
                    retrieved_at=now,
                    raw_excerpt="GSTIN: 07AAAAA0000A1Z5 | Legal Name: Apex Global Logistics Private Limited | Trade Name: Apex Courier | Status: Active | Constitution: Private Limited Company",
                    facts={
                        "legal_name": "Apex Global Logistics Private Limited",
                        "trade_name": "Apex Courier",
                        "status": "Active",
                        "state": "Delhi",
                        "entity_type": "Private Limited Company"
                    },
                    is_authoritative=True,
                    match_rationale="Simulated official GST registration record for benchmark entity."
                ),
                EvidenceItem(
                    evidence_id="ev_sim_mca_02",
                    source_url="https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do",
                    source_name="Ministry of Corporate Affairs [Simulated]",
                    claim_supported="Registered Address & Directorship",
                    source_type="PUBLIC_REGISTRY",
                    source_mode=SourceMode.SIMULATED,
                    is_fallback=is_fallback,
                    fallback_reason=fallback_reason,
                    retrieved_at=now,
                    raw_excerpt="CIN: U63090DL2018PTC334455 | Registered Office: Phase-II, Okhla Industrial Area, New Delhi - 110020",
                    facts={
                        "cin": "U63090DL2018PTC334455",
                        "registered_address": "Phase-II, Okhla Industrial Area, New Delhi - 110020",
                        "incorporation_date": "2018-04-12"
                    },
                    is_authoritative=True,
                    match_rationale="Simulated MCA company master data fixture."
                ),
                EvidenceItem(
                    evidence_id="ev_sim_bank_03",
                    source_url="https://rbi.org.in/scripts/IFSC.aspx",
                    source_name="RBI IFSC Directory [Simulated]",
                    claim_supported="Bank Branch Reference Only (NOT Ownership)",
                    source_type="REFERENCE_DIRECTORY",
                    source_mode=SourceMode.SIMULATED,
                    is_fallback=is_fallback,
                    fallback_reason=fallback_reason,
                    retrieved_at=now,
                    raw_excerpt="IFSC: HDFC0000123 | Bank: HDFC Bank | Branch: Okhla Phase II | City: New Delhi. NOTE: Public directory confirms branch existence; cannot confirm account beneficiary.",
                    facts={
                        "bank_name": "HDFC Bank",
                        "branch": "Okhla Phase II",
                        "ownership_verified": False
                    },
                    is_authoritative=False,
                    match_rationale="Public directory confirms IFSC branch; beneficiary ownership is explicitly unverified."
                )
            ]

        # Ghost Vendor / Suspended Scenario
        if "specter" in supp_lower or "ghost" in supp_lower:
            return [
                EvidenceItem(
                    evidence_id="ev_sim_ghost_gst",
                    source_url="https://service.gst.gov.in/services/searchtp",
                    source_name="GST Portal Public Registry [Simulated]",
                    claim_supported="Legal Entity & Registration Status",
                    source_type="PUBLIC_REGISTRY",
                    source_mode=SourceMode.SIMULATED,
                    is_fallback=is_fallback,
                    fallback_reason=fallback_reason,
                    retrieved_at=now,
                    raw_excerpt="GSTIN: 07AAAAA0000A1Z5 | Legal Name: Apex Global Logistics Private Limited | Trade Name: Apex Courier | Status: Active",
                    facts={
                        "legal_name": "Apex Global Logistics Private Limited",
                        "trade_name": "Apex Courier",
                        "status": "Active"
                    },
                    is_authoritative=True,
                    match_rationale="GSTIN belongs to Apex Global Logistics, but invoice claims Specter Cloud Technologies (Name Conflict)."
                )
            ]

        # General Unknown Entity Simulation
        return [
            EvidenceItem(
                evidence_id="ev_sim_gen_01",
                source_url="https://service.gst.gov.in/services/searchtp",
                source_name="GST Public Search [Simulated]",
                claim_supported="Legal Identity",
                source_type="PUBLIC_WEB",
                source_mode=SourceMode.SIMULATED,
                is_fallback=is_fallback,
                fallback_reason=fallback_reason,
                retrieved_at=now,
                raw_excerpt=f"Record query for '{supplier_name}': No definitive corporate registry match located in public indices.",
                facts={"query": supplier_name, "status": "UNKNOWN"},
                is_authoritative=False,
                match_rationale="No conclusive public registry record located for this supplier name."
            )
        ]
