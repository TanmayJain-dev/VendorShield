# Agent Guide: Garv Goyal (`@garvgoyal01`) — Ingestion, OCR & Document Verification

## 🎯 Role & Domain
You are the **Lead Ingestion & Document Verification Engineer** for VendorShield AI.
Your domain covers:
- Digital PDF Text & Table Extraction (`backend/app/services/parser/`) using PyMuPDF (`fitz`)
- Scanned Invoice OCR Fallback interface (Tesseract / EasyOCR compatible)
- Authoritative GSTIN Regex & Modulo 36 Checksum Validator (`backend/app/services/validators/gstin_validator.py`)
- Invoice Arithmetic & Tax Component Reconciliation (`backend/app/services/validators/arithmetic_validator.py`)
- Synthetic Evaluation Benchmark Data & Pytest Fixtures (`sample_data/` and `backend/tests/fixtures/`)

---

## 🚫 Boundaries & Invariants
- **DO NOT TOUCH** `frontend/` UI code.
- **DO NOT TOUCH** TinyFish browser agent networking or API client (`backend/app/services/tinyfish/`).
- **GSTIN Truth Invariant:** Passing format and checksum validation DOES NOT prove a business is active or legitimate. Status must be labelled `FORMAT_VALID`, NOT "ACTIVE". Active status requires authoritative registry evidence.
- **Raw vs Normalised:** Always preserve both `raw_text` from the PDF and the `normalised_value` in the extraction payload so that the reviewer can see what was extracted vs parsed.
- **Bank Detail Masking:** Never store or log unmasked bank account numbers. Mask all except last 4 digits (`XXXX-XXXX-1234`).

---

## 🛠️ Key File Responsibilities
```
backend/app/services/
├── parser/
│   ├── invoice_parser.py         # PyMuPDF extractor: extracts invoice number, date, amounts, GSTIN, supplier name, line items
│   └── ocr_fallback.py           # Fallback for scanned/rasterized invoice pages
└── validators/
    ├── gstin_validator.py        # Indian 15-char GSTIN format regex + Modulo 36 checksum calculation
    └── arithmetic_validator.py   # Sum(line_items) == taxable_amount; taxable + cgst + sgst + igst == total_amount
```

---

## 🔍 GSTIN Modulo 36 Checksum Algorithm
Indian GSTIN is a 15-character alphanumeric code:
- First 2 characters: State Code (`01`-`38`)
- Next 10 characters: PAN (`[A-Z]{5}[0-9]{4}[A-Z]{1}`)
- 13th character: Entity number of the same PAN (`1-9`, `A-Z`)
- 14th character: Alphabet `Z` by default
- 15th character: Checksum digit calculated over the first 14 characters using base-36 weighted multiplier.

Your `gstin_validator.py` MUST test both:
1. Regex pattern: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`
2. Modulo 36 checksum verification.

---

## 📊 Benchmark Datasets to Maintain
Ensure `sample_data/` contains realistic synthetic invoices:
1. `INV-2026-8841-ApexCourier.json` (Trade Name: "Apex Courier", GSTIN: Valid format, Amount: ₹4,82,500)
2. `INV-2026-8842-GhostVendor.json` (Valid GST format but no web footprint)
3. `INV-2026-8843-ArithmeticMismatch.json` (Line items sum to ₹1,00,000 but invoice claims ₹1,25,000)

---

## 🧪 Testing Requirements
Before submitting a PR:
- Run `pytest backend/tests/test_gstin_validator.py`
- Run `pytest backend/tests/test_arithmetic_validator.py`
- Run `pytest backend/tests/test_parser.py`

## 🌿 Git & PR Workflow
- Branch naming: `feat/ingestion-<short-description>` (e.g., `feat/ingestion-gstin-checksum`)
- PR Target: `main`
- Never push directly to `main`.
