from fastapi import APIRouter, HTTPException
from ..schemas.case import Case
from ..schemas.enums import CaseStatus
from .cases import case_store
from ..services.tinyfish.orchestrator import MultiHopTinyFishOrchestrator
from ..services.reconciler.evidence_reconciler import EvidenceReconciler
from ..services.rules.forensic_engine import ForensicRiskEngine
from ..services.audit.trail import AuditTrailService

router = APIRouter(prefix="/cases", tags=["investigation"])

orchestrator = MultiHopTinyFishOrchestrator()
reconciler = EvidenceReconciler()
forensic_engine = ForensicRiskEngine()
audit_service = AuditTrailService()

@router.post("/{case_id}/investigate", response_model=Case)
async def run_investigation(case_id: str):
    """
    VendorShield 2.0: Triggers 4-hop autonomous forensic investigation via TinyFish:
    - Hop 1: Entity & Constitution Verification (GSTN/MCA)
    - Hop 2: Director Portfolio & Shell Contagion Traversal
    - Hop 3: Geolocation Grounding & Ghost Hub Detection
    - Hop 4: Regulatory & NCLT Insolvency Sweep
    Evaluates the 5-Vector Forensic Risk Topology & Direct ₹ ITC Clawback Exposure.
    """
    if case_id not in case_store:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = case_store[case_id]
    if not case.invoice:
        raise HTTPException(status_code=400, detail="Invoice claims missing")

    case.status = CaseStatus.INVESTIGATING

    # 1. Gather 4-hop multi-entity evidence via TinyFish Orchestrator
    evidence_items, directors, address_cluster, litigation_meta = await orchestrator.execute_investigation(
        supplier_name=case.invoice.supplier_name,
        gstin=case.invoice.gstin,
        address=case.invoice.billing_address
    )
    case.evidence_items = evidence_items
    case.source_mode = orchestrator.source_mode

    # 2. Reconcile evidence against invoice claims
    field_checks = reconciler.reconcile(case.invoice, evidence_items)

    # 3. Apply 5-Vector Forensic Topology & compute direct ₹ ITC exposure
    assessment = forensic_engine.evaluate(
        case_id=case_id,
        invoice=case.invoice,
        field_checks=field_checks,
        directors=directors,
        address_cluster=address_cluster,
        litigation_meta=litigation_meta,
        evidence_items=evidence_items
    )
    case.assessment = assessment

    # 4. Update status and compute provisional integrity hash
    case.status = CaseStatus.READY_FOR_REVIEW
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)

    return case

