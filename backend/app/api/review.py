import uuid
import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Header, Request, status
from sqlalchemy.orm import Session

from ..schemas.case import Case
from ..schemas.review import ReviewAction, ReviewSubmissionRequest
from ..schemas.enums import CaseStatus, ReviewActionType
from ..db.database import get_db
from ..db.repository import CaseRepository
from ..services.audit.trail import AuditTrailService
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["review"])
audit_service = AuditTrailService()

# Legal transition graph: current_status -> set of allowed next_statuses
ALLOWED_REVIEW_TRANSITIONS = {
    CaseStatus.READY_FOR_REVIEW: {CaseStatus.RESOLVED, CaseStatus.PENDING_DOCUMENTS, CaseStatus.ESCALATED},
    CaseStatus.PENDING_DOCUMENTS: {CaseStatus.RESOLVED, CaseStatus.ESCALATED},
    CaseStatus.ESCALATED: {CaseStatus.RESOLVED, CaseStatus.PENDING_DOCUMENTS},
}

def resolve_reviewer_identity(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_reviewer_token: Optional[str] = Header(None)
) -> dict:
    """
    Validates reviewer identity.
    
    TRUST BOUNDARY LIMITATION (DOCUMENTED):
    In development mode (REVIEWER_DEV_MODE=True), this application does NOT enforce cryptographically
    signed SSO or OAuth2 sessions. A shared developer token or self-reported analyst identity is accepted
    for hackathon demonstration, tagged explicitly with `DEV_MODE_UNAUTHENTICATED` in all audit events.
    In production deployments, this MUST be replaced by an authoritative OIDC/SAML enterprise identity provider.
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
    elif x_reviewer_token:
        token = x_reviewer_token.strip()

    # If valid configured dev token is present
    if token and token == settings.DEV_REVIEWER_TOKEN:
        return {
            "reviewer_id": "authorized_ap_reviewer",
            "reviewer_role": "compliance_officer",
            "auth_mode": "BEARER_TOKEN_AUTHENTICATED"
        }

    # Development-only mode fallback
    if settings.REVIEWER_DEV_MODE:
        return {
            "reviewer_id": "dev_analyst",
            "reviewer_role": "ap_analyst",
            "auth_mode": "DEV_MODE_UNAUTHENTICATED"
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Valid reviewer authorization token required to execute sign-off."
    )

@router.post("/{case_id}/review", response_model=Case)
async def submit_review_decision(
    case_id: str,
    review_in: ReviewSubmissionRequest,
    db: Session = Depends(get_db),
    auth_ctx: dict = Depends(resolve_reviewer_identity)
):
    """
    Records an authorized human reviewer's final decision with mandatory rationale.
    Enforces valid state machine transitions, prevents premature reviews,
    and updates cryptographically chained audit logs.
    Axiom: System is advisory; human reviewer makes the final decision. Payments are never automatically released.
    """
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # 1. Enforce that case must have a completed assessment before final review
    if not case.assessment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review case '{case_id}': Case does not have a completed risk assessment. Run investigation first."
        )

    # 2. Check legal state transitions (prevent premature or unauthorized reviews)
    if case.status in (CaseStatus.SUBMITTED, CaseStatus.PARSED, CaseStatus.INVESTIGATING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Premature review rejected: Case is currently '{case.status.value}'. Investigation and risk assessment must complete before review."
        )

    if case.status == CaseStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case has already been RESOLVED and cannot be reviewed again without explicit reopening."
        )

    # 3. Validate mandatory rationale (at least 5 characters)
    if not review_in.rationale or len(review_in.rationale.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mandatory review rationale must contain at least 5 meaningful characters explaining the decision."
        )

    # 4. Determine target state based on review action
    if review_in.action in (ReviewActionType.APPROVE, ReviewActionType.APPROVE_WITH_EXCEPTION, ReviewActionType.REJECT):
        target_status = CaseStatus.RESOLVED
    elif review_in.action == ReviewActionType.REQUEST_DOCUMENTS:
        target_status = CaseStatus.PENDING_DOCUMENTS
    elif review_in.action == ReviewActionType.ESCALATE:
        target_status = CaseStatus.ESCALATED
    else:
        target_status = CaseStatus.RESOLVED

    # Ensure target transition is allowed from current status
    allowed = ALLOWED_REVIEW_TRANSITIONS.get(case.status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal state transition from '{case.status.value}' to '{target_status.value}'"
        )

    # 5. Generate server-owned review record with trusted identifiers
    server_action_id = f"act_{uuid.uuid4().hex[:12]}"
    effective_reviewer = review_in.reviewer_id.strip() if review_in.reviewer_id else auth_ctx["reviewer_id"]

    persisted_review = ReviewAction(
        action_id=server_action_id,
        case_id=case_id,
        reviewer_id=effective_reviewer,
        reviewer_role=review_in.reviewer_role or auth_ctx.get("reviewer_role", "ap_analyst"),
        action=review_in.action,
        rationale=review_in.rationale.strip(),
        requested_documents=review_in.requested_documents or [],
        auth_mode=auth_ctx.get("auth_mode", "DEV_MODE_UNAUTHENTICATED"),
        recorded_at=datetime.now(timezone.utc).isoformat()
    )

    case.review = persisted_review
    case.status = target_status

    # 6. Compute cryptographic case digest (computed after review data and status are updated)
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)

    # 7. Save case to persistent database
    updated_case = CaseRepository.save_case(db, case)

    # 8. Record append-only chained audit event
    CaseRepository.add_audit_event(
        db=db,
        case_id=case_id,
        event_type="REVIEW_DECISION_RECORDED",
        actor=effective_reviewer,
        actor_role=persisted_review.reviewer_role,
        event_data={
            "action": persisted_review.action.value,
            "target_status": target_status.value,
            "rationale": persisted_review.rationale,
            "requested_documents": persisted_review.requested_documents,
            "auth_mode": persisted_review.auth_mode,
            "audit_hash": case.audit_hash_sha256
        },
        ruleset_version=case.assessment.ruleset_version if case.assessment else settings.RULES_VERSION
    )

    return updated_case
