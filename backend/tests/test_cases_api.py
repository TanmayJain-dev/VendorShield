import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.enums import CaseStatus, RecommendationOutcome

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "VendorShield AI"

def test_list_cases():
    response = client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Benchmark case seeded
    apex = next((c for c in data if c["case_reference"] == "INV-2026-8841"), None)
    assert apex is not None

def test_create_and_investigate_case():
    # 1. Create Case
    create_resp = client.post(
        "/api/cases",
        data={
            "supplier_name": "Apex Courier",
            "gstin": "07AAAAA0000A1Z5",
            "invoice_number": "INV-TEST-001",
            "total_amount": 482500.00
        }
    )
    assert create_resp.status_code == 201
    case = create_resp.json()
    case_id = case["case_id"]

    # 2. Trigger Investigation
    inv_resp = client.post(f"/api/cases/{case_id}/investigate")
    assert inv_resp.status_code == 200
    updated_case = inv_resp.json()
    assert updated_case["status"] == CaseStatus.READY_FOR_REVIEW.value
    assert updated_case["assessment"]["recommendation"] == RecommendationOutcome.MANUAL_REVIEW.value
    assert "LEGAL_NAME_MISMATCH" in updated_case["assessment"]["reason_codes"]
    assert updated_case["audit_hash_sha256"] is not None

    # 3. Submit Reviewer Sign-Off
    review_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action_id": "temp",
            "case_id": case_id,
            "reviewer_id": "tanmay_lead",
            "action": "APPROVE_WITH_EXCEPTION",
            "rationale": "Verified registered trade name alias offline.",
            "requested_documents": []
        }
    )
    assert review_resp.status_code == 200
    final_case = review_resp.json()
    assert final_case["status"] == CaseStatus.RESOLVED.value
    assert final_case["review"]["reviewer_id"] == "dev_unauthenticated:tanmay_lead"
    assert final_case["review"]["auth_mode"] == "DEV_MODE_UNAUTHENTICATED"

    # 4. Export Audit Report
    report_resp = client.get(f"/api/cases/{case_id}/report")
    assert report_resp.status_code == 200
    assert "VendorShield Due-Diligence Audit Report" in report_resp.text
