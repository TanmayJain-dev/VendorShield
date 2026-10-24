from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .enums import CaseStatus, SourceMode, RecommendationOutcome
from .invoice import InvoiceClaim
from .evidence import EvidenceItem
from .assessment import RiskAssessment
from .review import ReviewAction

class CaseSummary(BaseModel):
    case_id: str
    case_reference: str
    status: CaseStatus
    supplier_name: str
    invoice_number: str
    total_amount: float
    recommendation: Optional[RecommendationOutcome] = None
    created_at: str

class Case(BaseModel):
    case_id: str
    case_reference: str
    status: CaseStatus = CaseStatus.SUBMITTED
    source_mode: SourceMode = SourceMode.SIMULATED
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    created_by: str = "ap_analyst"
    
    # Payload elements
    invoice: Optional[InvoiceClaim] = None
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    assessment: Optional[RiskAssessment] = None
    review: Optional[ReviewAction] = None
    
    # Audit integrity
    audit_hash_sha256: Optional[str] = None
