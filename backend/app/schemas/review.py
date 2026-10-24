import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from .enums import ReviewActionType

class ReviewAction(BaseModel):
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}")
    case_id: Optional[str] = None
    reviewer_id: str
    reviewer_role: str = "ap_analyst"
    action: ReviewActionType
    rationale: str
    requested_documents: List[str] = Field(default_factory=list)
    auth_mode: str = "DEV_MODE_UNAUTHENTICATED"
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
