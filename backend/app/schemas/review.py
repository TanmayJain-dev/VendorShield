import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from .enums import ReviewActionType

class ReviewSubmissionRequest(BaseModel):
    """
    Client submission payload for human review actions.
    Separates client-provided review intent from server-owned identifiers.
    In authenticated mode, caller-supplied reviewer_id/reviewer_role are ignored
    in favor of the server-authenticated token identity.
    In dev mode, any self-reported reviewer_id is explicitly prefixed with 'dev_unauthenticated:'.
    """
    action: ReviewActionType
    rationale: str
    reviewer_id: Optional[str] = None
    reviewer_role: Optional[str] = None
    requested_documents: List[str] = Field(default_factory=list)

class ReviewAction(BaseModel):
    """
    Server-persisted record of an executed human review action.
    Server generates action_id, timestamp, and audit metadata.
    """
    action_id: str
    case_id: str
    reviewer_id: str
    reviewer_role: str = "ap_analyst"
    action: ReviewActionType
    rationale: str
    requested_documents: List[str] = Field(default_factory=list)
    auth_mode: str = "DEV_MODE_UNAUTHENTICATED"
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
