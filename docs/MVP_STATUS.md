# VendorShield AI — Real-Invoice MVP Status & Execution Log

**Current Branch:** `mvp/real-invoices`  
**Base:** `origin/feat/ui-enterprise-dashboard`  
**Execution Mode:** Autonomous Phase-by-Phase Execution  

---

## 1. Execution Log

### Baseline Verification (Phase 0)
* **Backend Pytest Baseline:**
```
collected 78 items
======================= 78 passed, 2 warnings in 4.10s ========================
```
* **Frontend TypeScript Baseline:**
```
cd frontend && npx pnpm tsc --noEmit
Exit code: 0 (Clean)
```

### Phase A (P0): Fix Verified Defects (Completed)
* **Key Fixes Implemented:**
  - **A1:** Fixed missing `ExtractionStatus` import in `forensic_engine.py` preventing NameError HTTP 500 crashes during investigation.
  - **A2:** Removed hardcoded Mod-36 checksum bypass (`07AAAAA0000A1Z5`) in `gstin_validator.py`. Verified zero 15-char string backdoors. Created `backend/app/services/validators/gstin_tools.py` with `compute_check_char` and `make_gstin`. Replaced invalid fixtures across `sample_data/` and tests with verified Mod-36 GSTINs (Apex: `07AAAAA0000A1Z4`, Specter: `07BSPCT9999C1ZE`, QuickPrint: `07AQKPS1111Q1ZH`).
  - **A3:** Simulated orchestrator no longer returns Apex Courier fixtures for real vendors; returns explicit `UNAVAILABLE` evidence (`NO_PROVIDER_CONFIGURED`) failing closed to `MANUAL_REVIEW` unless `is_demo=True` or `DEMO_MODE=true`.
  - **A4:** Registry outages (timeouts, HTTP 500, captcha) ignore `UNAVAILABLE` evidence when reconciling GST status; only emit `GST_STATUS_INACTIVE_CONFIRMED` for verified cancelled/suspended statuses; composition status recognized as active.
  - **A5:** Refactored `TinyFishClient` in `client.py` with support for `output_schema`, async polling, and resilient fallback to `UNAVAILABLE`. Experimental hops 2-4 kept behind `ENABLE_EXPERIMENTAL_FORENSICS=false`.
  - **A6:** Created unified `AssessmentService.assess(case)` in `backend/app/services/rules/assessment_service.py` ensuring core deterministic rules govern all assessments across intake, investigation, and invoice corrections.
  - **A7:** Fixed `CORS_ORIGINS` pydantic-settings parsing in `config.py` using `Union[List[str], str]`, verified clean `uvicorn app.main:app` startup from `.env.example`, aligned `RULES_VERSION=2.0.0`, separated dev requirements into `requirements-dev.txt`.
  - **A8:** Added `is_demo` flag to `Case`, `CaseSummary`, and `CaseModel`. Removed automatic seeding on every request in `list_cases` and `create_case`; seeding is opt-in via `SEED_DEMO_DATA=true`.
  - **A9:** Manual intake and parser no longer fabricate 18% GST; manual intake sets `taxable_amount=0.0`, `cgst=0.0`, `sgst=0.0`, `igst=0.0`, `arithmetic_valid=None`, and `arithmetic_notes="ARITHMETIC_UNVERIFIED"`.
  - **A10:** Pre-ingestion validation aligned for Phase B layered pipeline.
  - **A12:** Configurable statutory parameters in `itc_calculator.py` with Finance Act 2024 Sec 74A and Sec 50(3) advisory notes; low-risk liability correctly returns ₹0.00.
  - **A13:** Standardized docs on `pnpm`, standardized Apex Global Logistics naming, aligned test counts.

* **Backend Pytest Output (Phase A):**
```
collected 85 items
======================= 85 passed, 2 warnings in 4.80s ========================
```

* **Frontend Build Output (Phase A):**
```
$ next build
   ▲ Next.js 15.5.28

   Creating an optimized production build ...
 ✓ Compiled successfully in 9.3s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (7/7)
 ✓ Generating static pages (7/7)
   Finalizing page optimization ...
   Collecting build traces ...
Route (app)                                 Size  First Load JS
┌ ○ /                                    15.9 kB         123 kB
├ ○ /_not-found                            988 B         103 kB
├ ƒ /cases/[id]                          9.82 kB         112 kB
├ ○ /dashboard                             245 B         112 kB
├ ○ /queue                                 162 B         112 kB
└ ○ /upload                               4.5 kB         111 kB
```

### Phase B (P0): Layered Extraction Pipeline (Completed)
* **Key Enhancements Implemented:**
  - **B1: E-Invoice QR Decoder (`qr_einvoice.py`):** Renders PDF pages at 200 DPI via PyMuPDF or decodes images directly with OpenCV. Decodes JWT e-invoice payloads, maps inner claims (`SellerGstin`, `BuyerGstin`, `DocNo`, `DocDt`, `TotInvVal`, `Irn`), labels signature `UNVERIFIED` (or verifies if `IRP_PUBLIC_KEY_PEM` is provided).
  - **B2: Text & Regex Layer (`text_layer.py`):** PyMuPDF text and bounding boxes. Disambiguates supplier vs buyer GSTINs based on explicit labels and relative page sections. Suppresses header defaults ("Tax Invoice") for supplier name.
  - **B3: Agnostic Multimodal LLM Extractor (`llm_extractor.py`):** Abstract provider interface with adapters for Gemini and Anthropic over `httpx`. Strict JSON schema with temperature 0, bank account masking (requesting last 4 digits only), and zero-cost `LLM_PROVIDER=none` fallback.
  - **B4: Merge & Provenance Engine (`merge.py`):** Precedence `QR > LLM > REGEX`. Tags every field with `ExtractionStatus` (`EXTRACTED_QR`, `EXTRACTED_LLM`, `EXTRACTED_REGEX`) and confidence. Detects material disagreements (GSTIN, invoice number, date, total, tax), marks status `CONFLICT`, and emits `EXTRACTION_CONFLICT` warnings.
  - **B5: Unified Pipeline Orchestration (`pipeline.py`):** Routes PDF and image uploads through the multi-layer pipeline.
  - **B6: Raw File Persistence & Endpoint:** Persists uploads under `UPLOAD_DIR/<case_id>/<sha256>.<ext>` and provides `GET /api/cases/{case_id}/file` for side-by-side verification.
  - **B7: Enum & Type Parity:** Extended `ExtractionStatus` with `EXTRACTED_QR`, `EXTRACTED_LLM`, `EXTRACTED_REGEX`, `CONFLICT` and `SourceMode` in backend and frontend `api.ts`.

* **Backend Pytest Output (Phase B):**
```
collected 95 items
======================= 95 passed, 2 warnings in 10.22s =======================
```

* **Frontend Build Output (Phase B):**
```
$ next build
   ▲ Next.js 15.5.28

   Creating an optimized production build ...
 ✓ Compiled successfully in 3.8s
   Linting and checking validity of types ...
   Collecting page data ...
 ✓ Generating static pages (7/7)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    15.9 kB         123 kB
├ ○ /_not-found                            988 B         103 kB
├ ƒ /cases/[id]                          9.82 kB         112 kB
├ ○ /dashboard                             245 B         112 kB
├ ○ /queue                                 162 B         112 kB
└ ○ /upload                               4.5 kB         111 kB
```

### Phase C (P0): Real Checks & Pluggable Providers (Completed)
* **Key Enhancements Implemented:**
  - **C1: Deterministic Real Checks:**
    - `BUYER_GSTIN_MISMATCH` & `BUYER_GSTIN_MISSING`: Verified against configured `BUYER_GSTINS` list. Prevents invalid claims in third-party entity names.
    - `TAX_TYPE_STATE_MISMATCH`: Verifies supplier state code (GSTIN chars 1-2) against buyer state code / place of supply. Flags intra-state IGST or inter-state CGST/SGST.
    - `PAN_FORMAT_INVALID`: Checks 4th character of embedded PAN against valid legal entity holder types (`CPHFATBLJG`).
    - `INVOICE_NUMBER_FORMAT_INVALID`: Validates invoice number length (<= 16) and character restrictions under GST Rule 46.
    - `FUTURE_INVOICE_DATE`: Rejects future invoice dates.
    - `ITC_TIME_BAR_WARNING`: Flags invoices beyond Section 16(4) cutoff (30 Nov following FY end) for CA review.
    - `EINVOICE_QR_MISMATCH`: Hard gate (BLOCK) if cryptographically verified QR code contradicts printed totals.
    - `LINE_ITEM_ARITHMETIC_MISMATCH`: Compares line item sums with taxable and gross totals.
  - **C2: Pluggable Registry Providers (`backend/app/services/providers/`):**
    - `ManualEntryProvider`: Reviewer submits public portal taxpayer details (`POST /api/cases/{id}/evidence/gstin`). Stored as authoritative evidence (`source_mode=MANUAL`).
    - `HttpKycProvider`: Configurable HTTP endpoint via `GSTIN_API_URL_TEMPLATE`, auth headers, and `GSTIN_API_FIELD_MAP`.
    - `TinyFishProvider`: Web research agent automation for public portal lookup.
    - `DemoProvider`: Isolated synthetic fixtures for demo mode only.
    - `CompositeRegistryProvider`: Sequences through `GSTIN_PROVIDERS` and fails closed to `UNAVAILABLE`.
  - **C3: IFSC Verification (`ifsc_provider.py`):**
    - Open RBI dataset via `https://ifsc.razorpay.com/<IFSC>`.
    - 30-day SQLite caching (`ifsc_cache` table) with TTL expiration.
    - Strict truth invariant: never claims account ownership; flags `BANK_OWNERSHIP_UNVERIFIED`.
  - **C4: Verdict Semantics & Explanation (`AssessmentService`):**
    - Single source of truth: PASS requires valid GSTIN, verified arithmetic, valid tax state alignment, active GST status, and no conflicts.
    - Added `GET /api/cases/{id}/explain` returning plain-English `why_this_verdict` and `what_would_change_it` action items.

* **Backend Pytest Output (Phase C):**
```
collected 105 items
====================== 105 passed, 2 warnings in 11.30s =======================
```

---

## 2. Phase Implementation Checklist

- [x] **Phase A (P0): Fix Verified Defects**
- [x] **Phase B (P0): Layered Extraction Pipeline (QR + Text + LLM with Provenance)**
- [x] **Phase C (P0): Real Checks, Pluggable Providers (Manual, HttpKyc, TinyFish), IFSC & Verdict Semantics**
- [ ] **Phase D (P0): Minimal Real Auth (Bearer Tokens, Roles, Server-Derived Identity, Audit Verify)**
- [ ] **Phase E (P0): Frontend for Real Flow (Review Step, Provenance Chips, Manual Evidence Form, Honest Claims)**
- [ ] **Phase F (P1): GSTR-2B Reconciliation & Invoice Matching**
- [ ] **Phase G (P1): Test Corpus (12 PDFs), Eval Harness, CI, Honest Documentation**
- [ ] **Phase H (P2): Additional Polish (if time permits)**

---

## 3. UNVERIFIED AGAINST REAL DATA

The following components interact with external standards or services where real test responses cannot be obtained directly in this sandbox environment. Tolerant, defensive implementations are used:

1. **GSTR-2B JSON Schema Variations:** The GSTR-2B parser expects standard B2B invoice fields (`ctin`, `inum`, `dt`, `val`, `txval`, tax splits, itc availability). Tolerant key mapping is implemented, but exact schema variations must be validated against real downloaded JSON exports from the GST portal.
2. **IRP Signed E-Invoice QR Payload Signature:** E-invoice QR JWT payloads are decoded and parsed leniently without relying on unverified signatures unless `IRP_PUBLIC_KEY_PEM` is explicitly configured.
3. **External GST Portal Captcha & Anti-Bot Behavior:** Live TinyFish automation on the public GST portal (`services.gst.gov.in`) may encounter captchas or IP rate limits; handled defensively by marking evidence `UNAVAILABLE`.
