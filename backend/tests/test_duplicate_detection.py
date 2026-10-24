import pytest
import io
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_exact_file_duplicate_detection():
    # Construct a minimal valid PDF payload
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Invoice 1) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    
    # 1. Upload original file
    file_tuple_1 = ("invoice_orig.pdf", io.BytesIO(pdf_content), "application/pdf")
    resp1 = client.post(
        "/api/cases",
        files={"file": file_tuple_1},
        data={"supplier_name": "Unique Vendor A", "invoice_number": f"INV-DUP-{uuid.uuid4().hex[:6]}"}
    )
    assert resp1.status_code == 201
    case1 = resp1.json()
    assert case1["duplicate_type"] is None

    # 2. Upload identical content under a different filename
    file_tuple_2 = ("invoice_renamed.pdf", io.BytesIO(pdf_content), "application/pdf")
    resp2 = client.post(
        "/api/cases",
        files={"file": file_tuple_2},
        data={"supplier_name": "Unique Vendor A", "invoice_number": f"INV-DUP-{uuid.uuid4().hex[:6]}"}
    )
    assert resp2.status_code == 201
    case2 = resp2.json()
    assert case2["duplicate_type"] == "EXACT_FILE_DUPLICATE"
    assert case2["duplicate_of_case_id"] == case1["case_id"]

def test_repeated_invoice_number_detection():
    vendor = "Delta Alpha Logistics"
    inv_num = f"INV-DELTA-{uuid.uuid4().hex[:6]}"
    
    # 1. Create first intake
    resp1 = client.post(
        "/api/cases",
        data={"supplier_name": vendor, "invoice_number": inv_num, "total_amount": 75000.0}
    )
    assert resp1.status_code == 201
    case1 = resp1.json()

    # 2. Intake with same vendor & same invoice number & same amount -> EXACT_INVOICE_DUPLICATE
    resp2 = client.post(
        "/api/cases",
        data={"supplier_name": vendor, "invoice_number": inv_num, "total_amount": 75000.0}
    )
    assert resp2.status_code == 201
    case2 = resp2.json()
    assert case2["duplicate_type"] == "EXACT_INVOICE_DUPLICATE"
    assert case2["duplicate_of_case_id"] == case1["case_id"]

    # 3. Intake with same vendor & same invoice number but CONFLICTING amount -> SUSPECT_INVOICE_REUSE
    resp3 = client.post(
        "/api/cases",
        data={"supplier_name": vendor, "invoice_number": inv_num, "total_amount": 99999.0}
    )
    assert resp3.status_code == 201
    case3 = resp3.json()
    assert case3["duplicate_type"] == "SUSPECT_INVOICE_REUSE"

def test_legitimate_separate_invoices_no_duplicate():
    vendor = "Omega Supplies"
    inv_num_1 = f"INV-OMEGA-{uuid.uuid4().hex[:6]}"
    inv_num_2 = f"INV-OMEGA-{uuid.uuid4().hex[:6]}"

    resp1 = client.post(
        "/api/cases",
        data={"supplier_name": vendor, "invoice_number": inv_num_1, "total_amount": 10000.0}
    )
    resp2 = client.post(
        "/api/cases",
        data={"supplier_name": vendor, "invoice_number": inv_num_2, "total_amount": 10000.0}
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp2.json()["duplicate_type"] is None
