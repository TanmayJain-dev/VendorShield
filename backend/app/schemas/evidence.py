from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from .enums import CheckStatus

class EvidenceItem(BaseModel):
    evidence_id: str
    source_url: str
    source_name: str
    claim_supported: str
    source_type: str = "PUBLIC_WEB"
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    raw_excerpt: str
    facts: Dict[str, Any] = Field(default_factory=dict)
    is_authoritative: bool = False

class FieldCheckResult(BaseModel):
    check_id: str
    field_name: str
    invoice_value: Optional[str] = None
    evidence_value: Optional[str] = None
    status: CheckStatus
    reason_code: Optional[str] = None
    explanation: str
    evidence_id: Optional[str] = None
    source_url: Optional[str] = None
