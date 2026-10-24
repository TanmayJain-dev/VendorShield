from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..schemas.case import Case
from ..schemas.enums import CaseStatus
from ..db.database import get_db
from ..db.repository import CaseRepository
from ..services.tinyfish.client import TinyFishService
from ..services.reconciler.evidence_reconciler import EvidenceReconciler
from ..services.rules.engine import DeterministicRuleEngine
from ..services.audit.trail import AuditTrailService
from ..config import settings

router = APIRouter(prefix="/cases", tags=["investigation"])

tinyfish_service = TinyFishService()
reconciler = EvidenceReconciler()
rule_engine = DeterministicRuleEngine()
audit_service = AuditTrailService()

@router.post("/{case_id}/investigate", response_model=Case)
async def run_investigation(case_id: str, db: Session = Depends(get_db)):
    """
    Triggers bounded public-web investigation via TinyFish,
    reconciles evidence, evaluates deterministic rules,
    and updates persistent database and audit trail.
    """
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if not case.invoice:
        raise HTTPException(status_code=400, detail="Invoice claims missing")

    case.status = CaseStatus.INVESTIGATING

    # 1. Gather public-web evidence via TinyFish
    evidence_items = await tinyfish_service.investigate_vendor(
        supplier_name=case.invoice.supplier_name,
        gstin=case.invoice.gstin
    )
    case.evidence_items = evidence_items
    case.source_mode = tinyfish_service.last_effective_mode

    # 2. Reconcile evidence against invoice claims
    field_checks = reconciler.reconcile(case.invoice, evidence_items)

    # 3. Apply deterministic rules & calculate assessment
    assessment = rule_engine.evaluate(case_id, case.invoice, field_checks)
    case.assessment = assessment

    # 4. Update status and compute provisional integrity hash
    case.status = CaseStatus.READY_FOR_REVIEW
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)

    # 5. Persist to DB
    saved_case = CaseRepository.save_case(db, case)

    # 6. Record append-only audit event
    CaseRepository.add_audit_event(
        db=db,
        case_id=case_id,
        event_type="INVESTIGATION_COMPLETED",
        actor="system",
        actor_role="research_agent",
        event_data={
            "evidence_count": len(evidence_items),
            "source_mode": case.source_mode.value,
            "recommendation": assessment.recommendation.value,
            "risk_score": assessment.risk_score,
            "rules_triggered": [r.rule_id for r in assessment.triggered_rules],
            "hard_gates": assessment.hard_gates_triggered,
            "audit_hash": case.audit_hash_sha256
        },
        ruleset_version=assessment.ruleset_version
    )

    return saved_case
