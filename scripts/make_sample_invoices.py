import os
import sys
import json
import base64
import argparse
from io import BytesIO

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF

from backend.app.services.validators.gstin_validator import calculate_gstin_checksum

def make_valid_gstin(state_code: str, pan: str, entity_num: str = "1") -> str:
    partial = f"{state_code}{pan}{entity_num}Z"
    chk = calculate_gstin_checksum(partial)
    return f"{partial}{chk}"

def draw_invoice_pdf(
    pdf_path: str,
    supplier_name: str,
    supplier_gstin: str,
    supplier_addr: str,
    buyer_name: str,
    buyer_gstin: str,
    buyer_addr: str,
    invoice_num: str,
    invoice_date: str,
    items: list,
    taxable_amt: float,
    cgst: float,
    sgst: float,
    igst: float,
    total_amt: float,
    qr_jwt: str = None,
    is_scanned_image: bool = False
):
    buffer = BytesIO()
    c = canvas.Canvas(buffer if is_scanned_image else pdf_path, pagesize=letter)
    width, height = letter

    # Header & Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "TAX INVOICE")

    c.setFont("Helvetica", 9)
    c.drawString(50, height - 65, "(Issued under Section 31 of CGST Act, 2017)")

    # Supplier Details Box
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 95, "SUPPLIER (Issued By):")
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 110, supplier_name)
    c.drawString(50, height - 123, supplier_addr)
    if supplier_gstin:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, height - 136, f"GSTIN: {supplier_gstin}")

    # Invoice Metadata (Right Box)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(360, height - 95, f"Invoice No: {invoice_num}")
    c.drawString(360, height - 110, f"Invoice Date: {invoice_date}")
    c.drawString(360, height - 125, "Place of Supply: Delhi (07)")

    # Buyer Details
    c.line(50, height - 145, width - 50, height - 145)
    c.drawString(50, height - 160, "BILLED TO (Recipient):")
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 173, buyer_name)
    c.drawString(50, height - 186, buyer_addr)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, height - 199, f"Buyer GSTIN: {buyer_gstin}")

    # Line Items Table
    c.line(50, height - 215, width - 50, height - 215)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, height - 230, "Sr.")
    c.drawString(85, height - 230, "Item Description")
    c.drawString(300, height - 230, "Qty")
    c.drawString(360, height - 230, "Rate")
    c.drawString(460, height - 230, "Amount (INR)")
    c.line(50, height - 235, width - 50, height - 235)

    c.setFont("Helvetica", 9)
    y = height - 250
    for idx, (desc, qty, rate, amt) in enumerate(items, 1):
        c.drawString(55, y, str(idx))
        c.drawString(85, y, desc)
        c.drawString(305, y, str(qty))
        c.drawString(360, y, f"{rate:.2f}")
        c.drawString(460, y, f"{amt:.2f}")
        y -= 20

    c.line(50, y - 5, width - 50, y - 5)

    # Financial Totals Box
    tot_y = y - 25
    c.setFont("Helvetica", 9)
    c.drawString(320, tot_y, "Taxable Amount:")
    c.drawRightString(width - 55, tot_y, f"INR {taxable_amt:,.2f}")

    if cgst > 0:
        tot_y -= 15
        c.drawString(320, tot_y, "CGST (9%):")
        c.drawRightString(width - 55, tot_y, f"INR {cgst:,.2f}")
    if sgst > 0:
        tot_y -= 15
        c.drawString(320, tot_y, "SGST (9%):")
        c.drawRightString(width - 55, tot_y, f"INR {sgst:,.2f}")
    if igst > 0:
        tot_y -= 15
        c.drawString(320, tot_y, "IGST (18%):")
        c.drawRightString(width - 55, tot_y, f"INR {igst:,.2f}")

    tot_y -= 18
    c.line(310, tot_y + 12, width - 50, tot_y + 12)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(320, tot_y, "Total Invoice Amount:")
    c.drawRightString(width - 55, tot_y, f"INR {total_amt:,.2f}")

    # Bank Account & Signature
    c.setFont("Helvetica", 8)
    c.drawString(50, 90, "Bank: HDFC Bank Ltd | Branch: Okhla Phase II")
    c.drawString(50, 78, "A/C No: XXXX-XXXX-9921 | IFSC: HDFC0000128")
    c.drawString(50, 66, "Terms: Payment due within 30 days.")

    # QR Code if provided
    if qr_jwt:
        qr = QrCodeWidget(qr_jwt)
        qr.barBorder = 3
        b_box = qr.getBounds()
        w_b = b_box[2] - b_box[0]
        h_b = b_box[3] - b_box[1]
        d = Drawing(160, 160, transform=[160 / w_b, 0, 0, 160 / h_b, 0, 0])
        d.add(qr)
        renderPDF.draw(d, c, 50, 120)
        c.setFont("Helvetica", 8)
        c.drawString(50, 110, "B2B e-Invoice QR Code (IRP Payload)")

    c.showPage()
    c.save()

    if is_scanned_image:
        # Convert first page of buffer to image via PyMuPDF and embed as scanned PDF
        import fitz
        doc = fitz.open(stream=buffer.getvalue(), filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("jpeg")
        doc.close()

        # Build clean image-only PDF
        c_img = canvas.Canvas(pdf_path, pagesize=letter)
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(BytesIO(img_bytes))
        c_img.drawImage(img_reader, 0, 0, width, height)
        c_img.showPage()
        c_img.save()

def make_jwt(payload: dict) -> str:
    header = {"alg": "RS256", "typ": "JWT"}
    p1 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p2 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    p3 = base64.urlsafe_b64encode(b"synthetic_irp_signature_bytes_mock").decode().rstrip("=")
    return f"{p1}.{p2}.{p3}"

def generate_corpus(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    buyer_delhi = make_valid_gstin("07", "ABCDE1234F")
    buyer_mumbai = make_valid_gstin("27", "XYZAB5678C")

    supplier_delhi = make_valid_gstin("07", "AABCB1234F")
    supplier_mumbai = make_valid_gstin("27", "AABCB9876K")

    corpus_specs = [
        # 1. Clean intra-state
        {
            "id": "01_clean_intra_state",
            "supp_name": "Apex Global Logistics Pvt Ltd",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Okhla Phase-II, New Delhi - 110020",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0001",
            "inv_date": "2026-10-15",
            "items": [("Freight Logistics Services", 1, 100000.0, 100000.0)],
            "taxable": 100000.0,
            "cgst": 9000.0,
            "sgst": 9000.0,
            "igst": 0.0,
            "total": 118000.0,
            "expected_verdict": "PASS"
        },
        # 2. Clean inter-state IGST
        {
            "id": "02_clean_inter_state_igst",
            "supp_name": "Maharashtra Industrial Logistics Ltd",
            "supp_gstin": supplier_mumbai,
            "supp_addr": "Nariman Point, Mumbai - 400021",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0002",
            "inv_date": "2026-10-16",
            "items": [("Inter-State Haulage Support", 1, 50000.0, 50000.0)],
            "taxable": 50000.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 9000.0,
            "total": 59000.0,
            "expected_verdict": "PASS"
        },
        # 3. Tampered Total (Arithmetic Mismatch)
        {
            "id": "03_tampered_total",
            "supp_name": "Delta Office Systems Pvt Ltd",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Nehru Place, New Delhi - 110019",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0003",
            "inv_date": "2026-10-17",
            "items": [("Office Computing Equipment", 1, 100000.0, 100000.0)],
            "taxable": 100000.0,
            "cgst": 9000.0,
            "sgst": 9000.0,
            "igst": 0.0,
            "total": 150000.0,  # Deliberately tampered: items sum to 118,000
            "expected_verdict": "MANUAL_REVIEW"
        },
        # 4. Wrong Buyer GSTIN
        {
            "id": "04_wrong_buyer_gstin",
            "supp_name": "Apex Global Logistics Pvt Ltd",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Okhla Phase-II, New Delhi - 110020",
            "buyer_name": "Third Party Enterprise Ltd",
            "buyer_gstin": "06ZZZZZ9999Z1Z5",  # Unknown Haryana GSTIN
            "buyer_addr": "Sector 18, Gurgaon - 122001",
            "inv_no": "INV-2026-0004",
            "inv_date": "2026-10-18",
            "items": [("Logistics Transport Delivery", 1, 10000.0, 10000.0)],
            "taxable": 10000.0,
            "cgst": 900.0,
            "sgst": 900.0,
            "igst": 0.0,
            "total": 11800.0,
            "expected_verdict": "MANUAL_REVIEW"
        },
        # 5. Wrong Tax Type (Intra-state charging IGST)
        {
            "id": "05_wrong_tax_type",
            "supp_name": "Apex Global Logistics Pvt Ltd",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Okhla Phase-II, New Delhi - 110020",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0005",
            "inv_date": "2026-10-19",
            "items": [("Same State Delivery Service", 1, 20000.0, 20000.0)],
            "taxable": 20000.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 3600.0,  # Wrong tax type for intra-state
            "total": 23600.0,
            "expected_verdict": "MANUAL_REVIEW"
        },
        # 6. Invalid GSTIN Checksum
        {
            "id": "06_invalid_gstin_checksum",
            "supp_name": "Bogus Supply Traders",
            "supp_gstin": "07AABCB1234F1Z0",  # Checksum digit 0 is invalid
            "supp_addr": "Chandni Chowk, Delhi - 110006",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0006",
            "inv_date": "2026-10-20",
            "items": [("Miscellaneous Supplies", 1, 10000.0, 10000.0)],
            "taxable": 10000.0,
            "cgst": 900.0,
            "sgst": 900.0,
            "igst": 0.0,
            "total": 11800.0,
            "expected_verdict": "BLOCK"
        },
        # 7. Duplicate Pair A
        {
            "id": "07_duplicate_pair_a",
            "supp_name": "Precision Engineering Works",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Mayapuri Industrial Area, New Delhi - 110064",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-DUP-77",
            "inv_date": "2026-10-21",
            "items": [("Custom Steel Fasteners", 1, 40000.0, 40000.0)],
            "taxable": 40000.0,
            "cgst": 3600.0,
            "sgst": 3600.0,
            "igst": 0.0,
            "total": 47200.0,
            "expected_verdict": "PASS"
        },
        # 8. Duplicate Pair B (Exact duplicate invoice)
        {
            "id": "08_duplicate_pair_b",
            "supp_name": "Precision Engineering Works",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Mayapuri Industrial Area, New Delhi - 110064",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-DUP-77",
            "inv_date": "2026-10-21",
            "items": [("Custom Steel Fasteners", 1, 40000.0, 40000.0)],
            "taxable": 40000.0,
            "cgst": 3600.0,
            "sgst": 3600.0,
            "igst": 0.0,
            "total": 47200.0,
            "expected_verdict": "MANUAL_REVIEW"
        },
        # 9. Same Number Different Amount (Suspect Invoice Reuse)
        {
            "id": "09_reuse_different_amount",
            "supp_name": "Precision Engineering Works",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Mayapuri Industrial Area, New Delhi - 110064",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-DUP-77",
            "inv_date": "2026-10-22",
            "items": [("Additional Tooling Reissue", 1, 80000.0, 80000.0)],
            "taxable": 80000.0,
            "cgst": 7200.0,
            "sgst": 7200.0,
            "igst": 0.0,
            "total": 94400.0,
            "expected_verdict": "MANUAL_REVIEW"
        },
        # 10. Missing GSTIN
        {
            "id": "10_missing_gstin",
            "supp_name": "Unregistered Local Vendors",
            "supp_gstin": "",  # Missing
            "supp_addr": "Old Delhi Market, Delhi - 110006",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0010",
            "inv_date": "2026-10-22",
            "items": [("Packing Materials", 1, 15000.0, 15000.0)],
            "taxable": 15000.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 0.0,
            "total": 15000.0,
            "expected_verdict": "MANUAL_REVIEW"
        },
        # 11. Scanned Image-Only Invoice
        {
            "id": "11_scanned_image_invoice",
            "supp_name": "Sunrise Hardware Stores",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Kashmere Gate, Delhi - 110006",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0011",
            "inv_date": "2026-10-23",
            "items": [("Workshop Maintenance Spares", 1, 30000.0, 30000.0)],
            "taxable": 30000.0,
            "cgst": 2700.0,
            "sgst": 2700.0,
            "igst": 0.0,
            "total": 35400.0,
            "expected_verdict": "MANUAL_REVIEW",
            "is_scanned": True
        },
        # 12. Matching e-Invoice QR
        {
            "id": "12_matching_einvoice_qr",
            "supp_name": "Zenith Cloud & Networks Ltd",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Barakhamba Road, New Delhi - 110001",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0012",
            "inv_date": "2026-10-23",
            "items": [("Enterprise Cloud Networking", 1, 200000.0, 200000.0)],
            "taxable": 200000.0,
            "cgst": 18000.0,
            "sgst": 18000.0,
            "igst": 0.0,
            "total": 236000.0,
            "qr_data": {
                "SellerGstin": supplier_delhi,
                "BuyerGstin": buyer_delhi,
                "DocNo": "INV-2026-0012",
                "DocDt": "23/10/2026",
                "TotInvVal": 236000.0,
                "Irn": "67a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8"
            },
            "expected_verdict": "PASS"
        },
        # 13. Conflicting e-Invoice QR (Tampering Warning)
        {
            "id": "13_conflicting_einvoice_qr",
            "supp_name": "Zenith Cloud & Networks Ltd",
            "supp_gstin": supplier_delhi,
            "supp_addr": "Barakhamba Road, New Delhi - 110001",
            "buyer_name": "Acme Industries India Ltd",
            "buyer_gstin": buyer_delhi,
            "buyer_addr": "Connaught Place, New Delhi - 110001",
            "inv_no": "INV-2026-0013",
            "inv_date": "2026-10-24",
            "items": [("Enterprise Cloud Networking", 1, 200000.0, 200000.0)],
            "taxable": 200000.0,
            "cgst": 18000.0,
            "sgst": 18000.0,
            "igst": 0.0,
            "total": 236000.0,  # Printed total is 236,000
            "qr_data": {
                "SellerGstin": supplier_delhi,
                "BuyerGstin": buyer_delhi,
                "DocNo": "INV-2026-0013",
                "DocDt": "24/10/2026",
                "TotInvVal": 150000.0,  # Contradicts printed total
                "Irn": "99a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f799"
            },
            "expected_verdict": "BLOCK"
        }
    ]

    for spec in corpus_specs:
        pdf_path = os.path.join(output_dir, f"{spec['id']}.pdf")
        json_path = os.path.join(output_dir, f"{spec['id']}.expected.json")

        qr_jwt = None
        if "qr_data" in spec:
            qr_jwt = make_jwt(spec["qr_data"])

        draw_invoice_pdf(
            pdf_path=pdf_path,
            supplier_name=spec["supp_name"],
            supplier_gstin=spec["supp_gstin"],
            supplier_addr=spec["supp_addr"],
            buyer_name=spec["buyer_name"],
            buyer_gstin=spec["buyer_gstin"],
            buyer_addr=spec["buyer_addr"],
            invoice_num=spec["inv_no"],
            invoice_date=spec["inv_date"],
            items=spec["items"],
            taxable_amt=spec["taxable"],
            cgst=spec["cgst"],
            sgst=spec["sgst"],
            igst=spec["igst"],
            total_amt=spec["total"],
            qr_jwt=qr_jwt,
            is_scanned_image=spec.get("is_scanned", False)
        )

        expected_meta = {
            "filename": f"{spec['id']}.pdf",
            "supplier_name": spec["supp_name"],
            "gstin": spec["supp_gstin"] or None,
            "buyer_gstin": spec["buyer_gstin"],
            "invoice_number": spec["inv_no"],
            "invoice_date": spec["inv_date"],
            "total_amount": spec["total"],
            "taxable_amount": spec["taxable"],
            "cgst": spec["cgst"],
            "sgst": spec["sgst"],
            "igst": spec["igst"],
            "expected_verdict": spec["expected_verdict"]
        }

        with open(json_path, "w", encoding="utf-8") as f_json:
            json.dump(expected_meta, f_json, indent=2)

    print(f"Successfully generated {len(corpus_specs)} synthetic invoice PDFs and .expected.json pairs in '{output_dir}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic vendor invoice corpus for VendorShield evaluation.")
    parser.add_argument("--output", default="data/sample_invoices", help="Output directory")
    args = parser.parse_args()
    generate_corpus(args.output)
