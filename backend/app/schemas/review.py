from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .enums import ReviewActionType

class ReviewAction(BaseModel):
    action_id: str
    case_id: str
    reviewer_id: str
    action: ReviewActionType
    rationale: str
    requested_documents: List[str] = Field(default_factory=list)
    recorded_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
