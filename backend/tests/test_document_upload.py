import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from backend.app.main import app

client = TestClient(app)


def _create_synthetic_invoice_image(format: str = "PNG") -> bytes:
    """Generates an image of a standard invoice for OCR verification."""
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    lines = [
        "TAX INVOICE",
        "Supplier: Havells India Ltd",
        "Supplier GSTIN: 07AAACH0828A1ZE",
        "Invoice No: INV-2026-9901",
        "Invoice Date: 2026-10-20",
        "Place of Supply: Delhi (07)",
        "Description: Heavy Duty Copper Cable 16sqmm",
        "Qty: 100",
        "Unit Price: 4225.00",
        "Taxable Amount: 422500.00",
        "CGST 9%: 38025.00",
        "SGST 9%: 38025.00",
        "Total Amount: 498550.00",
        "Bank Account No: 98765432109921",
        "IFSC Code: HDFC0000123",
        "e-Way Bill No: 123456789012"
    ]
    
    y = 30
    for line in lines:
        draw.text((40, y), line, fill=(0, 0, 0))
        y += 32
        
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def _create_synthetic_invoice_pdf() -> bytes:
    """Generates a digital PDF invoice using PyMuPDF."""
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
        
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    content = (
        "TAX INVOICE\n"
        "Supplier: Apex Courier Pvt Ltd\n"
        "Supplier GSTIN: 07AAAAA0000A1Z5\n"
        "Invoice No: INV-2026-8841\n"
        "Invoice Date: 2026-10-15\n"
        "Taxable Amount: 408898.31\n"
        "CGST: 36800.85\n"
        "SGST: 36800.85\n"
        "Total Amount: 482500.00\n"
        "Bank Account: 98765432101234\n"
        "IFSC Code: HDFC0000123\n"
        "e-Way Bill: 987654321099\n"
    )
    page.insert_text((50, 80), content, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_parse_document_pdf():
    pdf_bytes = _create_synthetic_invoice_pdf()
    resp = client.post(
        "/api/cases/parse-document",
        files={"file": ("invoice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["supplier_name"] == "Apex Courier Pvt Ltd"
    assert data["gstin"] == "07AAAAA0000A1Z5"
    assert data["gstin_format_valid"] is True
    assert data["invoice_number"] == "INV-2026-8841"
    assert abs(data["total_amount"] - 482500.00) < 1.0
    assert abs(data["base_amount"] - 408898.31) < 1.0
    assert len(data["raw_text_preview"]) > 20
    assert data["extraction_method"] in ["PYMUPDF_TEXT", "RAPIDOCR_ONNX_300DPI"]


def test_parse_document_image_png():
    img_bytes = _create_synthetic_invoice_image("PNG")
    resp = client.post(
        "/api/cases/parse-document",
        files={"file": ("sample_invoice.png", io.BytesIO(img_bytes), "image/png")}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["extraction_method"] in ["RAPIDOCR_ONNX_300DPI", "OCR_RASTER_300DPI"]
    assert data["is_scanned_image"] is True
    # Verify OCR extracted key invoice elements
    assert "07AAACH0828A1ZE" in data["raw_text_preview"] or data["gstin"] == "07AAACH0828A1ZE"
    assert data["total_amount"] > 0


def test_parse_document_image_jpeg():
    img_bytes = _create_synthetic_invoice_image("JPEG")
    resp = client.post(
        "/api/cases/parse-document",
        files={"file": ("sample invoice.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["extraction_method"] in ["RAPIDOCR_ONNX_300DPI", "OCR_RASTER_300DPI"]
    assert data["total_amount"] > 0


def test_create_case_and_investigate_from_image_upload():
    img_bytes = _create_synthetic_invoice_image("PNG")
    # 1. Intake creation with image file
    create_resp = client.post(
        "/api/cases",
        files={"file": ("sample_invoice.png", io.BytesIO(img_bytes), "image/png")},
        data={
            "supplier_name": "Havells India Ltd",
            "gstin": "07AAACH0828A1ZE",
            "invoice_number": "INV-2026-9901",
            "total_amount": 498550.00
        }
    )
    assert create_resp.status_code == 201, create_resp.text
    case = create_resp.json()
    case_id = case["case_id"]
    assert case["invoice"]["supplier_name"] == "Havells India Ltd"
    assert case["invoice"]["gstin"] == "07AAACH0828A1ZE"

    # 2. Trigger 4-Hop Forensic Investigation
    inv_resp = client.post(f"/api/cases/{case_id}/investigate")
    assert inv_resp.status_code == 200, inv_resp.text
    investigated_case = inv_resp.json()
    assert investigated_case["status"] == "READY_FOR_REVIEW"
    assert investigated_case["assessment"] is not None
    assert len(investigated_case["evidence_items"]) >= 1
