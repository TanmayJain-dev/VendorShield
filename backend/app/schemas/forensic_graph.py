from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ForensicVectorScores(BaseModel):
    """The 5-Vector Forensic Risk Topology (0.0 low risk to 1.0 critical risk)."""
    itc_clawback_risk_index: float = Field(..., ge=0.0, le=1.0, description="Risk of statutory ITC reversal under CGST Sec 16(2)(c)")
    director_shell_contagion_score: float = Field(..., ge=0.0, le=1.0, description="Ratio of struck-off/defaulted sister entities in promoter network")
    address_collocation_density: int = Field(..., ge=0, description="Count of independent businesses registered at the identical micro-address")
    operational_grounding_score: float = Field(..., ge=0.0, le=1.0, description="Congruity between physical premises type and invoice scale/goods")
    popup_velocity_factor: float = Field(..., ge=0.0, le=1.0, description="Risk indicator for high-value turnover on newly incorporated entities")
    # Extended 4-Hop Forensic Signals
    judicial_insolvency_contagion: Optional[float] = Field(default=None, description="Hop 2: Indian Kanoon NCLT/IBC/GST docket contagion (0.0-1.0)")
    procurement_price_anomaly: Optional[float] = Field(default=None, description="Hop 4: IndiaMART wholesale price inflation variance (0.0-1.0)")
    popup_velocity_and_bank_mutation: Optional[float] = Field(default=None, description="Combined velocity and bank account mutation index (0.0-1.0)")

class TreasurySettlementDetails(BaseModel):
    """
    Dynamic Treasury Split-Settlement Recommendation & GSTN IMS Portal Action.
    Resolves the statutory conflict between Income Tax Sec 43B(h) MSME 45-day payment
    and CGST Sec 16(2)(c) Input Tax Credit clawback protection.
    """
    recommendation: str = Field(..., description="FULL_DISBURSAL, STATUTORY_GST_ESCROW, or FORENSIC_FREEZE")
    release_now_inr: float = Field(..., description="Liquid payout released immediately to vendor")
    escrow_hold_gst_inr: float = Field(..., description="GST component retained in automated tax escrow until GSTR-3B is verified")
    statutory_clawback_risk_avoided_inr: float = Field(..., description="Total statutory clawback risk avoided (Tax + 100% Penalty + 18% Interest)")
    msme_43b_compliant: bool = Field(True, description="True if base amount is disbursed within statutory MSME window")
    gstn_ims_action: str = Field(..., description="Recommended GSTN IMS action: ACCEPT, PENDING_HOLD, or REJECT")
    settlement_rationale: str = Field(..., description="Legal and treasury audit rationale")
    ims_action_payload: Dict[str, Any] = Field(default_factory=dict, description="Structured payload for 1-click GSTN IMS JSON export")

class ProcurementPriceBenchmark(BaseModel):
    """Hop 4: IndiaMART Wholesale Market Benchmark Result."""
    item_description: str
    billed_unit_price: float
    market_median_price_inr: float = 0.0
    market_min_price_inr: float = 0.0
    market_max_price_inr: float = 0.0
    sample_listings_count: int = 0
    price_inflation_pct: float = 0.0
    is_anomaly: bool = False
    source_url: str = ""

class JudicialDocketSummary(BaseModel):
    """Hop 2: Indian Kanoon NCLT & GST Litigation Radar."""
    adverse_docket_count: int = 0
    top_case_title: Optional[str] = None
    insolvency_or_tax_fraud_flag: bool = False
    forensic_summary: str = ""
    source_url: str = ""

class EnforcementRadarSummary(BaseModel):
    """Hop 3: DGGI Enforcement & Debarment Radar."""
    enforcement_hit: bool = False
    agency_named: str = "None"
    allegation_summary: str = "Clean regulatory record"
    risk_severity: str = "LOW"
    source_url: str = ""

class ITCExposureDetails(BaseModel):
    """
    Illustrative decision-support exposure calculation under Indian GST law (CGST Act Sections 16(2)(c), 74, 50).
    Not a formal statutory tax assessment or legal liability notice.
    """
    tax_amount_claimed: float = Field(..., description="GST component (CGST + SGST + IGST) claimed on invoice in INR")
    itc_clawback_probability: float = Field(..., ge=0.0, le=1.0, description="Uncalibrated heuristic probability index for ITC disallowance")
    statutory_penalty_inr: float = Field(..., description="Illustrative 100% penalty projection under CGST Section 74 if disputed for willful misstatement")
    estimated_interest_inr: float = Field(..., description="Illustrative statutory delayed tax interest estimate at 18% p.a. under CGST Section 50")
    total_financial_liability_inr: float = Field(..., description="Estimated potential exposure (claimed GST + illustrative penalty/interest) under CGST Sec 16(2)(c) & Sec 74")
    applicable_sections: List[str] = Field(default_factory=list)
    risk_tier: str = Field(..., description="CRITICAL, HIGH, MODERATE, or LOW")
    cfo_advisory: str = Field(..., description="Decision-support advisory for AP and Treasury team")

class DirectorProfile(BaseModel):
    din: str
    name: str
    appointment_date: Optional[str] = None
    associated_companies_count: int = 1
    struck_off_companies_count: int = 0
    contagion_ratio: float = 0.0
    active_insolvency_cases: int = 0
    is_benami_flagged: bool = False

class AddressClusterProfile(BaseModel):
    raw_address: str
    collocated_gstins_count: int = 1
    premises_type: str = "COMMERCIAL_HUB"  # RESIDENTIAL, VIRTUAL_OFFICE, COMMERCIAL_HUB, INDUSTRIAL_WAREHOUSE, UNKNOWN
    is_ghost_hub: bool = False
    evidence_url: Optional[str] = None

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # VENDOR, DIRECTOR, SISTER_COMPANY, ADDRESS, LITIGATION
    risk_level: str  # NORMAL, WARNING, CRITICAL
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str  # DIRECTED_BY, REGISTERED_AT, SISTER_OF, SUED_IN
    is_flagged: bool = False
    weight: float = 1.0

class EntityGraph(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_flagged_edges: int = 0
