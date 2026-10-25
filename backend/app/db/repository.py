import json
import hashlib
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .models import (
    CaseModel, InvoiceModel, EvidenceItemModel,
    AssessmentModel, ReviewActionModel, AuditEventModel
)
from ..schemas.case import Case, CaseSummary
from ..schemas.invoice import InvoiceClaim, LineItem, TaxBreakdownItem, FieldExtractionMeta
from ..schemas.evidence import EvidenceItem, FieldCheckResult
from ..schemas.assessment import RiskAssessment, RuleTrigger
from ..schemas.forensic_graph import ForensicVectorScores, ITCExposureDetails, EntityGraph, TreasurySettlementDetails
from ..schemas.review import ReviewAction
from ..schemas.enums import (
    CaseStatus, SourceMode, RecommendationOutcome, CheckStatus,
    ExtractionStatus, ReviewActionType
)

def _canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, default=str)

def _compute_event_hash(prev_hash: str, timestamp: str, event_type: str, actor: str, data_json: str) -> str:
    seed = f"{prev_hash}|{timestamp}|{event_type}|{actor}|{data_json}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()

class CaseRepository:
    @staticmethod
    def model_to_case(cm: CaseModel) -> Case:
        # Reconstruct InvoiceClaim
        inv_claim = None
        if cm.invoice:
            im = cm.invoice
            line_items = []
            try:
                for li in json.loads(im.line_items_json or "[]"):
                    line_items.append(LineItem(**li))
            except Exception:
                pass

            tax_breakdown = []
            try:
                for tb in json.loads(im.tax_breakdown_json or "[]"):
                    tax_breakdown.append(TaxBreakdownItem(**tb))
            except Exception:
                pass

            extraction_metadata = {}
            try:
                raw_meta = json.loads(im.extraction_metadata_json or "{}")
                for k, v in raw_meta.items():
                    extraction_metadata[k] = FieldExtractionMeta(**v)
            except Exception:
                pass

            parsing_errors = []
            try:
                parsing_errors = json.loads(im.parsing_errors_json or "[]")
            except Exception:
                pass

            parsing_warnings = []
            try:
                parsing_warnings = json.loads(im.parsing_warnings_json or "[]")
            except Exception:
                pass

            inv_claim = InvoiceClaim(
                invoice_number=im.invoice_number,
                invoice_date=im.invoice_date,
                supplier_name=im.supplier_name,
                legal_name=im.legal_name,
                gstin=im.gstin,
                billing_address=im.billing_address,
                place_of_supply=im.place_of_supply,
                discount_amount=im.discount_amount or 0.0,
                round_off=im.round_off or 0.0,
                taxable_amount=im.taxable_amount or 0.0,
                cgst=im.cgst or 0.0,
                sgst=im.sgst or 0.0,
                igst=im.igst or 0.0,
                total_amount=im.total_amount or 0.0,
                tax_breakdown=tax_breakdown,
                bank_account_masked=im.bank_account_masked,
                ifsc_code=im.ifsc_code,
                line_items=line_items,
                gstin_format_valid=im.gstin_format_valid,
                arithmetic_valid=im.arithmetic_valid,
                arithmetic_notes=im.arithmetic_notes,
                raw_text=im.raw_text,
                extraction_metadata=extraction_metadata,
                parsing_errors=parsing_errors,
                parsing_warnings=parsing_warnings,
                is_scanned_image=im.is_scanned_image or False,
                ocr_applied=im.ocr_applied or False,
                ocr_status_message=im.ocr_status_message,
                file_sha256=im.file_sha256,
                duplicate_status=im.duplicate_status,
                duplicate_case_id=im.duplicate_case_id
            )

        # Reconstruct EvidenceItems
        evidence_items = []
        for em in (cm.evidence_items or []):
            facts = {}
            try:
                facts = json.loads(em.facts_json or "{}")
            except Exception:
                pass
            evidence_items.append(EvidenceItem(
                evidence_id=em.evidence_id,
                source_url=em.source_url,
                source_name=em.source_name,
                claim_supported=em.claim_supported,
                source_type=em.source_type,
                source_mode=SourceMode(em.source_mode) if em.source_mode in SourceMode.__members__.values() else SourceMode.SIMULATED,
                is_fallback=em.is_fallback or False,
                fallback_reason=em.fallback_reason,
                retrieved_at=em.retrieved_at,
                raw_excerpt=em.raw_excerpt,
                facts=facts,
                is_authoritative=em.is_authoritative or False,
                match_rationale=em.match_rationale
            ))

        # Reconstruct RiskAssessment
        assessment = None
        if cm.assessment:
            am = cm.assessment
            reason_codes = []
            hard_gates = []
            field_checks = []
            triggered_rules = []
            missing_evidence = []
            try:
                reason_codes = json.loads(am.reason_codes_json or "[]")
                hard_gates = json.loads(am.hard_gates_json or "[]")
                missing_evidence = json.loads(am.missing_evidence_items_json or "[]")
                for fc in json.loads(am.field_checks_json or "[]"):
                    field_checks.append(FieldCheckResult(**fc))
                for tr in json.loads(am.triggered_rules_json or "[]"):
                    triggered_rules.append(RuleTrigger(**tr))
            except Exception:
                pass

            forensic_vectors = None
            itc_exposure = None
            entity_graph = None
            if getattr(am, "forensic_vectors_json", None):
                try:
                    forensic_vectors = ForensicVectorScores(**json.loads(am.forensic_vectors_json))
                except Exception:
                    pass
            if getattr(am, "itc_exposure_json", None):
                try:
                    itc_exposure = ITCExposureDetails(**json.loads(am.itc_exposure_json))
                except Exception:
                    pass
            if getattr(am, "entity_graph_json", None):
                try:
                    entity_graph = EntityGraph(**json.loads(am.entity_graph_json))
                except Exception:
                    pass

            treasury_settlement = None
            if getattr(am, "treasury_settlement_json", None):
                try:
                    treasury_settlement = TreasurySettlementDetails(**json.loads(am.treasury_settlement_json))
                except Exception:
                    pass
            ims_action_json = None
            if getattr(am, "ims_action_json", None):
                try:
                    ims_action_json = json.loads(am.ims_action_json)
                except Exception:
                    pass

            assessment = RiskAssessment(
                assessment_id=am.assessment_id,
                case_id=am.case_id,
                ruleset_version=am.ruleset_version or "1.0.0",
                recommendation=RecommendationOutcome(am.recommendation) if am.recommendation in RecommendationOutcome.__members__.values() else RecommendationOutcome.MANUAL_REVIEW,
                risk_score=am.risk_score,
                score_explanation=am.score_explanation or "",
                reason_codes=reason_codes,
                field_checks=field_checks,
                hard_gates_triggered=hard_gates,
                triggered_rules=triggered_rules,
                missing_evidence_items=missing_evidence,
                forensic_vectors=forensic_vectors,
                itc_exposure=itc_exposure,
                entity_graph=entity_graph,
                treasury_settlement=treasury_settlement,
                gstn_ims_action=getattr(am, "gstn_ims_action", None),
                ims_action_json=ims_action_json,
                evidence_completeness=am.evidence_completeness or "COMPLETE",
                evidence_provenance_mode=SourceMode(am.evidence_provenance_mode) if am.evidence_provenance_mode in SourceMode.__members__.values() else SourceMode.SIMULATED,
                human_signoff_required=am.human_signoff_required if am.human_signoff_required is not None else True,
                assessed_at=am.assessed_at
            )

        # Reconstruct ReviewAction (latest) & Review History
        latest_review = None
        review_history = []
        for rm in (cm.reviews or []):
            req_docs = []
            try:
                req_docs = json.loads(rm.requested_documents_json or "[]")
            except Exception:
                pass
            ra = ReviewAction(
                action_id=rm.action_id,
                case_id=rm.case_id,
                reviewer_id=rm.reviewer_id,
                reviewer_role=rm.reviewer_role or "ap_analyst",
                action=ReviewActionType(rm.action) if rm.action in ReviewActionType.__members__.values() else ReviewActionType.APPROVE,
                rationale=rm.rationale,
                requested_documents=req_docs,
                auth_mode=rm.auth_mode or "DEV_MODE_UNAUTHENTICATED",
                recorded_at=rm.recorded_at
            )
            review_history.append(ra)
        if review_history:
            latest_review = review_history[0]

        return Case(
            case_id=cm.case_id,
            case_reference=cm.case_reference,
            status=CaseStatus(cm.status) if cm.status in CaseStatus.__members__.values() else CaseStatus.SUBMITTED,
            source_mode=SourceMode(cm.source_mode) if cm.source_mode in SourceMode.__members__.values() else SourceMode.SIMULATED,
            created_at=cm.created_at,
            updated_at=cm.updated_at,
            created_by=cm.created_by or "ap_analyst",
            file_sha256=cm.file_sha256,
            duplicate_of_case_id=cm.duplicate_of_case_id,
            duplicate_type=cm.duplicate_type,
            invoice=inv_claim,
            evidence_items=evidence_items,
            assessment=assessment,
            review=latest_review,
            review_history=review_history,
            audit_hash_sha256=cm.audit_hash_sha256
        )

    @staticmethod
    def get_case(db: Session, case_id: str) -> Optional[Case]:
        cm = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
        if not cm:
            return None
        return CaseRepository.model_to_case(cm)

    @staticmethod
    def list_cases(db: Session) -> List[CaseSummary]:
        cases = db.query(CaseModel).order_by(CaseModel.created_at.desc()).all()
        summaries = []
        for cm in cases:
            supp_name = "Unknown"
            inv_no = "N/A"
            total = 0.0
            if cm.invoice:
                supp_name = cm.invoice.supplier_name
                inv_no = cm.invoice.invoice_number
                total = cm.invoice.total_amount or 0.0

            rec = None
            score = None
            if cm.assessment:
                try:
                    rec = RecommendationOutcome(cm.assessment.recommendation)
                    score = cm.assessment.risk_score
                except Exception:
                    pass

            summaries.append(CaseSummary(
                case_id=cm.case_id,
                case_reference=cm.case_reference,
                status=CaseStatus(cm.status) if cm.status in CaseStatus.__members__.values() else CaseStatus.SUBMITTED,
                source_mode=SourceMode(cm.source_mode) if cm.source_mode in SourceMode.__members__.values() else SourceMode.SIMULATED,
                supplier_name=supp_name,
                invoice_number=inv_no,
                total_amount=total,
                recommendation=rec,
                risk_score=score,
                duplicate_type=cm.duplicate_type,
                created_at=cm.created_at
            ))
        return summaries

    @staticmethod
    def save_case(db: Session, case: Case, normalized_key: Optional[str] = None) -> Case:
        cm = db.query(CaseModel).filter(CaseModel.case_id == case.case_id).first()
        now_str = datetime.now(timezone.utc).isoformat()
        if not cm:
            cm = CaseModel(
                case_id=case.case_id,
                case_reference=case.case_reference,
                status=case.status.value,
                source_mode=case.source_mode.value,
                created_at=case.created_at or now_str,
                updated_at=case.updated_at or now_str,
                created_by=case.created_by,
                file_sha256=case.file_sha256,
                normalized_invoice_key=normalized_key,
                duplicate_of_case_id=case.duplicate_of_case_id,
                duplicate_type=case.duplicate_type,
                audit_hash_sha256=case.audit_hash_sha256
            )
            db.add(cm)
        else:
            cm.status = case.status.value
            cm.source_mode = case.source_mode.value
            cm.updated_at = now_str
            if case.file_sha256:
                cm.file_sha256 = case.file_sha256
            if normalized_key:
                cm.normalized_invoice_key = normalized_key
            if case.duplicate_of_case_id:
                cm.duplicate_of_case_id = case.duplicate_of_case_id
            if case.duplicate_type:
                cm.duplicate_type = case.duplicate_type
            if case.audit_hash_sha256:
                cm.audit_hash_sha256 = case.audit_hash_sha256

        # Update/create Invoice
        if case.invoice:
            inv = case.invoice
            im = cm.invoice
            line_items_data = [li.model_dump() for li in inv.line_items]
            tax_breakdown_data = [tb.model_dump() for tb in inv.tax_breakdown]
            extraction_meta_data = {k: v.model_dump() for k, v in inv.extraction_metadata.items()}

            if not im:
                im = InvoiceModel(
                    case_id=case.case_id,
                    invoice_number=inv.invoice_number,
                    invoice_date=inv.invoice_date,
                    supplier_name=inv.supplier_name,
                    legal_name=inv.legal_name,
                    gstin=inv.gstin,
                    billing_address=inv.billing_address,
                    place_of_supply=inv.place_of_supply,
                    discount_amount=inv.discount_amount,
                    round_off=inv.round_off,
                    taxable_amount=inv.taxable_amount,
                    cgst=inv.cgst,
                    sgst=inv.sgst,
                    igst=inv.igst,
                    total_amount=inv.total_amount,
                    bank_account_masked=inv.bank_account_masked,
                    ifsc_code=inv.ifsc_code,
                    line_items_json=json.dumps(line_items_data),
                    tax_breakdown_json=json.dumps(tax_breakdown_data),
                    gstin_format_valid=inv.gstin_format_valid,
                    arithmetic_valid=inv.arithmetic_valid,
                    arithmetic_notes=inv.arithmetic_notes,
                    raw_text=inv.raw_text,
                    extraction_metadata_json=json.dumps(extraction_meta_data),
                    parsing_errors_json=json.dumps(inv.parsing_errors),
                    parsing_warnings_json=json.dumps(inv.parsing_warnings),
                    is_scanned_image=inv.is_scanned_image,
                    ocr_applied=inv.ocr_applied,
                    ocr_status_message=inv.ocr_status_message,
                    file_sha256=inv.file_sha256,
                    duplicate_status=inv.duplicate_status,
                    duplicate_case_id=inv.duplicate_case_id
                )
                db.add(im)
            else:
                im.invoice_number = inv.invoice_number
                im.invoice_date = inv.invoice_date
                im.supplier_name = inv.supplier_name
                im.legal_name = inv.legal_name
                im.gstin = inv.gstin
                im.billing_address = inv.billing_address
                im.place_of_supply = inv.place_of_supply
                im.discount_amount = inv.discount_amount
                im.round_off = inv.round_off
                im.taxable_amount = inv.taxable_amount
                im.cgst = inv.cgst
                im.sgst = inv.sgst
                im.igst = inv.igst
                im.total_amount = inv.total_amount
                im.bank_account_masked = inv.bank_account_masked
                im.ifsc_code = inv.ifsc_code
                im.line_items_json = json.dumps(line_items_data)
                im.tax_breakdown_json = json.dumps(tax_breakdown_data)
                im.gstin_format_valid = inv.gstin_format_valid
                im.arithmetic_valid = inv.arithmetic_valid
                im.arithmetic_notes = inv.arithmetic_notes
                im.raw_text = inv.raw_text
                im.extraction_metadata_json = json.dumps(extraction_meta_data)
                im.parsing_errors_json = json.dumps(inv.parsing_errors)
                im.parsing_warnings_json = json.dumps(inv.parsing_warnings)
                im.is_scanned_image = inv.is_scanned_image
                im.ocr_applied = inv.ocr_applied
                im.ocr_status_message = inv.ocr_status_message
                im.file_sha256 = inv.file_sha256
                im.duplicate_status = inv.duplicate_status
                im.duplicate_case_id = inv.duplicate_case_id

        # Update Evidence Items
        if case.evidence_items:
            db.query(EvidenceItemModel).filter(EvidenceItemModel.case_id == case.case_id).delete()
            for ev in case.evidence_items:
                em = EvidenceItemModel(
                    case_id=case.case_id,
                    evidence_id=ev.evidence_id,
                    source_url=ev.source_url,
                    source_name=ev.source_name,
                    claim_supported=ev.claim_supported,
                    source_type=ev.source_type,
                    source_mode=ev.source_mode.value,
                    is_fallback=ev.is_fallback,
                    fallback_reason=ev.fallback_reason,
                    retrieved_at=ev.retrieved_at,
                    raw_excerpt=ev.raw_excerpt,
                    facts_json=json.dumps(ev.facts),
                    is_authoritative=ev.is_authoritative,
                    match_rationale=ev.match_rationale
                )
                db.add(em)

        # Update Assessment
        if case.assessment:
            ass = case.assessment
            am = cm.assessment
            fc_data = [fc.model_dump() for fc in ass.field_checks] if ass.field_checks else []
            tr_data = [tr.model_dump() for tr in ass.triggered_rules] if hasattr(ass, "triggered_rules") and ass.triggered_rules else []
            fv_json = json.dumps(ass.forensic_vectors.model_dump()) if getattr(ass, "forensic_vectors", None) else None
            itc_json = json.dumps(ass.itc_exposure.model_dump()) if getattr(ass, "itc_exposure", None) else None
            eg_json = json.dumps(ass.entity_graph.model_dump()) if getattr(ass, "entity_graph", None) else None
            ts_json = json.dumps(ass.treasury_settlement.model_dump()) if getattr(ass, "treasury_settlement", None) else None
            ims_payload_json = json.dumps(ass.ims_action_json) if getattr(ass, "ims_action_json", None) else None

            if not am:
                am = AssessmentModel(
                    case_id=case.case_id,
                    assessment_id=ass.assessment_id,
                    ruleset_version=ass.ruleset_version,
                    recommendation=ass.recommendation.value,
                    risk_score=ass.risk_score,
                    score_explanation=ass.score_explanation,
                    reason_codes_json=json.dumps(ass.reason_codes),
                    hard_gates_json=json.dumps(ass.hard_gates_triggered),
                    field_checks_json=json.dumps(fc_data),
                    triggered_rules_json=json.dumps(tr_data),
                    missing_evidence_items_json=json.dumps(ass.missing_evidence_items),
                    forensic_vectors_json=fv_json,
                    itc_exposure_json=itc_json,
                    entity_graph_json=eg_json,
                    treasury_settlement_json=ts_json,
                    gstn_ims_action=getattr(ass, "gstn_ims_action", None),
                    ims_action_json=ims_payload_json,
                    evidence_completeness=ass.evidence_completeness,
                    evidence_provenance_mode=ass.evidence_provenance_mode.value,
                    human_signoff_required=ass.human_signoff_required,
                    assessed_at=ass.assessed_at
                )
                db.add(am)
            else:
                am.assessment_id = ass.assessment_id
                am.ruleset_version = ass.ruleset_version
                am.recommendation = ass.recommendation.value
                am.risk_score = ass.risk_score
                am.score_explanation = ass.score_explanation
                am.reason_codes_json = json.dumps(ass.reason_codes)
                am.hard_gates_json = json.dumps(ass.hard_gates_triggered)
                am.field_checks_json = json.dumps(fc_data)
                am.triggered_rules_json = json.dumps(tr_data)
                am.missing_evidence_items_json = json.dumps(ass.missing_evidence_items)
                am.forensic_vectors_json = fv_json
                am.itc_exposure_json = itc_json
                am.entity_graph_json = eg_json
                am.treasury_settlement_json = ts_json
                am.gstn_ims_action = getattr(ass, "gstn_ims_action", None)
                am.ims_action_json = ims_payload_json
                am.evidence_completeness = ass.evidence_completeness
                am.evidence_provenance_mode = ass.evidence_provenance_mode.value
                am.human_signoff_required = ass.human_signoff_required
                am.assessed_at = ass.assessed_at

        # Update Review Decision
        if case.review:
            rev = case.review
            existing_rev = db.query(ReviewActionModel).filter(
                ReviewActionModel.action_id == rev.action_id
            ).first()
            if not existing_rev:
                rm = ReviewActionModel(
                    case_id=case.case_id,
                    action_id=rev.action_id,
                    reviewer_id=rev.reviewer_id,
                    reviewer_role=rev.reviewer_role,
                    action=rev.action.value,
                    rationale=rev.rationale,
                    requested_documents_json=json.dumps(rev.requested_documents),
                    auth_mode=rev.auth_mode,
                    recorded_at=rev.recorded_at
                )
                db.add(rm)

        db.commit()
        db.refresh(cm)
        return CaseRepository.model_to_case(cm)

    @staticmethod
    def add_audit_event(
        db: Session,
        case_id: str,
        event_type: str,
        actor: str,
        actor_role: str,
        event_data: dict,
        ruleset_version: str = "1.0.0"
    ) -> AuditEventModel:
        # Find latest event for this case to link previous hash
        last_event = db.query(AuditEventModel).filter(
            AuditEventModel.case_id == case_id
        ).order_by(AuditEventModel.id.desc()).first()

        prev_hash = last_event.event_hash if last_event else "0" * 64
        now_ts = datetime.now(timezone.utc).isoformat()
        data_json = _canonical_json(event_data)
        event_hash = _compute_event_hash(prev_hash, now_ts, event_type, actor, data_json)

        import uuid
        event = AuditEventModel(
            event_id=f"ev_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            actor_role=actor_role,
            timestamp=now_ts,
            event_data_json=data_json,
            ruleset_version=ruleset_version,
            prev_hash=prev_hash,
            event_hash=event_hash
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_audit_trail(db: Session, case_id: str) -> List[dict]:
        events = db.query(AuditEventModel).filter(
            AuditEventModel.case_id == case_id
        ).order_by(AuditEventModel.id.asc()).all()

        trail = []
        for e in events:
            trail.append({
                "event_id": e.event_id,
                "case_id": e.case_id,
                "event_type": e.event_type,
                "actor": e.actor,
                "actor_role": e.actor_role,
                "timestamp": e.timestamp,
                "event_data": json.loads(e.event_data_json or "{}"),
                "ruleset_version": e.ruleset_version,
                "prev_hash": e.prev_hash,
                "event_hash": e.event_hash
            })
        return trail

    @staticmethod
    def find_case_by_file_hash(db: Session, file_hash: str) -> Optional[CaseModel]:
        return db.query(CaseModel).filter(CaseModel.file_sha256 == file_hash).first()

    @staticmethod
    def find_case_by_normalized_key(db: Session, normalized_key: str) -> Optional[CaseModel]:
        return db.query(CaseModel).filter(CaseModel.normalized_invoice_key == normalized_key).first()

    @staticmethod
    def seed_benchmark_case(db: Session):
        case_id = "case_inv_2026_8841"
        existing = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
        if existing:
            return

        now_str = datetime.now(timezone.utc).isoformat()
        benchmark_case = Case(
            case_id=case_id,
            case_reference="INV-2026-8841",
            status=CaseStatus.PARSED,
            source_mode=SourceMode.SIMULATED,
            created_at=now_str,
            updated_at=now_str,
            invoice=InvoiceClaim(
                invoice_number="INV-2026-8841",
                invoice_date="2026-10-15",
                supplier_name="Apex Courier",
                legal_name="Apex Global Logistics Private Limited",
                gstin="07AAAAA0000A1Z5",
                billing_address="Okhla Industrial Area, Phase-II, New Delhi - 110020",
                taxable_amount=408898.31,
                cgst=36800.85,
                sgst=36800.85,
                igst=0.0,
                total_amount=482500.0,
                bank_account_masked="XXXX-XXXX-9921",
                ifsc_code="HDFC0000123",
                gstin_format_valid=True,
                arithmetic_valid=True,
                tax_breakdown=[
                    TaxBreakdownItem(tax_type="CGST", rate_pct=9.0, taxable_amount=408898.31, tax_amount=36800.85),
                    TaxBreakdownItem(tax_type="SGST", rate_pct=9.0, taxable_amount=408898.31, tax_amount=36800.85),
                ]
            )
        )
        CaseRepository.save_case(db, benchmark_case, normalized_key="apex courier_inv-2026-8841")
        CaseRepository.add_audit_event(
            db=db,
            case_id=case_id,
            event_type="CASE_SEEDED",
            actor="system",
            actor_role="system",
            event_data={"case_reference": "INV-2026-8841", "source": "benchmark_deck"}
        )
