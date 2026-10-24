from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.repository import CaseRepository
from ..services.audit.trail import AuditTrailService

router = APIRouter(prefix="/cases", tags=["reports"])
audit_service = AuditTrailService()

@router.get("/{case_id}/report", response_class=PlainTextResponse)
async def export_audit_report(case_id: str, db: Session = Depends(get_db)):
    """
    Exports full evidence trail, chained audit events, and reviewer sign-off report as Markdown.
    """
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    audit_events = CaseRepository.get_audit_trail(db, case_id)
    report_md = audit_service.generate_markdown_report(case, audit_events=audit_events)
    return report_md

@router.get("/{case_id}/audit-trail")
async def get_audit_trail(case_id: str, db: Session = Depends(get_db)):
    """
    Returns the structured tamper-evident chained audit trail for the case.
    """
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return CaseRepository.get_audit_trail(db, case_id)
