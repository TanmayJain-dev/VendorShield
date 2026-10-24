from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from .enums import RecommendationOutcome, SourceMode
from .evidence import FieldCheckResult

class RuleTrigger(BaseModel):
    rule_id: str
    rule_name: str
    severity: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    weight: int = 0
    is_hard_gate: bool = False
    description: str
    reason_code: str
    evidence_reference: Optional[str] = None
    missing_evidence: Optional[str] = None

class RiskAssessment(BaseModel):
    assessment_id: str
    case_id: str
    ruleset_version: str = "1.0.0"
    recommendation: RecommendationOutcome
    risk_score: Optional[int] = None  # Deterministic Policy Risk Index (0-100)
    score_explanation: str = "Deterministic policy compliance index based on explicit rule penalties; not a statistical fraud probability."
    reason_codes: List[str] = Field(default_factory=list)
    field_checks: List[FieldCheckResult] = Field(default_factory=list)
    hard_gates_triggered: List[str] = Field(default_factory=list)
    triggered_rules: List[RuleTrigger] = Field(default_factory=list)
    missing_evidence_items: List[str] = Field(default_factory=list)
    evidence_completeness: str = "COMPLETE"  # COMPLETE, PARTIAL, INSUFFICIENT, SIMULATED_ONLY
    evidence_provenance_mode: SourceMode = SourceMode.SIMULATED
    human_signoff_required: bool = True
    assessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
