from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ForensicVectorScores(BaseModel):
    """The 5-Vector Forensic Risk Topology (0.0 low risk to 1.0 critical risk)."""
    itc_clawback_risk_index: float = Field(..., ge=0.0, le=1.0, description="Risk of statutory ITC reversal under CGST Sec 16(2)(c)")
    director_shell_contagion_score: float = Field(..., ge=0.0, le=1.0, description="Ratio of struck-off/defaulted sister entities in promoter network")
    address_collocation_density: int = Field(..., ge=0, description="Count of independent businesses registered at the identical micro-address")
    operational_grounding_score: float = Field(..., ge=0.0, le=1.0, description="Congruity between physical premises type and invoice scale/goods")
    popup_velocity_factor: float = Field(..., ge=0.0, le=1.0, description="Risk indicator for high-value turnover on newly incorporated entities")

class ITCExposureDetails(BaseModel):
    """Direct rupee-denominated financial risk under Indian Goods and Services Tax law."""
    tax_amount_claimed: float = Field(..., description="GST component (CGST + SGST + IGST) on invoice in INR")
    itc_clawback_probability: float = Field(..., ge=0.0, le=1.0)
    statutory_penalty_inr: float = Field(..., description="100% penalty under CGST Section 74 / Section 122")
    estimated_interest_inr: float = Field(..., description="Estimated statutory interest at 18-24% per annum")
    total_financial_liability_inr: float = Field(..., description="Total exposure if tax authority rejects supplier ITC")
    applicable_sections: List[str] = Field(default_factory=list)
    risk_tier: str = Field(..., description="CRITICAL, HIGH, MODERATE, or LOW")
    cfo_advisory: str = Field(..., description="Direct operational instruction for AP and Treasury team")

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
