from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from .enums import CheckStatus, SourceMode

class EvidenceItem(BaseModel):
    evidence_id: str
    source_url: str
    source_name: str
    claim_supported: str
    source_type: str = "PUBLIC_WEB"
    source_mode: SourceMode = SourceMode.SIMULATED
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_excerpt: str
    facts: Dict[str, Any] = Field(default_factory=dict)
    is_authoritative: bool = False
    match_rationale: Optional[str] = None
    streaming_url: Optional[str] = None
    run_id: Optional[str] = None
    hop_number: Optional[int] = None
    hop_title: Optional[str] = None

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
    source_mode: SourceMode = SourceMode.SIMULATED
    is_fallback: bool = False
