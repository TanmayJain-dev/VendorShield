import os
import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import init_db

client = TestClient(app)

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_invoices")

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_corpus_exists():
    assert os.path.isdir(CORPUS_DIR), f"Corpus directory {CORPUS_DIR} must exist"
    pdfs = [f for f in os.listdir(CORPUS_DIR) if f.endswith(".pdf")]
    assert len(pdfs) >= 12, f"Expected at least 12 corpus PDFs, found {len(pdfs)}"

def test_clean_intra_state_e2e():
    pdf_path = os.path.join(CORPUS_DIR, "01_clean_intra_state.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("01_clean_intra_state.pdf missing")

    with open(pdf_path, "rb") as f:
        content = f.read()

    # 1. Upload Invoice
    res = client.post(
        "/api/cases",
        files={"file": ("01_clean_intra_state.pdf", content, "application/pdf")},
        headers={"Authorization": "Bearer priya-analyst-token-2026"}
    )
    assert res.status_code == 201
    case = res.json()
    case_id = case["case_id"]
    assert case["status"] == "PARSED"
    assert case["invoice"]["gstin"] == "07AABCB1234F1ZA"

    # 2. Trigger Investigation without external network (fails closed to MANUAL_REVIEW due to missing registry evidence)
    inv_res = client.post(
        f"/api/cases/{case_id}/investigate",
        headers={"Authorization": "Bearer priya-analyst-token-2026"}
    )
    assert inv_res.status_code == 200
    case_inv = inv_res.json()
    assert case_inv["assessment"]["recommendation"] in ["MANUAL_REVIEW", "PASS"]

    # 3. Add Authoritative Manual GSTIN Evidence (Active portal lookup)
    gst_res = client.post(
        f"/api/cases/{case_id}/evidence/gstin",
        json={
            "gstin": "07AABCB1234F1ZA",
            "legal_name": "Apex Global Logistics Pvt Ltd",
            "trade_name": "Apex Global Logistics",
            "status": "Active",
            "registration_date": "2021-04-01",
            "taxpayer_type": "Regular",
            "source_url": "https://services.gst.gov.in/services/searchtp"
        },
        headers={"Authorization": "Bearer priya-analyst-token-2026"}
    )
    assert gst_res.status_code == 200
    case_active = gst_res.json()
    assert case_active["assessment"]["recommendation"] in ["PASS", "MANUAL_REVIEW"]

    # 4. Reviewer Sign-Off
    rev_res = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "action": "APPROVE_WITH_EXCEPTION",
            "rationale": "Verified clean invoice, matching registered legal name and active GST status on public portal."
        },
        headers={"Authorization": "Bearer garv-reviewer-token-2026"}
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "RESOLVED"

    # 5. Cryptographic SHA-256 Audit Chain Verification
    audit_res = client.get(
        f"/api/cases/{case_id}/audit/verify",
        headers={"Authorization": "Bearer garv-reviewer-token-2026"}
    )
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["chain_valid"] is True
    assert audit_data["total_events"] >= 3

def test_tampered_total_fails_closed():
    pdf_path = os.path.join(CORPUS_DIR, "03_tampered_total.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("03_tampered_total.pdf missing")

    with open(pdf_path, "rb") as f:
        content = f.read()

    res = client.post(
        "/api/cases",
        files={"file": ("03_tampered_total.pdf", content, "application/pdf")},
        headers={"Authorization": "Bearer priya-analyst-token-2026"}
    )
    assert res.status_code == 201
    case_id = res.json()["case_id"]

    inv_res = client.post(
        f"/api/cases/{case_id}/investigate",
        headers={"Authorization": "Bearer priya-analyst-token-2026"}
    )
    assert inv_res.status_code == 200
    assessment = inv_res.json()["assessment"]
    assert assessment["recommendation"] == "MANUAL_REVIEW"
    assert "INVOICE_ARITHMETIC_MISMATCH" in assessment["reason_codes"]

def test_invalid_gstin_checksum_blocks():
    pdf_path = os.path.join(CORPUS_DIR, "06_invalid_gstin_checksum.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("06_invalid_gstin_checksum.pdf missing")

    with open(pdf_path, "rb") as f:
        content = f.read()

    res = client.post(
        "/api/cases",
        files={"file": ("06_invalid_gstin_checksum.pdf", content, "application/pdf")},
        headers={"Authorization": "Bearer priya-analyst-token-2026"}
    )
    assert res.status_code == 201
    case_id = res.json()["case_id"]

    inv_res = client.post(
        f"/api/cases/{case_id}/investigate",
        headers={"Authorization": "Bearer priya-analyst-token-2026"}
    )
    assert inv_res.status_code == 200
    assessment = inv_res.json()["assessment"]
    assert assessment["recommendation"] == "BLOCK"
    assert "GSTIN_FORMAT_INVALID" in assessment["hard_gates_triggered"]
