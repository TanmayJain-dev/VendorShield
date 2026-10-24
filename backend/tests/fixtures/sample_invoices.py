try:
    import pymupdf as fitz
except ImportError:
    import fitz


def create_test_invoice_pdf(
    invoice_number: str = "INV-2026-8841",
    invoice_date: str = "2026-10-15",
    supplier_name: str = "Apex Courier",
    legal_name: str = "Apex Global Logistics Pvt Ltd",
    gstin: str = "07AAAAA0000A1Z4",
    billing_address: str = "Plot 42, Okhla Industrial Area, Phase-II, New Delhi - 110020",
    account_number: str = "98765432109921",
    ifsc: str = "HDFC0000123",
    items: list = None,
    taxable_amount: float = 408898.31,
    cgst: float = 36800.85,
    sgst: float = 36800.85,
    igst: float = 0.0,
    total_amount: float = 482500.00
) -> bytes:
    """Generates a high-fidelity synthetic tax invoice PDF with text and tabular structure."""
    if items is None:
        items = [
            ("Domestic Air Express Freight & Dispatch (Batch A)", 10.0, 25000.00, 250000.00),
            ("Intercity Surface Courier & Fulfilment Operations", 5.0, 31779.66, 158898.31)
        ]

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # Standard A4 size

    # Header
    page.insert_text(fitz.Point(50, 50), "TAX INVOICE", fontsize=18)
    page.insert_text(fitz.Point(50, 75), f"Supplier: {supplier_name}", fontsize=12)
    page.insert_text(fitz.Point(50, 92), f"Legal Name: {legal_name}", fontsize=10)
    page.insert_text(fitz.Point(50, 107), f"Supplier GSTIN: {gstin}", fontsize=10)
    page.insert_text(fitz.Point(50, 122), f"Address: {billing_address}", fontsize=10)

    # Invoice Details
    page.insert_text(fitz.Point(380, 50), f"Invoice No: {invoice_number}", fontsize=11)
    page.insert_text(fitz.Point(380, 68), f"Invoice Date: {invoice_date}", fontsize=11)
    page.insert_text(fitz.Point(380, 86), "Place of Supply: Delhi (07)", fontsize=10)

    # Line Item Table Header
    y = 160
    page.draw_line(fitz.Point(50, y - 15), fitz.Point(545, y - 15))
    page.insert_text(fitz.Point(55, y), "Description", fontsize=10)
    page.insert_text(fitz.Point(320, y), "Qty", fontsize=10)
    page.insert_text(fitz.Point(380, y), "Unit Price", fontsize=10)
    page.insert_text(fitz.Point(470, y), "Amount", fontsize=10)
    page.draw_line(fitz.Point(50, y + 8), fitz.Point(545, y + 8))

    # Line Item Rows
    y += 25
    for desc, qty, price, total in items:
        page.insert_text(fitz.Point(55, y), desc[:40], fontsize=9)
        page.insert_text(fitz.Point(320, y), f"{qty:.1f}", fontsize=9)
        page.insert_text(fitz.Point(380, y), f"{price:.2f}", fontsize=9)
        page.insert_text(fitz.Point(470, y), f"{total:.2f}", fontsize=9)
        y += 20

    page.draw_line(fitz.Point(50, y), fitz.Point(545, y))
    y += 20

    # Totals Section
    page.insert_text(fitz.Point(320, y), f"Taxable Amount: INR {taxable_amount:.2f}", fontsize=10)
    y += 18
    if cgst > 0 or sgst > 0:
        page.insert_text(fitz.Point(320, y), f"CGST @ 9%: INR {cgst:.2f}", fontsize=10)
        y += 18
        page.insert_text(fitz.Point(320, y), f"SGST @ 9%: INR {sgst:.2f}", fontsize=10)
        y += 18
    if igst > 0:
        page.insert_text(fitz.Point(320, y), f"IGST @ 18%: INR {igst:.2f}", fontsize=10)
        y += 18

    page.insert_text(fitz.Point(320, y), f"Grand Total: INR {total_amount:.2f}", fontsize=12)

    # Bank Payment Instructions
    y = 350
    page.insert_text(fitz.Point(50, y), "Bank Payment Details:", fontsize=11)
    y += 18
    page.insert_text(fitz.Point(50, y), f"Bank Account No: {account_number}", fontsize=10)
    y += 18
    page.insert_text(fitz.Point(50, y), f"IFSC Code: {ifsc}", fontsize=10)
    y += 18
    page.insert_text(fitz.Point(50, y), "Bank Name: HDFC Bank Ltd, New Delhi", fontsize=10)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_scanned_test_invoice_pdf(
    invoice_number: str = "INV-SCAN-9001",
    supplier_name: str = "Raster Scans Logistics",
    gstin: str = "07AAAAA0000A1Z4"
) -> bytes:
    """
    Creates a pure raster image PDF (scanned invoice with no digital text stream).
    This tests the OCR fallback pipeline.
    """
    # 1. Create source doc with text
    source_pdf = create_test_invoice_pdf(
        invoice_number=invoice_number,
        supplier_name=supplier_name,
        gstin=gstin
    )
    src_doc = fitz.open(stream=source_pdf, filetype="pdf")
    src_page = src_doc[0]
    pix = src_page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    src_doc.close()

    # 2. Embed into a new document as an image page without digital text
    dest_doc = fitz.open()
    rect = fitz.Rect(0, 0, 595, 842)
    new_page = dest_doc.new_page(width=595, height=842)
    new_page.insert_image(rect, stream=img_bytes)
    
    result_bytes = dest_doc.tobytes()
    dest_doc.close()
    return result_bytes
