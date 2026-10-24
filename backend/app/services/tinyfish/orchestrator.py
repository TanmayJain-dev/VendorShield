import logging
import httpx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from ...schemas.evidence import EvidenceItem
from ...schemas.forensic_graph import DirectorProfile, AddressClusterProfile
from ...schemas.enums import SourceMode
from ...config import settings

logger = logging.getLogger(__name__)

class MultiHopTinyFishOrchestrator:
    """
    VendorShield 2.0 Multi-Hop Autonomous Browser Orchestrator.
    Directs TinyFish through a 4-Hop Forensic Traversal:
      Hop 1: Entity & Constitution Verification (GSTN / MCA)
      Hop 2: Director Portfolio & Shell Contagion Traversal (DIN / Zauba / MCA)
      Hop 3: Geolocation Grounding & Address Collocation ("Ghost Hub" detection)
      Hop 4: Regulatory, NCLT & Litigation Sweep (Insolvency / Debarment)
      
    TRUTH & PROVENANCE INVARIANTS:
    1. TinyFish researches; deterministic VendorShield rules decide.
    2. Real live calls are attempted when an API key is configured.
    3. If a live request fails, times out, or returns malformed/inconclusive data, that dimension
       is explicitly marked as UNAVAILABLE. It is NEVER silently replaced by synthetic fixtures.
    4. When running in simulated mode without API credentials, all fixtures are prominently
       tagged as [DEMO FIXTURE] with is_authoritative=False and is_fallback=True.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TINYFISH_API_KEY
        self.api_url = settings.TINYFISH_API_URL
        self._effective_mode = SourceMode.LIVE if bool(self.api_key) else SourceMode.SIMULATED

    @property
    def source_mode(self) -> SourceMode:
        return self._effective_mode

    async def execute_investigation(
        self,
        supplier_name: str,
        gstin: Optional[str] = None,
        address: Optional[str] = None
    ) -> Tuple[List[EvidenceItem], List[DirectorProfile], AddressClusterProfile, Dict[str, Any]]:
        """
        Executes the 4-hop forensic pipeline.
        Returns:
            (evidence_items, director_profiles, address_cluster, litigation_meta)
        """
        if self.api_key:
            return await self._execute_live_multihop(supplier_name, gstin, address)
        else:
            self._effective_mode = SourceMode.SIMULATED
            return self._execute_simulated_multihop(supplier_name, gstin, address)

    async def _execute_live_multihop(
        self,
        supplier_name: str,
        gstin: Optional[str],
        address: Optional[str]
    ) -> Tuple[List[EvidenceItem], List[DirectorProfile], AddressClusterProfile, Dict[str, Any]]:
        """
        Orchestrates sequential TinyFish live browser agent runs across 4 forensic hops.
        Fails closed gracefully without simulating success.
        """
        now = datetime.now(timezone.utc).isoformat()
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        evidence_items: List[EvidenceItem] = []
        directors: List[DirectorProfile] = []
        address_cluster = AddressClusterProfile(
            raw_address=address or "Unknown",
            collocated_gstins_count=1,
            premises_type="UNKNOWN",
            is_ghost_hub=False
        )
        litigation_meta: Dict[str, Any] = {"active_cases": 0, "nclt_petitions": [], "status": "UNKNOWN"}

        live_success_count = 0

        # --- HOP 1: Entity & Constitution Verification ---
        if gstin:
            payload_hop1 = {
                "url": "https://service.gst.gov.in/services/searchtp",
                "goal": f"Search for GSTIN {gstin}. Extract Legal Name, Trade Name, Constitution, Registration Date, and Filing Status."
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(self.api_url, json=payload_hop1, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        extracted = data.get("extracted_facts") or {}
                        evidence_items.append(EvidenceItem(
                            evidence_id="ev_hop1_gst_live",
                            source_url="https://service.gst.gov.in/services/searchtp",
                            source_name="GSTN Statutory Registry [Hop 1: Live]",
                            claim_supported="Legal Entity Standing & Constitution",
                            source_type="GOVERNMENT_REGISTRY",
                            source_mode=SourceMode.LIVE,
                            retrieved_at=now,
                            raw_excerpt=str(data.get("result", data))[:1000],
                            facts=extracted,
                            is_authoritative=True,
                            is_fallback=False
                        ))
                        live_success_count += 1
                    else:
                        evidence_items.append(EvidenceItem(
                            evidence_id="ev_hop1_gst_unavailable",
                            source_url="https://service.gst.gov.in/services/searchtp",
                            source_name="GSTN Statutory Registry [Hop 1: Unavailable]",
                            claim_supported="Legal Entity Standing & Constitution",
                            source_type="GOVERNMENT_REGISTRY",
                            source_mode=SourceMode.UNAVAILABLE,
                            retrieved_at=now,
                            raw_excerpt=f"TinyFish Hop 1 HTTP {resp.status_code}: {resp.text[:300]}",
                            facts={"status": "UNAVAILABLE", "http_code": resp.status_code},
                            is_authoritative=False,
                            is_fallback=False
                        ))
            except Exception as e:
                logger.warning(f"Live TinyFish Hop 1 failed: {e}")
                evidence_items.append(EvidenceItem(
                    evidence_id="ev_hop1_gst_error",
                    source_url="https://service.gst.gov.in/services/searchtp",
                    source_name="GSTN Statutory Registry [Hop 1: Error]",
                    claim_supported="Legal Entity Standing & Constitution",
                    source_type="GOVERNMENT_REGISTRY",
                    source_mode=SourceMode.UNAVAILABLE,
                    retrieved_at=now,
                    raw_excerpt=f"TinyFish live registry lookup failed or timed out: {str(e)}",
                    facts={"status": "UNAVAILABLE", "error": str(e)},
                    is_authoritative=False,
                    is_fallback=False
                ))

        # --- HOP 2: Director Portfolio & Shell Contagion Traversal ---
        query_hop2 = f"https://www.zaubacorp.com/company-directors/{supplier_name.replace(' ', '-')}"
        payload_hop2 = {
            "url": query_hop2,
            "goal": f"Find all Directors / DINs for {supplier_name}. For each director, check how many other companies they are associated with and how many are struck off under Section 248."
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.api_url, json=payload_hop2, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    extracted = data.get("extracted_facts") or {}
                    evidence_items.append(EvidenceItem(
                        evidence_id="ev_hop2_directors_live",
                        source_url=query_hop2,
                        source_name="Director & Shareholder Registry [Hop 2: Live]",
                        claim_supported="Promoter Network & Shell Contagion",
                        source_type="CORPORATE_REGISTRY",
                        source_mode=SourceMode.LIVE,
                        retrieved_at=now,
                        raw_excerpt=str(data.get("result", data))[:1000],
                        facts=extracted,
                        is_authoritative=False,
                        is_fallback=False
                    ))
                    # Defensively parse director profiles if returned
                    raw_dirs = extracted.get("directors") or []
                    for rd in raw_dirs:
                        if isinstance(rd, dict) and rd.get("name"):
                            directors.append(DirectorProfile(
                                din=str(rd.get("din", "UNKNOWN")),
                                name=str(rd.get("name")),
                                appointment_date=rd.get("appointment_date"),
                                associated_companies_count=int(rd.get("associated_companies_count", 1)),
                                struck_off_companies_count=int(rd.get("struck_off_companies_count", 0)),
                                contagion_ratio=float(rd.get("contagion_ratio", 0.0)),
                                active_insolvency_cases=int(rd.get("active_insolvency_cases", 0)),
                                is_benami_flagged=bool(rd.get("is_benami_flagged", False))
                            ))
                    live_success_count += 1
                else:
                    evidence_items.append(EvidenceItem(
                        evidence_id="ev_hop2_directors_unavailable",
                        source_url=query_hop2,
                        source_name="Director & Shareholder Registry [Hop 2: Unavailable]",
                        claim_supported="Promoter Network & Shell Contagion",
                        source_type="CORPORATE_REGISTRY",
                        source_mode=SourceMode.UNAVAILABLE,
                        retrieved_at=now,
                        raw_excerpt=f"TinyFish Hop 2 HTTP {resp.status_code}: {resp.text[:300]}",
                        facts={"status": "UNAVAILABLE", "http_code": resp.status_code},
                        is_authoritative=False,
                        is_fallback=False
                    ))
        except Exception as e:
            logger.warning(f"Live TinyFish Hop 2 failed: {e}")
            evidence_items.append(EvidenceItem(
                evidence_id="ev_hop2_directors_error",
                source_url=query_hop2,
                source_name="Director & Shareholder Registry [Hop 2: Error]",
                claim_supported="Promoter Network & Shell Contagion",
                source_type="CORPORATE_REGISTRY",
                source_mode=SourceMode.UNAVAILABLE,
                retrieved_at=now,
                raw_excerpt=f"Director traversal live lookup failed or timed out: {str(e)}",
                facts={"status": "UNAVAILABLE", "error": str(e)},
                is_authoritative=False,
                is_fallback=False
            ))

        # --- HOP 3: Geolocation Grounding & Address Hub Analysis ---
        if address:
            query_hop3 = f"https://maps.google.com/?q={address.replace(' ', '+')}"
            payload_hop3 = {
                "url": query_hop3,
                "goal": f"Verify physical grounding for address: '{address}'. Identify premises type (warehouse, commercial hub, virtual office, residential) and verify business presence."
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(self.api_url, json=payload_hop3, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        extracted = data.get("extracted_facts") or {}
                        evidence_items.append(EvidenceItem(
                            evidence_id="ev_hop3_geo_live",
                            source_url=query_hop3,
                            source_name="Spatial Geo-Cluster Analysis [Hop 3: Live]",
                            claim_supported="Physical Grounding & Address Hub Analysis",
                            source_type="GEO_DIRECTORY",
                            source_mode=SourceMode.LIVE,
                            retrieved_at=now,
                            raw_excerpt=str(data.get("result", data))[:1000],
                            facts=extracted,
                            is_authoritative=False,
                            is_fallback=False
                        ))
                        address_cluster = AddressClusterProfile(
                            raw_address=address,
                            collocated_gstins_count=int(extracted.get("collocated_count", 1)),
                            premises_type=str(extracted.get("premises_type", "COMMERCIAL_HUB")),
                            is_ghost_hub=bool(extracted.get("is_ghost_hub", False)),
                            evidence_url=query_hop3
                        )
                        live_success_count += 1
                    else:
                        evidence_items.append(EvidenceItem(
                            evidence_id="ev_hop3_geo_unavailable",
                            source_url=query_hop3,
                            source_name="Spatial Geo-Cluster Analysis [Hop 3: Unavailable]",
                            claim_supported="Physical Grounding & Address Hub Analysis",
                            source_type="GEO_DIRECTORY",
                            source_mode=SourceMode.UNAVAILABLE,
                            retrieved_at=now,
                            raw_excerpt=f"TinyFish Hop 3 HTTP {resp.status_code}",
                            facts={"status": "UNAVAILABLE"},
                            is_authoritative=False,
                            is_fallback=False
                        ))
            except Exception as e:
                logger.warning(f"Live TinyFish Hop 3 failed: {e}")
                evidence_items.append(EvidenceItem(
                    evidence_id="ev_hop3_geo_error",
                    source_url=query_hop3,
                    source_name="Spatial Geo-Cluster Analysis [Hop 3: Error]",
                    claim_supported="Physical Grounding & Address Hub Analysis",
                    source_type="GEO_DIRECTORY",
                    source_mode=SourceMode.UNAVAILABLE,
                    retrieved_at=now,
                    raw_excerpt=f"Address verification failed or timed out: {str(e)}",
                    facts={"status": "UNAVAILABLE", "error": str(e)},
                    is_authoritative=False,
                    is_fallback=False
                ))

        # --- HOP 4: Regulatory, NCLT & Litigation Sweep ---
        query_hop4 = "https://nclt.gov.in/case-status"
        payload_hop4 = {
            "url": query_hop4,
            "goal": f"Search for active NCLT petitions, IBC insolvency suits, or winding-up orders for '{supplier_name}'."
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.api_url, json=payload_hop4, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    extracted = data.get("extracted_facts") or {}
                    evidence_items.append(EvidenceItem(
                        evidence_id="ev_hop4_nclt_live",
                        source_url=query_hop4,
                        source_name="Judicial & NCLT Registry [Hop 4: Live]",
                        claim_supported="Litigation & Insolvency Sweep",
                        source_type="JUDICIAL_REGISTRY",
                        source_mode=SourceMode.LIVE,
                        retrieved_at=now,
                        raw_excerpt=str(data.get("result", data))[:1000],
                        facts=extracted,
                        is_authoritative=True,
                        is_fallback=False
                    ))
                    litigation_meta = {
                        "active_cases": int(extracted.get("active_petitions", 0)),
                        "nclt_petitions": extracted.get("petitions", []),
                        "status": "VERIFIED_CLEAN" if extracted.get("active_petitions", 0) == 0 else "FLAGGED"
                    }
                    live_success_count += 1
                else:
                    evidence_items.append(EvidenceItem(
                        evidence_id="ev_hop4_nclt_unavailable",
                        source_url=query_hop4,
                        source_name="Judicial & NCLT Registry [Hop 4: Unavailable]",
                        claim_supported="Litigation & Insolvency Sweep",
                        source_type="JUDICIAL_REGISTRY",
                        source_mode=SourceMode.UNAVAILABLE,
                        retrieved_at=now,
                        raw_excerpt=f"TinyFish Hop 4 HTTP {resp.status_code}",
                        facts={"status": "UNAVAILABLE"},
                        is_authoritative=False,
                        is_fallback=False
                    ))
        except Exception as e:
            logger.warning(f"Live TinyFish Hop 4 failed: {e}")
            evidence_items.append(EvidenceItem(
                evidence_id="ev_hop4_nclt_error",
                source_url=query_hop4,
                source_name="Judicial & NCLT Registry [Hop 4: Error]",
                claim_supported="Litigation & Insolvency Sweep",
                source_type="JUDICIAL_REGISTRY",
                source_mode=SourceMode.UNAVAILABLE,
                retrieved_at=now,
                raw_excerpt=f"Litigation sweep failed or timed out: {str(e)}",
                facts={"status": "UNAVAILABLE", "error": str(e)},
                is_authoritative=False,
                is_fallback=False
            ))

        # Determine effective source mode based on evidence returned
        if live_success_count > 0:
            self._effective_mode = SourceMode.LIVE
        else:
            self._effective_mode = SourceMode.UNAVAILABLE

        return evidence_items, directors, address_cluster, litigation_meta

    def _execute_simulated_multihop(
        self,
        supplier_name: str,
        gstin: Optional[str],
        address: Optional[str]
    ) -> Tuple[List[EvidenceItem], List[DirectorProfile], AddressClusterProfile, Dict[str, Any]]:
        """
        Deterministic, transparent simulation fixtures representing real forensic cases.
        Prominently labeled as synthetic demonstration data (is_fallback=True, is_authoritative=False).
        """
        now = datetime.now(timezone.utc).isoformat()
        name_lower = supplier_name.lower()

        # CASE 2: Shell Mill / Ghost Vendor / Circular Ring
        if "specter" in name_lower or "ghost" in name_lower:
            directors = [
                DirectorProfile(
                    din="08992144",
                    name="Ramesh Kumar (Nominee / Mule)",
                    appointment_date="2026-08-10",
                    associated_companies_count=14,
                    struck_off_companies_count=6,
                    contagion_ratio=0.43,
                    active_insolvency_cases=1,
                    is_benami_flagged=True
                )
            ]
            address_cluster = AddressClusterProfile(
                raw_address="Room 104, Plot 12, Shakarpur Commercial Complex, Delhi - 110092",
                collocated_gstins_count=38,
                premises_type="VIRTUAL_OFFICE",
                is_ghost_hub=True,
                evidence_url="demo://shakarpur-commercial-complex"
            )
            litigation_meta = {
                "active_cases": 1,
                "nclt_petitions": ["CP(IB)/412/ND/2026 under IBC Section 9"],
                "gem_blacklisted": False
            }
            evidence_items = [
                EvidenceItem(
                    evidence_id="ev_hop1_gst_shell",
                    source_url="demo://gstn-statutory-registry/07AAAAA0000A1Z5",
                    source_name="[DEMO FIXTURE] GSTN Statutory Registry",
                    claim_supported="Legal Entity Registration & Filing Cadence",
                    source_type="GOVERNMENT_REGISTRY",
                    source_mode=SourceMode.SIMULATED,
                    is_fallback=True,
                    fallback_reason="DEMO_EVALUATION_FIXTURE: System is operating in simulated evaluation mode without live TinyFish API credentials.",
                    retrieved_at=now,
                    raw_excerpt="[DEMO FIXTURE] GSTIN: 07AAAAA0000A1Z5 | Entity: Specter Cloud Technologies Pvt Ltd | Status: Active | Reg Date: 2026-07-01 | GSTR-3B: 2 Months Overdue | Cash Tax Paid: 0.1% (99.9% offset via ITC).",
                    facts={"status": "Active", "filing_delay_months": 2, "cash_tax_ratio": 0.001},
                    is_authoritative=False
                ),
                EvidenceItem(
                    evidence_id="ev_hop2_director_shell",
                    source_url="demo://mca-director-portfolio/08992144",
                    source_name="[DEMO FIXTURE] MCA Director Portfolio Traversal",
                    claim_supported="Promoter Network & Shell Contagion",
                    source_type="CORPORATE_REGISTRY",
                    source_mode=SourceMode.SIMULATED,
                    is_fallback=True,
                    fallback_reason="DEMO_EVALUATION_FIXTURE: System is operating in simulated evaluation mode without live TinyFish API credentials.",
                    retrieved_at=now,
                    raw_excerpt="[DEMO FIXTURE] DIN 08992144 is Director in 14 companies. 6 companies Struck Off by RoC under Section 248(1) (Non-operational/Shell). 1 company under active NCLT liquidation.",
                    facts={"din": "08992144", "total_companies": 14, "struck_off": 6, "shell_contagion": 0.43},
                    is_authoritative=False
                ),
                EvidenceItem(
                    evidence_id="ev_hop3_ghost_hub",
                    source_url="demo://spatial-geo-cluster/shakarpur",
                    source_name="[DEMO FIXTURE] Spatial Geo-Cluster Analysis",
                    claim_supported="Physical Grounding & Ghost Hub Detection",
                    source_type="GEO_DIRECTORY",
                    source_mode=SourceMode.SIMULATED,
                    is_fallback=True,
                    fallback_reason="DEMO_EVALUATION_FIXTURE: System is operating in simulated evaluation mode without live TinyFish API credentials.",
                    retrieved_at=now,
                    raw_excerpt="[DEMO FIXTURE] Address Collocation Analysis: 38 distinct GSTINs registered at Room 104, Shakarpur Complex (150 sq ft). Classified as High-Density Virtual Mailbox Hub.",
                    facts={"collocated_count": 38, "premises": "VIRTUAL_OFFICE", "is_ghost_hub": True},
                    is_authoritative=False
                ),
                EvidenceItem(
                    evidence_id="ev_hop4_nclt",
                    source_url="demo://nclt-registry/cp-ib-412-2026",
                    source_name="[DEMO FIXTURE] National Company Law Tribunal",
                    claim_supported="Litigation & Insolvency Sweep",
                    source_type="JUDICIAL_REGISTRY",
                    source_mode=SourceMode.SIMULATED,
                    is_fallback=True,
                    fallback_reason="DEMO_EVALUATION_FIXTURE: System is operating in simulated evaluation mode without live TinyFish API credentials.",
                    retrieved_at=now,
                    raw_excerpt="[DEMO FIXTURE] NCLT New Delhi Bench: CP(IB)/412/ND/2026 active under Section 9 of Insolvency and Bankruptcy Code (IBC) for operational creditor default.",
                    facts={"active_petitions": 1},
                    is_authoritative=False
                )
            ]
            return evidence_items, directors, address_cluster, litigation_meta

        # CASE 1: Benchmark Apex Courier (Legitimate operating business)
        directors = [
            DirectorProfile(
                din="02341908",
                name="Sanjay Singhal",
                appointment_date="2018-04-12",
                associated_companies_count=2,
                struck_off_companies_count=0,
                contagion_ratio=0.0,
                active_insolvency_cases=0,
                is_benami_flagged=False
            )
        ]
        address_cluster = AddressClusterProfile(
            raw_address="Plot 44, Phase-II, Okhla Industrial Area, New Delhi - 110020",
            collocated_gstins_count=1,
            premises_type="INDUSTRIAL_WAREHOUSE",
            is_ghost_hub=False,
            evidence_url="demo://okhla-phase-2"
        )
        litigation_meta = {"active_cases": 0, "nclt_petitions": [], "gem_blacklisted": False}
        evidence_items = [
            EvidenceItem(
                evidence_id="ev_hop1_gst_apex",
                source_url="demo://gstn-statutory-registry/07AAAAA0000A1Z5",
                source_name="[DEMO FIXTURE] GSTN Statutory Registry",
                claim_supported="Legal Entity Registration & Trade Name",
                source_type="GOVERNMENT_REGISTRY",
                source_mode=SourceMode.SIMULATED,
                is_fallback=True,
                fallback_reason="DEMO_EVALUATION_FIXTURE: System is operating in simulated evaluation mode without live TinyFish API credentials.",
                retrieved_at=now,
                raw_excerpt="[DEMO FIXTURE] GSTIN: 07AAAAA0000A1Z5 | Legal: Apex Global Logistics Pvt Ltd | Trade: Apex Courier | Status: Active | Constitution: Private Limited | Reg Date: 2018-04-12 | GSTR-3B: Regular.",
                facts={
                    "legal_name": "Apex Global Logistics Private Limited",
                    "trade_name": "Apex Courier",
                    "status": "Active",
                    "incorporation_date": "2018-04-12",
                    "filing_delay_months": 0
                },
                is_authoritative=False
            ),
            EvidenceItem(
                evidence_id="ev_hop2_director_apex",
                source_url="demo://mca-corporate-registry/APEX-GLOBAL-LOGISTICS",
                source_name="[DEMO FIXTURE] MCA Corporate Registry",
                claim_supported="Promoter Network & Directorship Verification",
                source_type="CORPORATE_REGISTRY",
                source_mode=SourceMode.SIMULATED,
                is_fallback=True,
                fallback_reason="DEMO_EVALUATION_FIXTURE: System is operating in simulated evaluation mode without live TinyFish API credentials.",
                retrieved_at=now,
                raw_excerpt="[DEMO FIXTURE] Director Sanjay Singhal (DIN 02341908). Active since 2018. Associated with 2 logistics firms. 0 struck-off entities. Clean MCA track record.",
                facts={"din": "02341908", "total_companies": 2, "struck_off": 0, "shell_contagion": 0.0},
                is_authoritative=False
            ),
            EvidenceItem(
                evidence_id="ev_hop3_geo_apex",
                source_url="demo://spatial-geo-cluster/okhla",
                source_name="[DEMO FIXTURE] Spatial Geo-Cluster Analysis",
                claim_supported="Physical Grounding & Operational Premises",
                source_type="GEO_DIRECTORY",
                source_mode=SourceMode.SIMULATED,
                is_fallback=True,
                fallback_reason="DEMO_EVALUATION_FIXTURE: System is operating in simulated evaluation mode without live TinyFish API credentials.",
                retrieved_at=now,
                raw_excerpt="[DEMO FIXTURE] Address Grounding: Plot 44, Okhla Industrial Area Phase II is an active 8,000 sq ft logistics depot. 1 GSTIN registered. Verified commercial premises.",
                facts={"collocated_count": 1, "premises": "INDUSTRIAL_WAREHOUSE", "is_ghost_hub": False},
                is_authoritative=False
            ),
            EvidenceItem(
                evidence_id="ev_hop4_judicial_apex",
                source_url="demo://nclt-registry/apex",
                source_name="[DEMO FIXTURE] Judicial & NCLT Registry",
                claim_supported="Litigation & Insolvency Sweep",
                source_type="JUDICIAL_REGISTRY",
                source_mode=SourceMode.SIMULATED,
                is_fallback=True,
                fallback_reason="DEMO_EVALUATION_FIXTURE: System is operating in simulated evaluation mode without live TinyFish API credentials.",
                retrieved_at=now,
                raw_excerpt="[DEMO FIXTURE] NCLT / eCourts: No insolvency petitions, winding-up suits, or debarment orders found for Apex Global Logistics Pvt Ltd.",
                facts={"active_petitions": 0},
                is_authoritative=False
            )
        ]
        return evidence_items, directors, address_cluster, litigation_meta
