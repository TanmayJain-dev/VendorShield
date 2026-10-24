import pytest
import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings

client = TestClient(app)

def test_reject_disguised_file_invalid_magic_bytes():
    # File named invoice.pdf but containing plaintext executable/script bytes
    fake_content = b"echo 'malicious script' >> /etc/passwd"
    resp = client.post(
        "/api/cases",
        files={"file": ("fake_invoice.pdf", io.BytesIO(fake_content), "application/pdf")},
        data={"supplier_name": "Test Vendor"}
    )
    assert resp.status_code == 400
    assert "does not match PDF" in resp.text

def test_reject_empty_file():
    empty_content = b""
    resp = client.post(
        "/api/cases",
        files={"file": ("empty.pdf", io.BytesIO(empty_content), "application/pdf")},
        data={"supplier_name": "Test Vendor"}
    )
    assert resp.status_code == 400
    assert "empty" in resp.text.lower()

def test_reject_oversized_file():
    # 11MB file exceeds 10MB limit
    oversized = b"%PDF-1.4\n" + (b"0" * (11 * 1024 * 1024))
    resp = client.post(
        "/api/cases",
        files={"file": ("huge.pdf", io.BytesIO(oversized), "application/pdf")},
        data={"supplier_name": "Test Vendor"}
    )
    assert resp.status_code == 400
    assert "exceeds maximum size" in resp.text
