from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, ForeignKey, DateTime
)
from sqlalchemy.orm import relationship
from .database import Base

class CaseModel(Base):
    __tablename__ = "cases"

    case_id = Column(String(64), primary_key=True, index=True)
    case_reference = Column(String(128), index=True, nullable=False)
    status = Column(String(32), default="SUBMITTED", nullable=False)
    source_mode = Column(String(32), default="SIMULATED", nullable=False)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)
    created_by = Column(String(64), default="ap_analyst")
    file_sha256 = Column(String(64), index=True, nullable=True)
    normalized_invoice_key = Column(String(128), index=True, nullable=True)
    duplicate_of_case_id = Column(String(64), nullable=True)
    duplicate_type = Column(String(64), nullable=True)
    audit_hash_sha256 = Column(String(64), nullable=True)

    # Relationships
    invoice = relationship("InvoiceModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceItemModel", back_populates="case", cascade="all, delete-orphan")
    assessment = relationship("AssessmentModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("ReviewActionModel", back_populates="case", cascade="all, delete-orphan", order_by="ReviewActionModel.recorded_at.desc()")
    audit_events = relationship("AuditEventModel", back_populates="case", cascade="all, delete-orphan", order_by="AuditEventModel.id.asc()")

class InvoiceModel(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), unique=True, nullable=False)
    invoice_number = Column(String(128), nullable=False)
    invoice_date = Column(String(64), nullable=True)
    supplier_name = Column(String(256), nullable=False)
    legal_name = Column(String(256), nullable=True)
    gstin = Column(String(32), nullable=True)
    billing_address = Column(Text, nullable=True)
    place_of_supply = Column(String(64), nullable=True)
    discount_amount = Column(Float, default=0.0)
    round_off = Column(Float, default=0.0)
    taxable_amount = Column(Float, default=0.0)
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    igst = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    bank_account_masked = Column(String(64), nullable=True)
    ifsc_code = Column(String(32), nullable=True)
    line_items_json = Column(Text, default="[]")
    tax_breakdown_json = Column(Text, default="[]")
    gstin_format_valid = Column(Boolean, nullable=True)
    arithmetic_valid = Column(Boolean, nullable=True)
    arithmetic_notes = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    extraction_metadata_json = Column(Text, default="{}")
    parsing_errors_json = Column(Text, default="[]")
    parsing_warnings_json = Column(Text, default="[]")
    is_scanned_image = Column(Boolean, default=False)
    ocr_applied = Column(Boolean, default=False)
    ocr_status_message = Column(Text, nullable=True)
    file_sha256 = Column(String(64), nullable=True)
    duplicate_status = Column(String(64), nullable=True)
    duplicate_case_id = Column(String(64), nullable=True)

    case = relationship("CaseModel", back_populates="invoice")

class EvidenceItemModel(Base):
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    evidence_id = Column(String(64), nullable=False)
    source_url = Column(Text, nullable=False)
    source_name = Column(String(256), nullable=False)
    claim_supported = Column(String(256), nullable=False)
    source_type = Column(String(64), default="PUBLIC_WEB")
    source_mode = Column(String(32), default="SIMULATED")
    is_fallback = Column(Boolean, default=False)
    fallback_reason = Column(Text, nullable=True)
    retrieved_at = Column(String(64), nullable=False)
    raw_excerpt = Column(Text, nullable=False)
    facts_json = Column(Text, default="{}")
    is_authoritative = Column(Boolean, default=False)
    match_rationale = Column(Text, nullable=True)

    case = relationship("CaseModel", back_populates="evidence_items")

class AssessmentModel(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), unique=True, nullable=False)
    assessment_id = Column(String(64), nullable=False)
    ruleset_version = Column(String(32), default="2.0.0")
    recommendation = Column(String(32), nullable=False)
    risk_score = Column(Integer, nullable=True)
    score_explanation = Column(Text, nullable=True)
    reason_codes_json = Column(Text, default="[]")
    hard_gates_json = Column(Text, default="[]")
    field_checks_json = Column(Text, default="[]")
    triggered_rules_json = Column(Text, default="[]")
    missing_evidence_items_json = Column(Text, default="[]")
    forensic_vectors_json = Column(Text, nullable=True)
    itc_exposure_json = Column(Text, nullable=True)
    entity_graph_json = Column(Text, nullable=True)
    treasury_settlement_json = Column(Text, nullable=True)
    gstn_ims_action = Column(String(64), nullable=True)
    ims_action_json = Column(Text, nullable=True)
    evidence_completeness = Column(String(32), default="COMPLETE")
    evidence_provenance_mode = Column(String(32), default="SIMULATED")
    human_signoff_required = Column(Boolean, default=True)
    assessed_at = Column(String(64), nullable=False)

    case = relationship("CaseModel", back_populates="assessment")

class ReviewActionModel(Base):
    __tablename__ = "review_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    action_id = Column(String(64), nullable=False)
    reviewer_id = Column(String(128), nullable=False)
    reviewer_role = Column(String(64), default="ap_analyst")
    action = Column(String(64), nullable=False)
    rationale = Column(Text, nullable=False)
    requested_documents_json = Column(Text, default="[]")
    auth_mode = Column(String(64), default="DEV_MODE_UNAUTHENTICATED")
    recorded_at = Column(String(64), nullable=False)

    case = relationship("CaseModel", back_populates="reviews")

class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    event_type = Column(String(64), nullable=False)
    actor = Column(String(128), nullable=False)
    actor_role = Column(String(64), default="system")
    timestamp = Column(String(64), nullable=False)
    event_data_json = Column(Text, default="{}")
    ruleset_version = Column(String(32), default="2.0.0")
    prev_hash = Column(String(64), default="0" * 64)
    event_hash = Column(String(64), nullable=False)

    case = relationship("CaseModel", back_populates="audit_events")
