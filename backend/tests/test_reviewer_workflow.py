import pytest
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.enums import CaseStatus, RecommendationOutcome

client = TestClient(app)

def test_mandatory_rationale_enforced():
    case_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Review Test Vendor", "total_amount": 20000.0}
    )
    case_id = case_resp.json()["case_id"]

    # Attempt sign-off with empty rationale -> 422 Unprocessable Entity
    rev_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action_id": "temp",
            "case_id": case_id,
            "reviewer_id": "analyst_test",
            "action": "APPROVE",
            "rationale": "ok"  # Too short (< 5 chars)
        }
    )
    assert rev_resp.status_code == 422
    assert "at least 5" in rev_resp.text

def test_support_escalate_and_request_documents():
    case_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Escalate Test Vendor", "total_amount": 50000.0}
    )
    case_id = case_resp.json()["case_id"]

    # 1. Action: REQUEST_DOCUMENTS -> moves to PENDING_DOCUMENTS
    req_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action_id": "act_1",
            "case_id": case_id,
            "reviewer_id": "analyst_test",
            "action": "REQUEST_DOCUMENTS",
            "rationale": "Holding for cancelled cheque copy to verify beneficiary.",
            "requested_documents": ["cancelled_cheque.pdf"]
        }
    )
    assert req_resp.status_code == 200
    assert req_resp.json()["status"] == CaseStatus.PENDING_DOCUMENTS.value

    # 2. Action: ESCALATE from PENDING_DOCUMENTS -> moves to ESCALATED
    esc_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action_id": "act_2",
            "case_id": case_id,
            "reviewer_id": "analyst_test",
            "action": "ESCALATE",
            "rationale": "Vendor did not provide cancelled cheque within 48 hours; escalating to AP Manager."
        }
    )
    assert esc_resp.status_code == 200
    assert esc_resp.json()["status"] == CaseStatus.ESCALATED.value

def test_invoice_correction_triggers_fresh_assessment():
    # Create case and investigate with mismatch
    case_resp = client.post(
        "/api/cases",
        data={
            "supplier_name": "Specter Cloud Technologies",
            "gstin": "07AAAAA0000A1Z5",
            "total_amount": 10000.0
        }
    )
    case_id = case_resp.json()["case_id"]
    inv_resp = client.post(f"/api/cases/{case_id}/investigate")
    assert inv_resp.status_code == 200
    assert inv_resp.json()["assessment"]["recommendation"] == RecommendationOutcome.BLOCK.value

    # Correct invoice supplier name to match registered trade name
    patch_resp = client.patch(
        f"/api/cases/{case_id}/invoice",
        json={
            "corrected_supplier_name": "Apex Courier",
            "correction_notes": "Corrected OCR misread of vendor entity"
        }
    )
    assert patch_resp.status_code == 200
    updated_case = patch_resp.json()
    assert updated_case["invoice"]["supplier_name"] == "Apex Courier"
    # Fresh assessment triggered automatically: BLOCK should change to MANUAL_REVIEW
    assert updated_case["assessment"]["recommendation"] == RecommendationOutcome.MANUAL_REVIEW.value
    assert "CRITICAL_NAME_MISMATCH" not in updated_case["assessment"]["reason_codes"]
