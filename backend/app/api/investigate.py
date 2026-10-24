from fastapi import APIRouter, HTTPException
from ..schemas.case import Case
from ..schemas.enums import CaseStatus
from .cases import case_store
from ..services.tinyfish.client import TinyFishService
from ..services.reconciler.evidence_reconciler import EvidenceReconciler
from ..services.rules.engine import DeterministicRuleEngine
from ..services.audit.trail import AuditTrailService

router = APIRouter(prefix="/cases", tags=["investigation"])

tinyfish_service = TinyFishService()
reconciler = EvidenceReconciler()
rule_engine = DeterministicRuleEngine()
audit_service = AuditTrailService()

@router.post("/{case_id}/investigate", response_model=Case)
async def run_investigation(case_id: str):
    """
    Triggers bounded public-web investigation via TinyFish,
    reconciles evidence, and evaluates deterministic rules.
    """
    if case_id not in case_store:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = case_store[case_id]
    if not case.invoice:
        raise HTTPException(status_code=400, detail="Invoice claims missing")

    case.status = CaseStatus.INVESTIGATING

    # 1. Gather public-web evidence via TinyFish
    evidence_items = await tinyfish_service.investigate_vendor(
        supplier_name=case.invoice.supplier_name,
        gstin=case.invoice.gstin
    )
    case.evidence_items = evidence_items
    case.source_mode = tinyfish_service.source_mode

    # 2. Reconcile evidence against invoice claims
    field_checks = reconciler.reconcile(case.invoice, evidence_items)

    # 3. Apply deterministic rules & calculate assessment
    assessment = rule_engine.evaluate(case_id, case.invoice, field_checks)
    case.assessment = assessment

    # 4. Update status and compute provisional integrity hash
    case.status = CaseStatus.READY_FOR_REVIEW
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)

    return case
