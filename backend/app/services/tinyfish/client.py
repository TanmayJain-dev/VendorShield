import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from ...schemas.evidence import EvidenceItem
from ...schemas.enums import SourceMode
from ...config import settings

logger = logging.getLogger(__name__)

class TinyFishService:
    """
    Client for TinyFish Browser Automation & Web Research API.
    Axiom: TinyFish researches; VendorShield decides.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TINYFISH_API_KEY
        self.api_url = settings.TINYFISH_API_URL
        self.source_mode = SourceMode.LIVE if self.api_key else SourceMode.SIMULATED

    async def investigate_vendor(
        self,
        supplier_name: str,
        gstin: Optional[str] = None
    ) -> List[EvidenceItem]:
        """
        Runs bounded public-web investigation for a vendor.
        Returns source-linked evidence items with raw excerpts and timestamps.
        """
        if self.source_mode == SourceMode.LIVE:
            return await self._run_live_investigation(supplier_name, gstin)
        else:
            return self._run_simulated_investigation(supplier_name, gstin)

    async def _run_live_investigation(
        self,
        supplier_name: str,
        gstin: Optional[str]
    ) -> List[EvidenceItem]:
        """Calls the real TinyFish API at agent.tinyfish.ai."""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        evidence_items = []
        
        # 1. Investigate GST Registration if GSTIN provided
        if gstin:
            payload = {
                "url": f"https://service.gst.gov.in/services/searchtp",
                "goal": f"Search for GSTIN {gstin} and extract legal entity name, trade name, and registration status."
            }
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(self.api_url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        evidence_items.append(
                            EvidenceItem(
                                evidence_id="ev_tinyfish_gst",
                                source_url="https://service.gst.gov.in/services/searchtp",
                                source_name="GST Public Search Portal (via TinyFish)",
                                claim_supported="GSTIN & Legal Entity Registration",
                                raw_excerpt=str(data.get("result", data)),
                                facts=data.get("extracted_facts", {}),
                                is_authoritative=True,
                                retrieved_at=datetime.utcnow().isoformat() + "Z"
                            )
                        )
            except Exception as e:
                logger.warning(f"Live TinyFish GST lookup failed: {e}")

        # 2. General corporate web footprint
        query_url = f"https://www.google.com/search?q={supplier_name}+headquarters+office+India"
        payload = {
            "url": query_url,
            "goal": f"Find official website, registered office address, and parent company for {supplier_name}."
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(self.api_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    evidence_items.append(
                        EvidenceItem(
                            evidence_id="ev_tinyfish_web",
                            source_url=query_url,
                            source_name="Web Search Footprint (via TinyFish)",
                            claim_supported="Business Footprint & Operational Presence",
                            raw_excerpt=str(data.get("result", data)),
                            facts=data.get("extracted_facts", {}),
                            is_authoritative=False,
                            retrieved_at=datetime.utcnow().isoformat() + "Z"
                        )
                    )
        except Exception as e:
            logger.warning(f"Live TinyFish web research failed: {e}")

        # If live calls failed, fallback to simulated with warning
        if not evidence_items:
            return self._run_simulated_investigation(supplier_name, gstin)
            
        return evidence_items

    def _run_simulated_investigation(
        self,
        supplier_name: str,
        gstin: Optional[str]
    ) -> List[EvidenceItem]:
        """
        Deterministic, transparent simulation fixtures for development and hackathon demos.
        Never pretends to be live data — explicitly tagged with SIMULATED.
        """
        now = datetime.utcnow().isoformat() + "Z"
        
        # Benchmark Case: Apex Courier
        if "apex" in supplier_name.lower():
            return [
                EvidenceItem(
                    evidence_id="ev_sim_gst_01",
                    source_url="https://service.gst.gov.in/services/searchtp",
                    source_name="GST Portal Public Registry [Simulated]",
                    claim_supported="Legal Entity & Registration Status",
                    source_type="PUBLIC_REGISTRY",
                    retrieved_at=now,
                    raw_excerpt="GSTIN: 07AAAAA0000A1Z5 | Legal Name: Apex Global Logistics Private Limited | Trade Name: Apex Courier | Status: Active | Constitution: Private Limited Company",
                    facts={
                        "legal_name": "Apex Global Logistics Private Limited",
                        "trade_name": "Apex Courier",
                        "status": "Active",
                        "state": "Delhi",
                        "entity_type": "Private Limited Company"
                    },
                    is_authoritative=True
                ),
                EvidenceItem(
                    evidence_id="ev_sim_mca_02",
                    source_url="https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do",
                    source_name="Ministry of Corporate Affairs [Simulated]",
                    claim_supported="Registered Address & Directorship",
                    source_type="PUBLIC_REGISTRY",
                    retrieved_at=now,
                    raw_excerpt="CIN: U63090DL2018PTC334455 | Registered Office: Phase-II, Okhla Industrial Area, New Delhi - 110020",
                    facts={
                        "cin": "U63090DL2018PTC334455",
                        "registered_address": "Phase-II, Okhla Industrial Area, New Delhi - 110020",
                        "incorporation_date": "2018-04-12"
                    },
                    is_authoritative=True
                ),
                EvidenceItem(
                    evidence_id="ev_sim_bank_03",
                    source_url="https://rbi.org.in/scripts/IFSC.aspx",
                    source_name="RBI IFSC Directory [Simulated]",
                    claim_supported="Bank Branch Reference Only (NOT Ownership)",
                    source_type="REFERENCE_DIRECTORY",
                    retrieved_at=now,
                    raw_excerpt="IFSC: HDFC0000123 | Bank: HDFC Bank | Branch: Okhla Phase II | City: New Delhi. NOTE: Public directory confirms branch existence; cannot confirm account beneficiary.",
                    facts={
                        "bank_name": "HDFC Bank",
                        "branch": "Okhla Phase II",
                        "ownership_verified": False
                    },
                    is_authoritative=False
                )
            ]
        
        # Generic fallback simulation
        return [
            EvidenceItem(
                evidence_id="ev_sim_gen_01",
                source_url="https://service.gst.gov.in/services/searchtp",
                source_name="GST Public Search [Simulated]",
                claim_supported="Legal Identity",
                retrieved_at=now,
                raw_excerpt=f"Record found for query {supplier_name} under general trade registries.",
                facts={"query": supplier_name, "status": "UNKNOWN"},
                is_authoritative=False
            )
        ]
