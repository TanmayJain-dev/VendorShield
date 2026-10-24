from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from .cases import case_store
from ..services.audit.trail import AuditTrailService

router = APIRouter(prefix="/cases", tags=["reports"])
audit_service = AuditTrailService()

@router.get("/{case_id}/report", response_class=PlainTextResponse)
async def export_audit_report(case_id: str):
    """
    Exports full evidence trail and reviewer sign-off report as Markdown.
    """
    if case_id not in case_store:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = case_store[case_id]
    report_md = audit_service.generate_markdown_report(case)
    return report_md
