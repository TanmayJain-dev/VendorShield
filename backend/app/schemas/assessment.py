from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .enums import RecommendationOutcome
from .evidence import FieldCheckResult
from .forensic_graph import ForensicVectorScores, ITCExposureDetails, EntityGraph

class RuleTrigger(BaseModel):
    rule_id: str
    condition: str
    weight: int = 0
    is_hard_gate: bool = False
    description: str

class RiskAssessment(BaseModel):
    assessment_id: str
    case_id: str
    ruleset_version: str = "2.0.0"
    recommendation: RecommendationOutcome
    risk_score: Optional[int] = None  # 0 to 100 overall composite safety score
    reason_codes: List[str] = Field(default_factory=list)
    field_checks: List[FieldCheckResult] = Field(default_factory=list)
    hard_gates_triggered: List[str] = Field(default_factory=list)
    
    # --- VendorShield 2.0 Forensic Intelligence Layer ---
    forensic_vectors: Optional[ForensicVectorScores] = None
    itc_exposure: Optional[ITCExposureDetails] = None
    entity_graph: Optional[EntityGraph] = None

    evidence_completeness: str = "COMPLETE"  # COMPLETE, PARTIAL, INSUFFICIENT
    human_signoff_required: bool = True
    assessed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

