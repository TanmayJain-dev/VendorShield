from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from .enums import CaseStatus, SourceMode, RecommendationOutcome
from .invoice import InvoiceClaim
from .evidence import EvidenceItem
from .assessment import RiskAssessment
from .review import ReviewAction

class CaseSummary(BaseModel):
    case_id: str
    case_reference: str
    status: CaseStatus
    source_mode: SourceMode = SourceMode.SIMULATED
    supplier_name: str
    invoice_number: str
    total_amount: float
    recommendation: Optional[RecommendationOutcome] = None
    risk_score: Optional[int] = None
    duplicate_type: Optional[str] = None
    is_demo: bool = False
    created_at: str

class Case(BaseModel):
    case_id: str
    case_reference: str
    status: CaseStatus = CaseStatus.SUBMITTED
    source_mode: SourceMode = SourceMode.SIMULATED
    is_demo: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = "ap_analyst"
    file_sha256: Optional[str] = None
    duplicate_of_case_id: Optional[str] = None
    duplicate_type: Optional[str] = None
    
    # Payload elements
    invoice: Optional[InvoiceClaim] = None
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    assessment: Optional[RiskAssessment] = None
    review: Optional[ReviewAction] = None
    review_history: List[ReviewAction] = Field(default_factory=list)
    
    # Audit integrity
    audit_hash_sha256: Optional[str] = None
