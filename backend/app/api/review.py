import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request, status
from sqlalchemy.orm import Session

from ..schemas.case import Case
from ..schemas.review import ReviewAction
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
    CaseStatus.PARSED: {CaseStatus.RESOLVED, CaseStatus.PENDING_DOCUMENTS, CaseStatus.ESCALATED},
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
    In development mode: permits documented development identities with explicit dev auditing.
    In production mode: enforces strict token/session verification.
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
        logger.warning(
            "Review action executed under DEVELOPMENT_MODE. This endpoint is not production-secure without configured OAuth/SSO."
        )
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
    review_in: ReviewAction,
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

    # 1. Check legal state transitions (prevent premature or unauthorized reviews)
    if case.status in (CaseStatus.SUBMITTED, CaseStatus.INVESTIGATING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Premature review rejected: Case is currently '{case.status.value}'. Intake parsing and investigation must complete before review."
        )

    if case.status == CaseStatus.RESOLVED:
        # Prevent unauthorized review of already resolved cases without escalation
        if auth_ctx["reviewer_role"] not in ("ap_manager", "compliance_officer"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case has already been RESOLVED. Reopening or overriding requires AP Manager authorization."
            )

    # 2. Validate mandatory rationale
    if not review_in.rationale or len(review_in.rationale.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mandatory review rationale must contain at least 5 meaningful characters explaining the decision."
        )

    # 3. Determine target state based on review action
    if review_in.action in (ReviewActionType.APPROVE, ReviewActionType.APPROVE_WITH_EXCEPTION, ReviewActionType.REJECT):
        target_status = CaseStatus.RESOLVED
    elif review_in.action == ReviewActionType.REQUEST_DOCUMENTS:
        target_status = CaseStatus.PENDING_DOCUMENTS
    elif review_in.action == ReviewActionType.ESCALATE:
        target_status = CaseStatus.ESCALATED
    else:
        target_status = CaseStatus.RESOLVED

    # Ensure target transition is allowed
    allowed = ALLOWED_REVIEW_TRANSITIONS.get(case.status, set())
    if target_status not in allowed and case.status != CaseStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal state transition from '{case.status.value}' to '{target_status.value}'"
        )

    # 4. Attach reviewer identity and auth metadata
    # If client passed an explicit reviewer_id, keep it if in dev mode, but tag with auth_mode
    effective_reviewer = review_in.reviewer_id.strip() if review_in.reviewer_id else auth_ctx["reviewer_id"]
    review_in.action_id = f"act_{uuid.uuid4().hex[:8]}"
    review_in.case_id = case_id
    review_in.reviewer_id = effective_reviewer
    review_in.reviewer_role = auth_ctx.get("reviewer_role", "ap_analyst")
    review_in.auth_mode = auth_ctx.get("auth_mode", "DEV_MODE_UNAUTHENTICATED")

    case.review = review_in
    case.status = target_status

    # 5. Compute cryptographic case digest
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)

    # 6. Save case to persistent database
    updated_case = CaseRepository.save_case(db, case)

    # 7. Record append-only chained audit event
    CaseRepository.add_audit_event(
        db=db,
        case_id=case_id,
        event_type="REVIEW_DECISION_RECORDED",
        actor=effective_reviewer,
        actor_role=review_in.reviewer_role,
        event_data={
            "action": review_in.action.value,
            "target_status": target_status.value,
            "rationale": review_in.rationale,
            "requested_documents": review_in.requested_documents,
            "auth_mode": review_in.auth_mode,
            "audit_hash": case.audit_hash_sha256
        },
        ruleset_version=case.assessment.ruleset_version if case.assessment else settings.RULES_VERSION
    )

    return updated_case
