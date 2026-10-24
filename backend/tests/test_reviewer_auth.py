import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import Settings
from backend.app.schemas.enums import CaseStatus

client = TestClient(app)

def _create_and_investigate_case() -> str:
    case_resp = client.post(
        "/api/cases",
        data={"supplier_name": "Auth Test Vendor", "total_amount": 50000.0}
    )
    assert case_resp.status_code == 201
    case_id = case_resp.json()["case_id"]
    inv_resp = client.post(f"/api/cases/{case_id}/investigate")
    assert inv_resp.status_code == 200
    return case_id

def test_authenticated_review_ignores_caller_spoofed_identity():
    """
    When caller provides a valid Bearer token, the server uses authoritative identity.
    Caller-supplied reviewer_id / reviewer_role are strictly ignored and cannot spoof identity.
    """
    case_id = _create_and_investigate_case()

    rev_resp = client.post(
        f"/api/cases/{case_id}/review",
        headers={"Authorization": "Bearer vendorshield-dev-review-token-2026"},
        json={
            "action": "APPROVE",
            "rationale": "Legitimate verified approval by authorized compliance officer.",
            "reviewer_id": "malicious_spoofed_admin",
            "reviewer_role": "cfo"
        }
    )
    assert rev_resp.status_code == 200
    case_data = rev_resp.json()
    review = case_data["review"]
    assert review is not None
    # Server strictly overrides with authenticated token identity
    assert review["reviewer_id"] == "authorized_ap_reviewer"
    assert review["reviewer_role"] == "compliance_officer"
    assert review["auth_mode"] == "PRESHARED_DEV_TOKEN_AUTHENTICATED"

def test_invalid_bearer_token_rejected_with_401():
    """
    If a caller passes an invalid Bearer token, it must be rejected with 401.
    It must NOT fall through to dev unauthenticated mode.
    """
    case_id = _create_and_investigate_case()

    rev_resp = client.post(
        f"/api/cases/{case_id}/review",
        headers={"Authorization": "Bearer invalid-tampered-token-999"},
        json={
            "action": "APPROVE",
            "rationale": "Attempting signoff with invalid token."
        }
    )
    assert rev_resp.status_code == 401
    assert "Invalid reviewer authorization token" in rev_resp.text

def test_invalid_x_reviewer_token_header_rejected_with_401():
    """
    If a caller passes an invalid X-Reviewer-Token, it must be rejected with 401.
    """
    case_id = _create_and_investigate_case()

    rev_resp = client.post(
        f"/api/cases/{case_id}/review",
        headers={"X-Reviewer-Token": "wrong-token-abc"},
        json={
            "action": "APPROVE",
            "rationale": "Attempting signoff with wrong header token."
        }
    )
    assert rev_resp.status_code == 401
    assert "Invalid reviewer authorization token" in rev_resp.text

def test_dev_mode_labels_self_reported_identity_as_unauthenticated():
    """
    In dev mode without tokens, self-reported identities are explicitly tagged
    with 'dev_unauthenticated:' prefix and auth_mode is DEV_MODE_UNAUTHENTICATED.
    """
    case_id = _create_and_investigate_case()

    rev_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action": "APPROVE",
            "rationale": "Review conducted under local development mode.",
            "reviewer_id": "tanmay_analyst",
            "reviewer_role": "senior_analyst"
        }
    )
    assert rev_resp.status_code == 200
    review = rev_resp.json()["review"]
    assert review["reviewer_id"] == "dev_unauthenticated:tanmay_analyst"
    assert review["reviewer_role"] == "dev_unauthenticated:senior_analyst"
    assert review["auth_mode"] == "DEV_MODE_UNAUTHENTICATED"

def test_production_mode_rejects_unsafe_defaults_at_startup():
    """
    Production mode validation:
    1. Rejects REVIEWER_DEV_MODE = True in production.
    2. Rejects default DEV_REVIEWER_TOKEN in production.
    3. Accepts secure production configuration with non-default token and dev mode disabled.
    """
    # 1. Dev mode True in production -> rejected
    with pytest.raises(ValueError, match="REVIEWER_DEV_MODE cannot be enabled in production"):
        Settings(ENVIRONMENT="production", REVIEWER_DEV_MODE=True)

    # 2. Default dev token in production -> rejected
    with pytest.raises(ValueError, match="Production mode rejects the default dev reviewer token"):
        Settings(
            ENVIRONMENT="production",
            REVIEWER_DEV_MODE=False,
            DEV_REVIEWER_TOKEN="vendorshield-dev-review-token-2026"
        )

    # 3. Explicit secure configuration -> accepted
    prod_settings = Settings(
        ENVIRONMENT="production",
        REVIEWER_DEV_MODE=False,
        DEV_REVIEWER_TOKEN="prod-secure-token-9f82a17bc6e4d5"
    )
    assert prod_settings.ENVIRONMENT == "production"
    assert prod_settings.REVIEWER_DEV_MODE is False
    assert prod_settings.DEV_REVIEWER_TOKEN == "prod-secure-token-9f82a17bc6e4d5"
