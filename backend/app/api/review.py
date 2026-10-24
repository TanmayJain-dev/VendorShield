import uuid
from fastapi import APIRouter, HTTPException
from ..schemas.case import Case
from ..schemas.review import ReviewAction
from ..schemas.enums import CaseStatus
from .cases import case_store
from ..services.audit.trail import AuditTrailService

router = APIRouter(prefix="/cases", tags=["review"])
audit_service = AuditTrailService()

@router.post("/{case_id}/review", response_model=Case)
async def submit_review_decision(case_id: str, review_in: ReviewAction):
    """
    Records an authorized human reviewer's final decision with mandatory rationale.
    Human-in-the-loop: Vendors are never automatically approved without human sign-off.
    """
    if case_id not in case_store:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = case_store[case_id]
    if not review_in.rationale or len(review_in.rationale.strip()) < 5:
        raise HTTPException(status_code=422, detail="Mandatory review rationale must be at least 5 characters")

    # Record action
    review_in.action_id = f"act_{uuid.uuid4().hex[:8]}"
    review_in.case_id = case_id
    case.review = review_in
    case.status = CaseStatus.RESOLVED

    # Finalize cryptographic audit hash
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)
    
    return case
