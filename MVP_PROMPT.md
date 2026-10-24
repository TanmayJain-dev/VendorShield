# VendorShield → Real-Invoice MVP — One-Shot Correction Brief for Antigravity

> Drop this file in the repo root as `MVP_PROMPT.md`, then tell Antigravity:
> **"Read MVP_PROMPT.md fully and execute it end to end, phase by phase, committing after each phase. Do not stop to ask questions; where something is ambiguous, pick the safest option, note it in docs/MVP_STATUS.md, and continue."**

---

## 0. Git setup (the human runs this BEFORE starting the agent)

```bash
git fetch origin
git tag pre-mvp-main origin/main                      # safety net
git checkout -b mvp/real-invoices origin/feat/ui-enterprise-dashboard
```

Why this base: `feat/ui-enterprise-dashboard` already contains all of `main` plus the new UI, so it is a strict superset. `feat/ingestion-parser-ocr-verification` is **stale**: its head is an ancestor of `main`, and diffing it against `main` shows ~8,000 deleted lines. Never merge it, never "resolve conflicts" toward it, never cherry-pick from it. Ignore it entirely.

When all phases are done: open a PR `mvp/real-invoices → main`, merge it, close the stale ingestion PR (#1) and delete that branch.

---

## 1. Mission

VendorShield checks supplier invoices before payment (Indian GST context) and returns PASS / MANUAL_REVIEW / BLOCK with evidence and human sign-off. Today it is a convincing **demo that runs on hardcoded fixtures**. Turn it into an **MVP that gives honest, useful answers on real invoice PDFs and photos** an AP person uploads.

### Non-negotiable principles
1. **Never present fixture, simulated or guessed data as real.** Demo data must be visibly labelled `DEMO` everywhere (API field, UI badge, report, audit event) and must never mix into real cases.
2. **Fail closed to MANUAL_REVIEW.** A failed, timed-out or missing lookup means "unknown", never "inactive" and never "clean".
3. **No special cases in validators or rules.** No hardcoded GSTINs, vendor names or invoice numbers in non-test code paths (except inside the clearly isolated demo provider).
4. **Every fact carries provenance:** source, retrieval timestamp, mode (`QR`, `LLM`, `REGEX`, `MANUAL`, `API`, `LIVE_AGENT`, `DEMO`), and who/what produced it.
5. **Do not claim what cannot be verified.** If something cannot be verified against real data in this environment (e.g. exact GSTR-2B JSON field names, e-invoice QR field names, TinyFish behaviour on the GST portal), implement tolerant parsing and record it in `docs/MVP_STATUS.md` under "UNVERIFIED AGAINST REAL DATA".
6. Keep it simple: SQLite stays, no new services, no Docker requirement, no Celery/Redis. Pure Python + the existing Next.js app.
7. Commit after every phase with a clear message. Run the full backend tests and the frontend build after every phase and fix regressions before moving on. Paste real command output into `docs/MVP_STATUS.md`, never summarise from memory.

Priorities: **P0 = must ship**, **P1 = should ship**, **P2 = only if time remains**. Do all P0 before any P1.

---

## 2. PHASE A (P0) — Fix verified defects

Each item lists the evidence found in the audit. Fix it, add a regression test, then move on.

**A1. `ExtractionStatus` is used but never imported in `backend/app/services/rules/forensic_engine.py`** (used inside `_is_inferred`; the import line only brings in `RecommendationOutcome, CheckStatus, SourceMode`). Any invoice with non-empty `extraction_metadata` and `tax_inferred=False` (i.e. every uploaded PDF) raises `NameError` → HTTP 500 on `POST /api/cases/{id}/investigate`. Fix the import. Add a test that parses a real text PDF (generate one with PyMuPDF in the test) and runs the full create → investigate flow through the API.

**A2. Hardcoded checksum backdoor in `gstin_validator.py` (on the UI branch):** `if cleaned == "07AAAAA0000A1Z5": return True, "FORMAT_VALID"`. The real Mod-36 check character for `07AAAAA0000A1Z` is `4`, so `...Z5` is invalid and the code special-cases it so demo data passes. Remove the bypass. Unify all fixtures: `sample_data/*.json` use `...Z4` (valid) but `repository.seed_benchmark_case`, the TinyFish simulation fixtures and the orchestrator fixtures use `...Z5`; also three different vendors share one GSTIN across the sample files. Create `backend/app/services/validators/gstin_tools.py` with `compute_check_char()` and `make_gstin(state, pan)`; give each demo scenario its **own** checksum-valid synthetic GSTIN; add a test that asserts no GSTIN in `sample_data/` or fixtures fails validation and that `validate_gstin_format` has no special cases (grep test for string literals of 15 chars in the validator).

**A3. The simulated orchestrator returns the wrong company's data for any vendor.** In `orchestrator._execute_simulated_multihop`, every vendor whose name does not contain "specter"/"ghost" receives the **Apex Courier "clean" fixture**, so a real vendor gets Apex's legal name → `CRITICAL_NAME_MISMATCH` → BLOCK. Fix: demo fixtures are returned **only** when `DEMO_MODE=true` **and** the case is flagged `is_demo` (set only by the demo-scenario endpoint/UI buttons). For any other case with no configured provider, return an explicit `UNAVAILABLE` evidence item ("No registry provider configured") so the case lands in MANUAL_REVIEW with a clear "add evidence manually" call to action.

**A4. Registry outage is treated as "GST inactive" → false BLOCK.** In `orchestrator`, failed hops produce evidence with `facts={"status": "UNAVAILABLE"}` and `claim_supported` containing "Legal Entity…". In `evidence_reconciler.reconcile`, `gst_evidence` is picked by `"legal" in claim_supported`, then `reg_status="UNAVAILABLE"` is not "active" → `GST_STATUS_INACTIVE_CONFIRMED` → hard gate → BLOCK. Fix: (a) ignore evidence with `source_mode == UNAVAILABLE` when selecting `gst_evidence`; (b) only emit `GST_STATUS_INACTIVE_CONFIRMED` when status ∈ {cancelled, suspended, inactive, "cancelled suspo-moto", …} from non-demo, non-unavailable evidence; any other unrecognised status string → `GST_STATUS_UNKNOWN`. Add tests for: timeout, HTTP 500, captcha-failure text, and a status string like "Active (Composition)".

**A5. TinyFish live client reads fields that TinyFish does not return.** `client.py` and `orchestrator.py` read `extracted_facts` from the response; the documented response has `status` (`COMPLETED|FAILED`), `result` (object|null), `error` (object|null). So `facts` is always `{}` and every live case hits `EVIDENCE_INSUFFICIENT`. The code also uses the synchronous `/v1/automation/run` with a 30 s client timeout, while TinyFish docs say `/run` suits tasks under ~30 s, and chains four hops sequentially. Rework into a single `TinyFishClient` (httpx, `X-API-Key`) that: sends `url`, `goal`, **`output_schema`** (JSON-schema subset), `agent_config.max_steps` and `agent_config.max_duration_seconds`; uses `POST /v1/automation/run-async` then polls `GET /v1/runs/{run_id}` until `COMPLETED|FAILED|CANCELLED` or a deadline; maps `result` (validated against the schema with Pydantic) into evidence `facts`; treats `FAILED`, `error`, schema-invalid results or empty results as `UNAVAILABLE`. Remove the dead duplicate (`TinyFishService`) or make the orchestrator use it. Hops 2–4 currently use **guessed URLs** (`zaubacorp.com/company-directors/<name-slug>`, `nclt.gov.in/case-status`, Google Maps search); move all of this behind `ENABLE_EXPERIMENTAL_FORENSICS=false` (default off), keep it out of the default scoring, and clearly mark every output "EXPERIMENTAL – unverified". Hop 1 (GST portal) may hit a captcha; implement it as an optional provider (see Phase C) and treat captcha/blocked as `UNAVAILABLE`, never as a result.

**A6. Two assessment engines give different answers.** `investigate.py` uses `ForensicRiskEngine` (v2, vectors + ITC + graph) but `PATCH /cases/{id}/invoice` re-assesses with `DeterministicRuleEngine` (v1), silently dropping `forensic_vectors`, `itc_exposure`, `entity_graph` and flipping `ruleset_version`. Create one `AssessmentService.assess(case)` used by create, investigate, patch, manual-evidence and review-prep. The v1 rule engine becomes the **core engine**; forensic vectors are an optional add-on computed only when `ENABLE_EXPERIMENTAL_FORENSICS=true` or the case `is_demo`. The frontend must render correctly when `forensic_vectors`/`itc_exposure`/`entity_graph` are `null`.

**A7. `.env.example` crashes startup.** `CORS_ORIGINS=a,b` with a `List[str]` field makes pydantic-settings try `json.loads` and raise `SettingsError` before any validator runs; the UI branch's `mode="before"` validator does not fix that for `List[str]`. Fix using `Annotated[List[str], NoDecode]` (bump `pydantic-settings>=2.7`) or a string field plus a property. **Acceptance:** `cp .env.example backend/.env` then `uvicorn app.main:app` starts clean (run it and show the output). Also set `RULES_VERSION` consistently (`.env.example` says 1.0.0, config says 2.0.0). Pin versions in `requirements.txt`; move `pytest*` to `requirements-dev.txt`.

**A8. Demo data pollutes the real database.** `list_cases` and `create_case` call `seed_benchmark_case` on every request. Make seeding opt-in: only at startup when `SEED_DEMO_DATA=true`, with `is_demo=true` stored on the case; the real queue hides demo cases unless the "Show demo cases" toggle is on.

**A9. Manual intake fabricates tax data.** In `cases.create_case` (no file), tax is hardcoded as 18% inclusive, `arithmetic_valid=True`. That contradicts the project's own fail-closed rule. Fix: manual intake requires taxable amount and tax lines (or marks them `UNAVAILABLE`), sets `arithmetic_valid=None` (unknown), and never infers 18%. Remove the 18% inference in `parse_invoice_text` as well (keep a warning, set `INFERRED`, never use it in any check or PASS decision).

**A10. Image uploads are accepted then fail.** `_validate_file_upload` allows PNG/JPEG, but `extract_text_from_pdf_bytes` rejects anything without `%PDF-`, so images always produce a parse error. OCR code exists but `pytesseract`, `Pillow`, `easyocr` are not in `requirements.txt`. Also `parse_invoice_pdf` (which merges PDF table extraction) is never called by the API; `create_case` calls `extract_text_from_pdf_bytes` + `parse_invoice_text` directly. Fix in Phase B by routing everything through the new extraction pipeline (images → vision-capable extraction; scanned PDFs → rasterise pages → same path). Do not add heavy OCR dependencies.

**A11. API is unauthenticated except sign-off.** Case create/list/get/patch/investigate have no auth; reviewer dev mode is on by default and the dev token is committed in `config.py` and `.env.example`. See Phase D for the minimal fix.

**A12. ITC calculator legal parameters need correction and honest labelling** (`itc_calculator.py`). It cites Sec 74 with 100% penalty and Sec 50 at 18%. As amended by the Finance Act 2024, Sec 74A governs demands from FY 2024-25 onward (Sec 73/74 for earlier periods), and Sec 50(3) uses a higher rate (24% p.a. under Rule 14) for ITC wrongly availed **and** utilised. Treat these as **configurable constants with a visible "verify with a Chartered Accountant" note**; relabel `itc_clawback_probability` in the UI/docs as "ITC risk score (heuristic, not a probability)" and `total_financial_liability_inr` as "illustrative exposure". Never show it as a statutory demand. Only compute exposure from real extracted GST amounts.

**A13. Docs contradict the code.** README says 75+ tests, PROJECT_GUIDE says 33; run command in PROJECT_GUIDE (`uvicorn backend.app.main:app` from `backend/`) is wrong; README says `npm install` while CI uses `pnpm --frozen-lockfile`; the landing page says "Apex Express Logistics" while the backend says "Apex Global Logistics". Standardise on `pnpm`, the real test count, one run command, one name.

Commit: `fix(core): P0 defects A1-A13`.

---

## 3. PHASE B (P0) — Extraction pipeline that works on real invoices

Replace regex-only parsing with a layered pipeline in `backend/app/services/extraction/`:

1. **`qr_einvoice.py`** — For each PDF page (render with PyMuPDF at ~200 DPI) or image, try to find and decode a QR code with `opencv-python-headless` (`cv2.QRCodeDetector` / `detectAndDecodeMulti`). If the payload is a JWT (3 dot-separated base64url parts), decode the claims **without trusting them**; the inner `data` claim is a JSON string with the e-invoice fields (expect keys like `SellerGstin`, `BuyerGstin`, `DocNo`, `DocTyp`, `DocDt`, `TotInvVal`, `ItemCnt`, `MainHsnCode`, `Irn`, `IrnDt`; parse leniently, tolerate casing/variants). Signature verification is **only** performed when `IRP_PUBLIC_KEY_PEM` is configured; otherwise mark `qr_signature: UNVERIFIED`. QR-derived values are the highest-confidence source (`EXTRACTED_QR`).
2. **`text_layer.py`** — PyMuPDF text, words with bounding boxes, and table extraction (reuse existing `extract_tables_from_pdf`). Keep the existing regex parser as the **fallback** extractor (`EXTRACTED_REGEX`), and fix: seller vs buyer GSTIN disambiguation by section/position rather than first match; supplier name must not default to "first line"; `CGST/SGST/IGST` rate and amount from table rows; totals must not pick up "Sub Total" or "Total Taxable".
3. **`llm_extractor.py`** — Provider-agnostic interface `ExtractionProvider.extract(file_bytes, mime) -> dict` with thin `httpx` adapters for **Gemini** and **Anthropic** (PDF/image inline), selected by `LLM_PROVIDER` (`gemini|anthropic|none`), `LLM_API_KEY`, `LLM_MODEL` (all from env; **do not hardcode model names**). Temperature 0, JSON schema for output: supplier legal name, trade name, supplier GSTIN, buyer name, buyer GSTIN, invoice number, invoice date, place of supply, line items (description, HSN/SAC, qty, rate, taxable, tax rate), taxable total, CGST, SGST, IGST, cess, round-off, discount, total, currency, bank name, IFSC, masked account (**ask the model for last 4 digits only**), IRN if printed. Validate the response with Pydantic; reject and retry once on invalid JSON; never trust numbers blindly — see merge rules.
4. **`merge.py`** — Field-level merge with precedence **QR > LLM > REGEX**, each field tagged with source and confidence. Where two sources disagree on a material field (GSTIN, invoice number, date, total, tax), keep both values, set status `CONFLICT`, and emit rule `EXTRACTION_CONFLICT` (MANUAL_REVIEW). Run the deterministic validators on the merged result. Set `ExtractionStatus` honestly: `EXTRACTED` only when the value is literally present in the document text or QR; LLM values are `EXTRACTED_LLM`; unknown → `UNAVAILABLE`. Add the new enum values and mirror them in `frontend/src/types/api.ts`.
5. **Privacy note:** invoice content is sent to the configured LLM provider. Add `LLM_PROVIDER=none` (regex + QR only) as a supported mode, document it in README, never log raw invoice text or full bank account numbers, and keep masking.
6. **Persist the uploaded file** under `UPLOAD_DIR/<case_id>/<sha256>.<ext>` (outside any static path) and add authenticated `GET /api/cases/{id}/file` so the UI can show the original beside extracted fields. Today only the hash is stored.
7. Route `POST /api/cases` through this pipeline for PDFs and images; scanned PDFs are handled by rendering pages to images and sending them down the same path.

**Tests (no network):** mock the LLM HTTP layer with `httpx.MockTransport`; build a synthetic JWT QR payload in-test and render it into a PDF; cover QR present, QR absent, QR/printed mismatch, LLM invalid JSON, provider `none`, image upload, scanned PDF.

Commit: `feat(extraction): layered QR + text + LLM pipeline with provenance`.

---

## 4. PHASE C (P0) — Checks that work with real data

### C1. Deterministic checks (no external data)
Add to the rule engine with reason codes, weights, and tests:
- **Buyer GSTIN mismatch:** configure `BUYER_GSTINS` (comma list, own company registrations). If extracted buyer GSTIN is missing or not in the list → HIGH (ITC not claimable in another entity's name).
- **Tax type vs state:** supplier state code (GSTIN chars 1–2) vs place of supply / buyer state code. Same state → CGST+SGST expected; different → IGST expected. Wrong tax type → HIGH.
- **PAN consistency:** GSTIN chars 3–12 must be a well-formed PAN; the 4th PAN character must be one of the valid holder-type letters (C,P,H,F,A,T,B,L,J,G); mismatch with a PAN printed on the invoice → HIGH.
- **Invoice number format:** ≤16 chars, only alphanumerics, `-` and `/` (Rule 46). Violation → LOW.
- **Date sanity:** future date → HIGH; ITC time-bar (30 Nov following the financial year of the invoice) as an informational flag, constants configurable, labelled "verify with CA".
- **E-invoice markers:** IRN/QR missing on a B2B invoice → INFO only (depends on supplier turnover; do not penalise hard). QR/printed field mismatch → CRITICAL (possible tampering) with no BLOCK unless the QR signature is verified.
- **Arithmetic** from **extracted** values only; line-item sums vs taxable total; per-line rate × taxable = tax within tolerance.
- **Duplicate detection:** keep existing, but compare normalised invoice number + supplier GSTIN (not just name).

### C2. Pluggable registry providers (`backend/app/services/providers/`)
Interface `GstinProvider.lookup(gstin) -> Evidence`. Implement:
1. **`ManualEntryProvider` (default for MVP, works with zero cost today).** UI form where the reviewer pastes details from the public GST "Search Taxpayer" page (legal name, trade name, status, registration date, constitution, source URL, optional screenshot). Stored as evidence with mode `MANUAL`, user id and timestamp, `is_authoritative=true` only because a named human attested it. Endpoint: `POST /api/cases/{id}/evidence/gstin`. Re-run assessment automatically.
2. **`HttpKycProvider`** — generic: `GSTIN_API_URL_TEMPLATE`, auth header name/value from env, and a JSON mapping (`GSTIN_API_FIELD_MAP`) from vendor response → `{legal_name, trade_name, status, registration_date, constitution}`. This lets the team plug in whichever GSP/KYC vendor they get a key for (Vayana, Signzy, Masters India, Sovos and similar offer "search taxpayer" APIs) in minutes, without code changes.
3. **`TinyFishProvider`** — the reworked client from A5, experimental, optional.
4. **`DemoProvider`** — fixtures, only when `DEMO_MODE=true` and `case.is_demo`.

Provider order is configurable (`GSTIN_PROVIDERS=http_kyc,manual`). If none returns data → `UNAVAILABLE` → MANUAL_REVIEW with the "add registry details" call to action.

### C3. IFSC verification (free, real)
`IfscProvider` calls `https://ifsc.razorpay.com/<IFSC>` (open dataset), with timeout, caching (SQLite table, 30-day TTL), and failure → `UNAVAILABLE`. Compare returned bank name with the bank name printed on the invoice. Invalid IFSC → MEDIUM. **Never claim account ownership**; keep the existing `BANK_OWNERSHIP_UNVERIFIED` rule and the cancelled-cheque / penny-drop wording.

### C4. Verdict semantics (single source of truth in `AssessmentService`)
- **PASS** only if: GSTIN checksum valid, arithmetic verified from extracted (non-inferred) values, buyer GSTIN OK, tax type consistent, no extraction conflicts, GSTIN status `Active` from a non-demo, non-unavailable provider, legal/trade name matches, no duplicates.
- **BLOCK** only on confirmed-bad facts: invalid GSTIN checksum, registry status cancelled/suspended from real or attested evidence, verified-signature QR contradicting the printed invoice, exact duplicate of an already-RESOLVED-approved case (keep exact duplicates as MANUAL_REVIEW otherwise).
- Everything else MANUAL_REVIEW. Demo evidence can produce a demo verdict but the response carries `evidence_provenance_mode=DEMO` and the UI shows a DEMO banner.
- Add a `GET /api/cases/{id}/explain` payload (or extend the case) with a plain-English "why this verdict" list and "what would change it" list.

Commit: `feat(checks): deterministic invoice checks, registry providers, IFSC, verdict semantics`.

---

## 5. PHASE D (P0) — Minimal real auth

- `USERS_JSON` env: `[{"token":"…","id":"priya","role":"ap_analyst"},{"token":"…","id":"garv","role":"reviewer"}]`. Roles: `ap_analyst` (create, upload, correct, add evidence, investigate), `reviewer` (all + sign-off).
- Require `Authorization: Bearer <token>` on **every** `/api/*` route except `/health`, unless `AUTH_DISABLED=true` and `ENVIRONMENT=development` (log a loud warning). Identity is always server-derived; remove client-supplied `reviewer_id`/`reviewer_role` trust entirely (also remove them from the request schema or ignore them).
- Remove the committed default token and the dev-token constant from `config.py`; the startup validator must refuse production if no users are configured.
- Frontend: a small "Enter access token" screen storing the token in `sessionStorage`; `lib/api.ts` sends it; 401 → redirect to that screen.
- Add upload rate limiting (simple in-memory per-token limiter) and a per-case size cap already present.
- Audit events record the real user id and role. Keep the SHA-256 hash chain, and add `GET /api/cases/{id}/audit/verify` that recomputes the chain and reports the first broken link.

Commit: `feat(auth): token-based users, server-derived identity, audit verify`.

---

## 6. PHASE E (P0) — Frontend for the real flow

Keep the existing visual design. Changes:
1. **`/upload`:** real file upload is the primary path (PDF/PNG/JPG, multi-file allowed → creates one case each). Remove the prefilled "Apex Courier" defaults. Move scenario presets into a collapsed "Demo scenarios" section; every case created from them is flagged `is_demo` and shows a `DEMO DATA` badge in the queue and dossier.
2. **Extraction review step (new, on `/cases/[id]` before investigation):** left = original file (from `/api/cases/{id}/file`), right = extracted fields with a provenance chip per field (`QR`, `LLM`, `REGEX`, `MANUAL`), confidence, `CONFLICT` highlighting, and inline edit (existing PATCH). Primary button **"Confirm & run checks"**.
3. **Evidence panel:** shows each check with status, provenance mode chip, source URL, retrieved-at, and `UNAVAILABLE` rendered as grey "not checked", never red. Add the **"Add GST registry details"** form (C2.1) with a button that copies the GSTIN and a link to the public GST Search Taxpayer page.
4. **Verdict card:** verdict, score labelled "policy index (heuristic)", the "why / what would change it" lists, and the ITC exposure card only if present and labelled "illustrative".
5. **Queue (`/queue`):** filters (status, verdict, demo on/off), search by vendor / invoice no / GSTIN, CSV export of the queue.
6. **Null-safe rendering** for every optional forensic field. Add an error boundary and clear error toasts using the backend `detail`.
7. **Landing page (`/`):** grep the page for any invented metrics, customer claims, accuracy numbers, testimonials, or "live" labels that are not true; replace with factual statements or delete. Fixture content (Apex, Specter) may stay only inside a section clearly captioned "Illustrative example (demo data)". Respect `prefers-reduced-motion` in the 3D hero; if the hero hurts mobile performance, lazy-load it.
8. Mirror every new backend enum/field in `frontend/src/types/api.ts`. `pnpm tsc --noEmit` and `pnpm build` must pass with the **existing lockfile unchanged** unless you add a dependency (then update `pnpm-lock.yaml` with `pnpm install` and commit it).

Commit: `feat(ui): real-invoice flow, extraction review, evidence entry, honest labelling`.

---

## 7. PHASE F (P1) — GSTR-2B reconciliation (highest-value real dataset)

The buyer can download **GSTR-2B** from the GST portal; it lists invoices that suppliers filed against the buyer's GSTIN, which is the practical proof that ITC is claimable.
- `POST /api/gstr2b/import` accepts the GSTR-2B JSON (and optionally the Excel export). Parse tolerantly: B2B section → supplier GSTIN (`ctin`), trade name, invoice number (`inum`), date (`dt`), value (`val`), taxable (`txval`), `igst/cgst/sgst/cess`, ITC availability flag. Field names are from memory: accept variants, log unknown shapes, and **record in docs/MVP_STATUS.md that this parser must be validated against a real downloaded file**.
- Store in a `gstr2b_entries` table (period, buyer GSTIN, rows).
- Match each case on normalised (supplier GSTIN, invoice number); compare date, taxable value and tax. New rules: `ITC_NOT_IN_GSTR2B` (MEDIUM → payment-hold advice), `GSTR2B_VALUE_MISMATCH` (HIGH), `GSTR2B_ITC_NOT_AVAILABLE` (MEDIUM).
- UI: import box on the queue page, GSTR-2B status chip per case, and a "unmatched GSTR-2B rows" list.
- Test with a synthetic file generated in-test.

Commit: `feat(gstr2b): import and invoice matching`.

---

## 8. PHASE G (P1) — Test corpus, eval harness, docs

1. `scripts/make_sample_invoices.py` (use `reportlab`, add to `requirements-dev.txt`) generates ~12 PDFs with checksum-valid synthetic GSTINs and a matching `expected.json` for each: clean intra-state, clean inter-state (IGST), tampered total, wrong buyer GSTIN, wrong tax type for the states, invalid GSTIN checksum, duplicate pair, same invoice number with a different amount, missing GSTIN, image-only scanned version, and one carrying a synthetic e-invoice QR (matching) plus one with a QR that disagrees with the printed total.
2. `scripts/eval_extraction.py <folder>` runs the pipeline over PDFs with a sibling `.expected.json` and prints a per-field accuracy table. Tell the team they can drop in 10–20 real (redacted) vendor invoices to get a real accuracy number for the mentors.
3. Tests: end-to-end API tests for upload → review → evidence → verdict → sign-off for each corpus file; no network in CI.
4. CI: backend `pytest -q`, frontend `pnpm tsc --noEmit && pnpm build`, plus a job that boots the server from `.env.example` and hits `/health`.
5. Docs: rewrite `README.md` with an honest **Real / Demo / Roadmap** table; `docs/DATA_SOURCES.md` (every data source, how it is obtained, cost, reliability, limits); `docs/DEMO_SCRIPT.md` (a 5-minute mentor demo: real upload → extraction review → missing registry evidence → manual entry → verdict → sign-off → audit verify, plus a 60-second demo-scenario fallback); `docs/MVP_STATUS.md` (what was done, real command output, UNVERIFIED AGAINST REAL DATA list, known limits). Remove or clearly mark stale claims (test counts, "Verified" statuses that were fixture-only).

Commit: `chore(mvp): corpus, eval harness, CI, honest docs`.

---

## 9. PHASE H (P2 — only if time remains)
- Bulk ZIP upload and batch queue progress.
- Vendor master: remember attested GSTIN details per vendor so the second invoice from the same vendor needs no manual lookup (with "re-verify after 90 days" flag).
- PDF export of the dossier (Markdown export already exists).
- Email-in intake via a watched IMAP inbox.

---

## 10. Definition of done
1. A real text-based invoice PDF, a scanned PDF and a phone photo all upload, extract with provenance, and reach a verdict **without a 500 error**, with no API keys configured (`LLM_PROVIDER=none`, no registry provider) → verdict MANUAL_REVIEW with a clear "add registry details" prompt.
2. With an LLM key configured, the same files extract more fields correctly; with manual registry details entered for an active vendor and clean checks, the verdict can become PASS.
3. No demo data in the real queue; demo cases are always labelled.
4. `cp .env.example backend/.env && uvicorn app.main:app` boots; `pnpm build` passes; backend tests pass; CI green.
5. Every item in Phase A has a regression test; no hardcoded GSTINs outside the demo provider and tests.
6. `docs/MVP_STATUS.md` contains real command output and the UNVERIFIED list.

## 11. Final report format (print at the end)
Phases completed; commits; test and build output (pasted); what is REAL vs DEMO vs EXPERIMENTAL; the UNVERIFIED-against-real-data list; the first three things the team should do next with real data.
