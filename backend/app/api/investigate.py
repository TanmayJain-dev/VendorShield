from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..schemas.case import Case
from ..schemas.enums import CaseStatus
from ..db.database import get_db
from ..db.repository import CaseRepository
from ..services.tinyfish.orchestrator import MultiHopTinyFishOrchestrator
from ..services.rules.assessment_service import assessment_service
from ..services.audit.trail import AuditTrailService
from ..config import settings

router = APIRouter(prefix="/cases", tags=["investigation"])

orchestrator = MultiHopTinyFishOrchestrator(api_key=settings.TINYFISH_API_KEY)
audit_service = AuditTrailService()

@router.post("/{case_id}/investigate", response_model=Case)
async def run_investigation(case_id: str, db: Session = Depends(get_db)):
    """
    VendorShield Investigation:
    Gathers multi-hop evidence via TinyFish Orchestrator (or pluggable providers),
    reconciles evidence, evaluates unified assessment, updates database and audit trail.
    """
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if not case.invoice:
        raise HTTPException(status_code=400, detail="Invoice claims missing")

    case.status = CaseStatus.INVESTIGATING

    # 1. Gather multi-entity evidence via TinyFish Orchestrator
    evidence_items, directors, address_cluster, litigation_meta = await orchestrator.execute_investigation(
        supplier_name=case.invoice.supplier_name,
        gstin=case.invoice.gstin,
        address=case.invoice.billing_address,
        is_demo=getattr(case, "is_demo", False)
    )
    case.evidence_items = evidence_items
    case.source_mode = orchestrator.source_mode

    # 2. Evaluate unified assessment via AssessmentService
    assessment = assessment_service.assess(
        case=case,
        directors=directors,
        address_cluster=address_cluster,
        litigation_meta=litigation_meta
    )
    case.assessment = assessment

    # 3. Update status and compute provisional integrity hash
    case.status = CaseStatus.READY_FOR_REVIEW
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)

    # 4. Persist to DB
    saved_case = CaseRepository.save_case(db, case)

    # 5. Record append-only audit event
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
            "rules_triggered": [r.rule_id for r in assessment.triggered_rules] if hasattr(assessment, "triggered_rules") else [],
            "hard_gates": assessment.hard_gates_triggered,
            "audit_hash": case.audit_hash_sha256
        },
        ruleset_version=assessment.ruleset_version
    )

    return saved_case
