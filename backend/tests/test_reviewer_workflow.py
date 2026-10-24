import pytest
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.enums import CaseStatus, RecommendationOutcome

client = TestClient(app)

def test_review_rejected_when_assessment_missing():
    # Case created but not investigated -> has no assessment
    case_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Unassessed Vendor", "total_amount": 15000.0}
    )
    assert case_resp.status_code == 201
    case_id = case_resp.json()["case_id"]

    # Attempt to review before running investigation
    rev_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action": "APPROVE",
            "rationale": "Attempting signoff without assessment"
        }
    )
    assert rev_resp.status_code == 400
    assert "risk assessment" in rev_resp.text.lower()

def test_mandatory_rationale_enforced():
    case_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Review Test Vendor", "total_amount": 20000.0}
    )
    case_id = case_resp.json()["case_id"]

    # Investigate to establish assessment
    inv_resp = client.post(f"/api/cases/{case_id}/investigate")
    assert inv_resp.status_code == 200
    assert inv_resp.json()["status"] == CaseStatus.READY_FOR_REVIEW.value

    # Attempt sign-off with short rationale (< 5 chars) -> 422 Unprocessable Entity
    rev_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action": "APPROVE",
            "rationale": "ok"
        }
    )
    assert rev_resp.status_code == 422
    assert "at least 5" in rev_resp.text

def test_clean_review_contract_server_generated_ids():
    case_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Contract Test Vendor", "total_amount": 35000.0}
    )
    case_id = case_resp.json()["case_id"]

    # Run investigation
    client.post(f"/api/cases/{case_id}/investigate")

    # Client sends clean request without action_id or case_id
    rev_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action": "APPROVE",
            "rationale": "All documentation verified against registry.",
            "reviewer_id": "auditor_jane"
        }
    )
    assert rev_resp.status_code == 200
    case_data = rev_resp.json()
    assert case_data["status"] == CaseStatus.RESOLVED.value
    review = case_data["review"]
    assert review is not None
    # Server generated trusted IDs
    assert review["action_id"].startswith("act_")
    assert review["case_id"] == case_id
    assert review["reviewer_id"] == "dev_unauthenticated:auditor_jane"
    assert review["auth_mode"] == "DEV_MODE_UNAUTHENTICATED"
    assert review["action"] == "APPROVE"

def test_cannot_review_already_resolved_case():
    case_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Resolved Test Vendor", "total_amount": 40000.0}
    )
    case_id = case_resp.json()["case_id"]
    client.post(f"/api/cases/{case_id}/investigate")

    # First review resolves the case
    rev1 = client.post(
        f"/api/cases/{case_id}/review",
        json={"action": "APPROVE", "rationale": "First approval sign-off."}
    )
    assert rev1.status_code == 200
    assert rev1.json()["status"] == CaseStatus.RESOLVED.value

    # Attempting to review again on RESOLVED case -> 400
    rev2 = client.post(
        f"/api/cases/{case_id}/review",
        json={"action": "REJECT", "rationale": "Attempting second review on resolved case."}
    )
    assert rev2.status_code == 400
    assert "already been resolved" in rev2.text.lower()

def test_support_escalate_and_request_documents():
    case_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Escalate Test Vendor", "total_amount": 50000.0}
    )
    case_id = case_resp.json()["case_id"]
    client.post(f"/api/cases/{case_id}/investigate")

    # 1. Action: REQUEST_DOCUMENTS -> moves to PENDING_DOCUMENTS
    req_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
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
            "action": "ESCALATE",
            "rationale": "Vendor did not provide cancelled cheque within 48 hours; escalating to AP Manager."
        }
    )
    assert esc_resp.status_code == 200
    assert esc_resp.json()["status"] == CaseStatus.ESCALATED.value

def test_invoice_correction_triggers_fresh_assessment():
    case_resp = client.post(
        "/api/cases",
        data={
            "supplier_name": "Specter Cloud Technologies",
            "gstin": "07AAAAA0000A1Z4",
            "total_amount": 10000.0,
            "is_demo": "true"
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
    # Fresh assessment triggered automatically
    assert updated_case["assessment"]["recommendation"] == RecommendationOutcome.MANUAL_REVIEW.value
