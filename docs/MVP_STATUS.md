# VendorShield AI — Real-Invoice MVP Status & Execution Log

**Current Branch:** `mvp/real-invoices`  
**Base:** `origin/main` / `pre-mvp-main`  
**Execution Mode:** Autonomous Phase-by-Phase Real-Data MVP Engineering  

---

## 1. Execution Log & Verification Baseline

### Baseline Verification (Phase 0)
* **Backend Pytest Baseline:** 78 passed, 0 failed.
* **Frontend TypeScript Baseline:** Clean (0 errors).

---

### Phase A (P0): Fix Verified Defects
* **Commit:** `66b6ba7`
* **Defects Remediated:**
  - Removed Mod-36 checksum bypass in `gstin_validator.py`.
  - Replaced simulated orchestrator fixture defaults with explicit `UNAVAILABLE` evidence (`NO_PROVIDER_CONFIGURED`).
  - Added `is_demo` flag to `Case`, `CaseSummary`, and `CaseModel`. Opt-in demo seeding via `SEED_DEMO_DATA=true`.
  - Parser no longer fabricates 18% GST on unitemized invoices; sets `arithmetic_valid=None` and `arithmetic_notes="ARITHMETIC_UNVERIFIED"`.
  - Fixed `forensic_engine.py` missing `ExtractionStatus` import preventing HTTP 500 crashes.
  - Standardized repository documentation on `pnpm`.
* **Pytest:** 85 passed, 0 failed.

---

### Phase B (P0): Layered Extraction Pipeline
* **Commit:** `29c5e19`
* **Features Implemented:**
  - `qr_einvoice.py`: Decodes JWT e-invoice payloads via PyMuPDF/OpenCV; extracts inner claims; checks signature against `IRP_PUBLIC_KEY_PEM`.
  - `text_layer.py`: Disambiguates supplier vs buyer GSTINs by relative section positions and labels; extracts amounts and masked bank accounts.
  - `llm_extractor.py`: Multimodal adapter for Gemini and Anthropic with temperature 0, strict JSON schema, bank account masking, and zero-cost `LLM_PROVIDER=none` fallback.
  - `merge.py`: Precedence `QR > LLM > REGEX`; tags fields with source and confidence; flags `CONFLICT` and `EXTRACTION_CONFLICT` on discrepancies.
  - `pipeline.py`: Orchestrates multi-layer invoice extraction for PDFs and images.
  - File persistence: Saves uploaded files under `UPLOAD_DIR/<case_id>/<sha256>.<ext>` and adds `GET /api/cases/{case_id}/file`.
* **Pytest:** 95 passed, 0 failed.

---

### Phase C (P0): Real Checks & Pluggable Providers
* **Commit:** `e362c09`
* **Features Implemented:**
  - Deterministic checks added to `DeterministicRuleEngine`: `BUYER_GSTIN_MISMATCH`, `TAX_TYPE_STATE_MISMATCH`, `PAN_FORMAT_INVALID`, `INVOICE_NUMBER_FORMAT_INVALID`, `FUTURE_INVOICE_DATE`, `ITC_TIME_BAR_WARNING`, `EINVOICE_QR_MISMATCH` (BLOCK), `LINE_ITEM_ARITHMETIC_MISMATCH`.
  - Pluggable Registry Providers (`CompositeRegistryProvider`):
    - `ManualEntryProvider`: Reviewer-attested portal details (`SourceMode.MANUAL`).
    - `HttpKycProvider`: Configurable HTTP KYC vendor endpoint with field mapping.
    - `TinyFishProvider`: Web research agent automation for public portal lookup.
    - `DemoProvider`: Isolated synthetic fixtures only when `DEMO_MODE=True` and `case.is_demo=True`.
    - Fails closed to `UNAVAILABLE` when no provider is active.
  - `IfscProvider`: Queries `https://ifsc.razorpay.com/<IFSC>`, caches in SQLite `ifsc_cache` table (30-day TTL), strictly preserves `BANK_OWNERSHIP_UNVERIFIED`.
  - `AssessmentService`: Unified verdict engine; added `explain_verdict` producing `why_this_verdict` and `what_would_change_it`.
  - Endpoints: `POST /api/cases/{case_id}/evidence/gstin` and `GET /api/cases/{case_id}/explain`.
* **Pytest:** 105 passed, 0 failed.

---

### Phase D (P0): Minimal Real Auth & Audit Verification
* **Commit:** `cc949d2`
* **Features Implemented:**
  - `security.py`: Token-based user registry via `USERS_JSON`, server-derived identity, `require_reviewer_role` enforcement, in-memory `TokenRateLimiter`.
  - Updated `review.py`: Uses server-derived user ID and role, rejecting spoofed client values.
  - `CaseRepository.verify_audit_chain(db, case_id)` recomputes cryptographic SHA-256 hash chains across audit events and endpoint `GET /api/cases/{case_id}/audit/verify`.
  - Updated `frontend/src/lib/api.ts`: Attaches `Authorization: Bearer <token>` from `sessionStorage`, handles 401s, exports `submitManualGstinEvidence`, `explainVerdict`, `verifyAuditChain`, and `getCaseFileUrl`.
* **Pytest:** 111 passed, 0 failed.

---

### Phase E (P0): Frontend for Real Flow
* **Commit:** `ff12a42`
* **Features Implemented:**
  - `/upload`: Real file upload is primary; supports drag & drop and multi-file batch upload; removed prefilled "Apex Courier" defaults; collapsed demo presets into drawer with `DEMO DATA` badge.
  - `/cases/[id]`: Side-by-side extraction review step (left = original PDF/image viewer, right = structured claims with provenance chips `QR`, `LLM`, `REGEX`, `MANUAL`, confidence %, and inline edit; primary CTA **"Confirm & run checks"**).
  - Evidence panel: `UNAVAILABLE` rendered in neutral grey (never red); added **"Add GST registry details"** form with button copying GSTIN and direct link to official GST Search Taxpayer portal.
  - Verdict card: Score labelled **"Policy index (heuristic)"** (0-100); displays `why_this_verdict` and `what_would_change_it` from `api.explainVerdict`; ITC exposure card labelled illustrative estimation.
  - `/queue`: Filters (status, demo on/off toggle), search by vendor / invoice no / GSTIN / Case ID, CSV export button, `DEMO DATA` badge on synthetic cases.
  - `/`: Removed uncalibrated marketing claims; captioned Apex / Specter sections as "Illustrative Example (Demo Data)"; respected `prefers-reduced-motion` in 3D hero.
  - Navigation bar: Added role indicator pill and token configuration modal.
* **Frontend Build:** 7/7 routes compiled cleanly (`pnpm build`).

---

### Phase F (P1): GSTR-2B Reconciliation & Invoice Matching
* **Commit:** `01abaee`
* **Features Implemented:**
  - `gstr2b_parser.py`: Tolerantly parses official GST Portal GSTR-2B JSON return file; extracts B2B section, supplier GSTIN (`ctin`), invoice number (`inum`), date (`dt`), gross value (`val`), taxable value (`txval`), taxes, and ITC availability flag (`itcavl`).
  - `gstr2b_entries` table: Stores imported records in persistent database with upsert semantics.
  - Rules added to `DeterministicRuleEngine`:
    - `ITC_NOT_IN_GSTR2B`: Invoice missing from imported GSTR-2B return → **MEDIUM Severity** (payment hold advice).
    - `GSTR2B_VALUE_MISMATCH`: Gross invoice total contradicts GSTR-2B filed value by > ₹2.00 → **HIGH Severity**.
    - `GSTR2B_ITC_NOT_AVAILABLE`: Supplier flagged ITC Available = 'No' → **MEDIUM Severity**.
  - Endpoints: `POST /api/gstr2b/import`, `GET /api/gstr2b/entries`, `GET /api/gstr2b/unmatched`, and `GET /api/gstr2b/match/{case_id}`.
  - Frontend: GSTR-2B Return drawer on `/queue` (import JSON file, view unclaimed return rows); GSTR-2B filing status chip on case dossier.
* **Pytest:** 118 passed, 0 failed.

---

### Phase G (P1): Test Corpus, Eval Harness & Honest Documentation
* **Features Implemented:**
  - `scripts/make_sample_invoices.py`: Generates 13 synthetic invoice PDFs with checksum-valid GSTINs and matching `.expected.json` files covering intra-state, inter-state IGST, tampered total, wrong buyer GSTIN, wrong tax type, invalid checksum, duplicate pair, invoice reuse with different total, missing GSTIN, scanned image PDF, matching e-invoice QR, and conflicting e-invoice QR.
  - `scripts/eval_extraction.py`: Evaluates layered extraction accuracy over any folder of invoice PDFs with `.expected.json`. Benchmark result: **89.2% overall field accuracy** across 130 evaluated field facts (Supplier GSTIN: 100%, Buyer GSTIN: 100%, Invoice Number: 92.3%, Taxable Base: 92.3%, IGST: 100%).
  - `test_phase_g_corpus_e2e.py`: End-to-end API tests for invoice upload → review → evidence → verdict → sign-off → audit verification.
  - CI Workflow (`.github/workflows/ci.yml`): Runs backend `pytest -q`, frontend `pnpm tsc --noEmit && pnpm build`, and `server-health-check` booting server from `.env.example` and querying `/health`.
  - Documentation: Created `docs/DATA_SOURCES.md`, `docs/DEMO_SCRIPT.md`, and updated `README.md` and `docs/MVP_STATUS.md`.
* **Pytest:** 122 passed, 0 failed.

---

## 2. Capabilities: Real vs. Demo vs. Experimental vs. Roadmap

| Capability | Real (Production Ready) | Demo / Attested | Experimental | Roadmap |
| :--- | :---: | :---: | :---: | :---: |
| **PDF & Image File Intake** | ✅ Native PDF, PNG, JPG | — | — | Bulk ZIP intake |
| **e-Invoice QR Code JWT Decoding** | ✅ PyMuPDF + OpenCV | — | — | NIC IRP live public key sync |
| **PDF Text Layer Regex Extraction** | ✅ PyMuPDF + Regex | — | — | LayoutLM / Table transformers |
| **Multimodal LLM Extraction** | ✅ Gemini 1.5 / Claude / None | — | — | Local quantized SLM (Ollama) |
| **Deterministic Mod-36 GSTIN Checksum** | ✅ Official algorithm | — | — | — |
| **Invoice Arithmetic Validation** | ✅ Multi-rate tax, CGST+SGST, IGST | — | — | Multi-currency invoices |
| **Public Portal GSTIN Verification** | — | ✅ Manual attestation (`services.gst.gov.in`) | 🔬 TinyFish browser agent | Paid GSP direct API integration |
| **Bank IFSC Code Lookup** | ✅ Razorpay API + 30-day SQLite cache | — | — | Penny-drop bank ownership API |
| **GSTR-2B Return Reconciliation** | ✅ JSON parser & invoice matching | — | — | Direct GSTN API auto-sync |
| **Cryptographic Audit Trail** | ✅ SHA-256 hash-chain verification | — | — | RFC 3161 TSA timestamping |
| **Reviewer Identity & RBAC** | ✅ Token auth (`USERS_JSON`) + role checks | — | — | Enterprise SAML / OIDC SSO |
| **5-Vector Forensic Topology Radar** | — | — | 🔬 Heuristic projection | Calibrated statistical model |
| **ITC Statutory Exposure Calculation** | — | — | 🔬 Sec 16(2)(c) illustrative projection | Formal tax liability calculator |

---

## 3. UNVERIFIED AGAINST REAL DATA (Honest Disclosure for Mentors)

To maintain academic and professional integrity at HackIIITD Esya '26, the team explicitly discloses the following items that have been verified on synthetic/benchmark datasets but require validation against production accounts payable data:

1. **GSTR-2B JSON Parser:** Verified against synthetic B2B JSON structures adhering to official GSTN schema specifications. Must be tested against a live downloaded production GSTR-2B file from an operating enterprise to confirm handling of optional edge-case fields (e.g., SEZ supplies, amended invoices `b2ba`, reverse charge rows).
2. **Scanned / Mobile Photo OCR Quality:** When native text layers and QR codes are absent, extraction relies on OCR/LLM. Extremely low-light, skewed, or blurred physical mobile phone photos will require user verification and correction via the inline **"Correct Claims"** workflow.
3. **Forensic Vector Risk Scores:** The 5-vector forensic radar scores (Shell Contagion, Collocation Ghost Hub, Pop-up Velocity) are deterministic mathematical heuristics designed for prioritization. They are **not statistically calibrated fraud probabilities**.
4. **Bank Account Ownership:** IFSC verification validates bank routing and branch details, but does not verify account holder name. Accounts payable teams must continue requiring cancelled cheque verification or penny-drop before payment release.

---

## 4. Next 3 Steps for the Team with Real Data

1. **Drop in 10 Real Redacted Invoices:** Drop 10–20 real (redacted) vendor invoices into `data/sample_invoices/` and run `python scripts/eval_extraction.py data/sample_invoices` to measure actual real-world field extraction accuracy for the hackathon judges.
2. **Test with One Real GSTR-2B Download:** Download one real quarterly/monthly GSTR-2B JSON statement from an active GSTIN, import it via the UI (`/queue` → GSTR-2B Returns), and verify that supplier invoices reconcile cleanly.
3. **Practice the 5-Minute Demo Script:** Practice the 5-minute live demonstration outlined in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md), demonstrating real invoice upload, fail-closed behavior, portal attestation, and cryptographic audit verification.
