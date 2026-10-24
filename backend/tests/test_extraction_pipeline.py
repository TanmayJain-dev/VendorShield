import io
import json
import base64
import pytest
import httpx
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from app.schemas.enums import ExtractionStatus
from app.services.extraction.qr_einvoice import extract_qr_einvoice, _decode_jwt_payload_lenient
from app.services.extraction.text_layer import extract_text_layer, extract_text_from_pdf, disambiguate_gstins
from app.services.extraction.llm_extractor import GeminiExtractor, AnthropicExtractor, NoneExtractor
from app.services.extraction.merge import merge_extractions
from app.services.extraction.pipeline import extract_invoice

def create_synthetic_pdf(
    supplier_gstin="07AAAAA0000A1Z4",
    buyer_gstin="27ABCDE1234F1Z5",
    invoice_number="INV-2026-001",
    total_amount=11800.0,
    include_qr=True,
    qr_payload=None
) -> bytes:
    """Creates an in-memory synthetic invoice PDF with optional QR code."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    
    # Header & supplier details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "Apex Global Logistics Pvt Ltd")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, f"GSTIN: {supplier_gstin}")
    c.drawString(50, 720, "123 Commercial Plaza, Connaught Place, New Delhi 110001")
    
    # Invoice metadata
    c.drawString(350, 750, f"Tax Invoice No: {invoice_number}")
    c.drawString(350, 735, "Invoice Date: 2026-04-15")
    
    # Buyer details
    c.drawString(50, 670, "Bill To: TechCorp Solutions Ltd")
    c.drawString(50, 655, f"Buyer GSTIN: {buyer_gstin}")
    c.drawString(50, 640, "456 Silicon Park, Mumbai, Maharashtra 400001")
    
    # Financials
    taxable = total_amount / 1.18
    igst = total_amount - taxable
    c.drawString(50, 580, f"Taxable Value: INR {taxable:.2f}")
    c.drawString(50, 565, f"IGST: INR {igst:.2f}")
    c.drawString(50, 550, f"Grand Total: INR {total_amount:.2f}")
    
    # Bank Details
    c.drawString(50, 500, "Bank: HDFC Bank")
    c.drawString(50, 485, "A/C: 987654321012")
    c.drawString(50, 470, "IFSC: HDFC0000128")
    
    # Optional QR code
    if include_qr:
        if not qr_payload:
            claims = {
                "data": json.dumps({
                    "SellerGstin": supplier_gstin,
                    "BuyerGstin": buyer_gstin,
                    "DocNo": invoice_number,
                    "DocDt": "15/04/2026",
                    "TotInvVal": total_amount,
                    "Irn": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
                })
            }
            hdr = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
            pld = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
            sig = base64.urlsafe_b64encode(b"fakesig").decode().rstrip("=")
            qr_payload = f"{hdr}.{pld}.{sig}"
            
        qr_widget = QrCodeWidget(qr_payload)
        qr_widget.barBorder = 3
        bounds = qr_widget.getBounds()
        w = bounds[2] - bounds[0]
        h = bounds[3] - bounds[1]
        size = 160
        d = Drawing(size, size, transform=[size/w, 0, 0, size/h, 0, 0])
        d.add(qr_widget)
        renderPDF.draw(d, c, 380, 520)
        
    c.save()
    buf.seek(0)
    return buf.getvalue()


def test_qr_extraction_present():
    pdf_bytes = create_synthetic_pdf(include_qr=True)
    res = extract_qr_einvoice(pdf_bytes, is_pdf=True)
    assert res.found is True
    assert res.is_jwt is True
    assert res.qr_signature_status == "UNVERIFIED"
    assert res.extracted_fields["supplier_gstin"] == "07AAAAA0000A1Z4"
    assert res.extracted_fields["buyer_gstin"] == "27ABCDE1234F1Z5"
    assert res.extracted_fields["invoice_number"] == "INV-2026-001"
    assert res.extracted_fields["total_amount"] == 11800.0


def test_qr_extraction_absent():
    pdf_bytes = create_synthetic_pdf(include_qr=False)
    res = extract_qr_einvoice(pdf_bytes, is_pdf=True)
    assert res.found is False
    assert res.extracted_fields == {}


def test_text_layer_gstin_disambiguation():
    pdf_bytes = create_synthetic_pdf(include_qr=False)
    text, is_scanned, ocr_msg, errors = extract_text_from_pdf(pdf_bytes)
    assert not is_scanned
    sup_gstin, buy_gstin = disambiguate_gstins(text)
    assert sup_gstin == "07AAAAA0000A1Z4"
    assert buy_gstin == "27ABCDE1234F1Z5"


def test_text_layer_extraction_fields():
    pdf_bytes = create_synthetic_pdf(include_qr=False)
    text, is_scanned, ocr_msg, errors = extract_text_from_pdf(pdf_bytes)
    res = extract_text_layer(text)
    assert res.extracted_fields.get("supplier_gstin") == "07AAAAA0000A1Z4"
    assert res.extracted_fields.get("buyer_gstin") == "27ABCDE1234F1Z5"
    assert res.extracted_fields.get("invoice_number") == "INV-2026-001"
    assert res.extracted_fields.get("total_amount") == 11800.0
    assert res.extracted_fields.get("bank_account_masked") == "XXXX-XXXX-1012"
    assert res.extracted_fields.get("ifsc_code") == "HDFC0000128"


@pytest.mark.asyncio
async def test_gemini_extractor_mock():
    mock_llm_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "supplier_name": "Apex Global Logistics",
                                "supplier_gstin": "07AAAAA0000A1Z4",
                                "invoice_number": "INV-2026-001",
                                "total_amount": 11800.0,
                                "bank_account_last4": "1012"
                            })
                        }
                    ]
                }
            }
        ]
    }

    def handler(request: httpx.Request):
        return httpx.Response(200, json=mock_llm_response)

    extractor = GeminiExtractor(api_key="mock_key", model="gemini-1.5-flash")
    extractor.transport = httpx.MockTransport(handler)

    res = await extractor.extract(b"fake_pdf_content", "application/pdf")
    assert res["supplier_gstin"] == "07AAAAA0000A1Z4"
    assert res["invoice_number"] == "INV-2026-001"
    assert res["total_amount"] == 11800.0
    assert res["bank_account_last4"] == "1012"


@pytest.mark.asyncio
async def test_anthropic_extractor_mock():
    mock_anthropic_response = {
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "supplier_name": "Apex Global Logistics",
                    "supplier_gstin": "07AAAAA0000A1Z4",
                    "invoice_number": "INV-2026-001",
                    "total_amount": 11800.0
                })
            }
        ]
    }

    def handler(request: httpx.Request):
        return httpx.Response(200, json=mock_anthropic_response)

    extractor = AnthropicExtractor(api_key="mock_key", model="claude-3-5-sonnet-20241022")
    extractor.transport = httpx.MockTransport(handler)

    res = await extractor.extract(b"fake_pdf_content", "application/pdf")
    assert res["supplier_gstin"] == "07AAAAA0000A1Z4"
    assert res["invoice_number"] == "INV-2026-001"


@pytest.mark.asyncio
async def test_llm_provider_none():
    extractor = NoneExtractor()
    res = await extractor.extract(b"fake_content", "application/pdf")
    assert res == {}


@pytest.mark.asyncio
async def test_llm_invalid_json_fallback():
    def handler(request: httpx.Request):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "THIS IS NOT JSON"}]}}]})

    extractor = GeminiExtractor(api_key="mock_key")
    extractor.transport = httpx.MockTransport(handler)
    res = await extractor.extract(b"fake_pdf_content", "application/pdf")
    assert res == {}


@pytest.mark.asyncio
async def test_extraction_conflict_detection():
    # PDF with printed total 11800.0, but QR with 99999.0
    claims = {
        "data": json.dumps({
            "SellerGstin": "07AAAAA0000A1Z4",
            "DocNo": "INV-2026-001",
            "TotInvVal": 99999.0  # Conflicting total
        })
    }
    hdr = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
    pld = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(b"sig").decode().rstrip("=")
    conflicting_jwt = f"{hdr}.{pld}.{sig}"
    
    pdf_bytes = create_synthetic_pdf(total_amount=11800.0, include_qr=True, qr_payload=conflicting_jwt)
    
    claim = await extract_invoice(pdf_bytes, filename="test_invoice.pdf")
    
    # Expect conflict on total_amount
    assert len(claim.extraction_conflicts) > 0
    conflict = next((c for c in claim.extraction_conflicts if c["field"] == "total_amount"), None)
    assert conflict is not None
    assert conflict["value_a"] == 99999.0
    assert conflict["value_b"] == 11800.0
    assert claim.extraction_metadata["total_amount"].status == ExtractionStatus.CONFLICT
    assert any("EXTRACTION_CONFLICT" in w for w in claim.parsing_warnings)


@pytest.mark.asyncio
async def test_end_to_end_layered_pipeline():
    pdf_bytes = create_synthetic_pdf(include_qr=True)
    claim = await extract_invoice(pdf_bytes, filename="invoice.pdf")
    
    assert claim.gstin == "07AAAAA0000A1Z4"
    assert claim.buyer_gstin == "27ABCDE1234F1Z5"
    assert claim.invoice_number == "INV-2026-001"
    assert claim.total_amount == 11800.0
    assert claim.gstin_format_valid is True
    assert claim.extraction_metadata["supplier_gstin"].status == ExtractionStatus.EXTRACTED_QR
    assert claim.extraction_metadata["supplier_gstin"].source == "QR"
