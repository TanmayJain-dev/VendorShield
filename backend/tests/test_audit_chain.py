import pytest
import hashlib
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_tamper_evident_audit_trail_chain():
    # 1. Create Case -> creates CASE_CREATED audit event
    create_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Audit Test Corp", "total_amount": 42000.0}
    )
    case_id = create_resp.json()["case_id"]

    # 2. Trigger Investigation -> creates INVESTIGATION_COMPLETED audit event
    client.post(f"/api/cases/{case_id}/investigate")

    # 3. Correct Invoice -> creates INVOICE_FIELDS_CORRECTED audit event
    client.patch(
        f"/api/cases/{case_id}/invoice",
        json={"corrected_total_amount": 43000.0, "correction_notes": "Added freight"}
    )

    # 4. Review Decision -> creates REVIEW_DECISION_RECORDED audit event
    client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action_id": "act_rev",
            "case_id": case_id,
            "reviewer_id": "auditor_1",
            "action": "APPROVE",
            "rationale": "All documentation reconciled."
        }
    )

    # 5. Fetch audit trail
    trail_resp = client.get(f"/api/cases/{case_id}/audit-trail")
    assert trail_resp.status_code == 200
    events = trail_resp.json()
    assert len(events) >= 4

    # Verify cryptographic hash chain integrity
    for i in range(len(events)):
        curr = events[i]
        if i == 0:
            assert curr["prev_hash"] == "0" * 64
        else:
            prev = events[i - 1]
            assert curr["prev_hash"] == prev["event_hash"]
        assert len(curr["event_hash"]) == 64
