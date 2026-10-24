import json
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.auth.security import load_users, TokenRateLimiter
from app.db.database import SessionLocal, init_db
from app.db.models import AuditEventModel
from app.db.repository import CaseRepository
from app.schemas.case import Case
from app.schemas.invoice import InvoiceClaim
from app.schemas.enums import CaseStatus

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_users_json_loading(monkeypatch):
    mock_users = json.dumps([
        {"token": "token-test-analyst-1", "id": "priya_analyst", "role": "ap_analyst"},
        {"token": "token-test-reviewer-2", "id": "garv_reviewer", "role": "reviewer"}
    ])
    monkeypatch.setattr(settings, "USERS_JSON", mock_users)
    
    users = load_users()
    assert "token-test-analyst-1" in users
    assert users["token-test-analyst-1"].id == "priya_analyst"
    assert users["token-test-analyst-1"].role == "ap_analyst"
    
    assert "token-test-reviewer-2" in users
    assert users["token-test-reviewer-2"].id == "garv_reviewer"
    assert users["token-test-reviewer-2"].role == "reviewer"


def test_rate_limiter_enforcement():
    limiter = TokenRateLimiter(max_requests=5, window_seconds=10)
    test_token = "rate-limit-test-token"
    
    for _ in range(5):
        limiter.check_rate_limit(test_token)
        
    with pytest.raises(Exception) as excinfo:
        limiter.check_rate_limit(test_token)
    assert "429" in str(excinfo.value)


def test_analyst_cannot_sign_off_review(monkeypatch):
    mock_users = json.dumps([
        {"token": "analyst-token", "id": "analyst_sam", "role": "ap_analyst"}
    ])
    monkeypatch.setattr(settings, "USERS_JSON", mock_users)

    # Attempt to submit review with analyst token
    resp = client.post(
        "/api/cases/case_nonexistent/review",
        headers={"Authorization": "Bearer analyst-token"},
        json={
            "action": "APPROVE",
            "rationale": "Analyst attempting unauthorized sign-off"
        }
    )
    assert resp.status_code == 403
    assert "Reviewer role required" in resp.json()["detail"]


def test_audit_chain_verification_intact():
    db = SessionLocal()
    try:
        case_id = f"case_audit_{uuid.uuid4().hex[:8]}"

        case = Case(
            case_id=case_id,
            case_reference="INV-AUDIT-001",
            status=CaseStatus.SUBMITTED,
            invoice=InvoiceClaim(
                invoice_number="INV-AUDIT-001",
                supplier_name="Apex Logistics",
                total_amount=1000.0,
                taxable_amount=1000.0
            )
        )
        CaseRepository.save_case(db, case)

        CaseRepository.add_audit_event(db, case_id, "CASE_CREATED", "analyst_1", "ap_analyst", {"note": "created"})
        CaseRepository.add_audit_event(db, case_id, "INVESTIGATION_STARTED", "analyst_1", "ap_analyst", {"hop": 1})
        CaseRepository.add_audit_event(db, case_id, "EVIDENCE_ATTACHED", "system", "system", {"provider": "manual"})

        verify_res = CaseRepository.verify_audit_chain(db, case_id)
        assert verify_res["chain_valid"] is True
        assert verify_res["broken_event_id"] is None
        assert verify_res["total_events"] == 3
        assert "intact and fully verified" in verify_res["detail"]
    finally:
        db.close()


def test_audit_chain_verification_detects_tampering():
    db = SessionLocal()
    try:
        case_id = f"case_tamper_{uuid.uuid4().hex[:8]}"

        case = Case(
            case_id=case_id,
            case_reference="INV-AUDIT-002",
            status=CaseStatus.SUBMITTED,
            invoice=InvoiceClaim(
                invoice_number="INV-AUDIT-002",
                supplier_name="Apex Logistics",
                total_amount=1000.0,
                taxable_amount=1000.0
            )
        )
        CaseRepository.save_case(db, case)

        CaseRepository.add_audit_event(db, case_id, "CASE_CREATED", "analyst_1", "ap_analyst", {"note": "step 1"})
        ev2 = CaseRepository.add_audit_event(db, case_id, "INVESTIGATION_STARTED", "analyst_1", "ap_analyst", {"note": "step 2"})
        CaseRepository.add_audit_event(db, case_id, "EVIDENCE_ATTACHED", "system", "system", {"note": "step 3"})

        # Tamper with event 2 in the database directly
        db_ev = db.query(AuditEventModel).filter(AuditEventModel.event_id == ev2.event_id).first()
        db_ev.event_data_json = '{"note": "tampered content"}'
        db.commit()

        verify_res = CaseRepository.verify_audit_chain(db, case_id)
        assert verify_res["chain_valid"] is False
        assert verify_res["broken_event_id"] == ev2.event_id
        assert verify_res["broken_event_index"] == 1
        assert "Content has been modified" in verify_res["detail"]
    finally:
        db.close()


def test_audit_verify_api_endpoint():
    db = SessionLocal()
    try:
        case_id = f"case_api_verify_{uuid.uuid4().hex[:8]}"

        case = Case(
            case_id=case_id,
            case_reference="INV-VERIFY-003",
            status=CaseStatus.SUBMITTED,
            invoice=InvoiceClaim(
                invoice_number="INV-VERIFY-003",
                supplier_name="Apex Logistics",
                total_amount=1000.0,
                taxable_amount=1000.0
            )
        )
        CaseRepository.save_case(db, case)
        CaseRepository.add_audit_event(db, case_id, "CASE_CREATED", "system", "system", {"init": True})

        resp = client.get(f"/api/cases/{case_id}/audit/verify")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chain_valid"] is True
        assert data["total_events"] == 1
    finally:
        db.close()
