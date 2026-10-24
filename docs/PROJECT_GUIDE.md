# VendorShield AI — Comprehensive Project Guide

> **Tagline:** *Know your vendor before you pay.*  
> **Repository:** `https://github.com/TanmayJain-dev/VendorShield.git`  
> **Hackathon:** HackIIITD (Esya '26, IIIT Delhi) | **Track:** FinTech & Enterprise Automation  
> **Official Team Roles:**
> - **Tanmay Jain:** Team Lead + Tech Lead
> - **Prachi Bhalla:** Problem Research + Product Strategy + User Experience
> - **Garv Goyal:** Risk Research + Validation + Impact

---

## 1. Executive Summary & Problem Statement

### The Problem
Accounts Payable (AP) and procurement departments process thousands of supplier invoices monthly. Organizations lose billions globally each year to vendor fraud, including:
1. **Ghost Vendors / Shell Companies:** Fraudsters submit invoices using fake corporate identities or fabricated Goods and Services Tax Identification Numbers (GSTINs).
2. **Trade Name vs. Legal Entity Conflicts:** Invoices display a recognizable consumer trade name (e.g., "Apex Courier"), but payments are routed to an unrelated corporate bank account.
3. **Suspended or Cancelled GST Registrations:** Vendors whose tax registration was revoked continue billing clients. When companies pay such invoices, tax authorities disallow Input Tax Credit (ITC), causing direct financial loss.
4. **Duplicate Billing:** Identical invoices are resubmitted across cycles, or modified amounts are applied to re-used invoice numbers.
5. **Invoice Tampering & Arithmetic Inconsistencies:** Subtle arithmetic errors, manipulated tax splits (CGST + SGST vs. IGST), or discrepancies between line item subtotals and grand totals.

### The Solution: VendorShield AI
VendorShield AI is an **evidence-grounded accounts payable due-diligence and risk mitigation system**. It automates statutory verification and web due-diligence before payment authorization:
- It parses invoices to extract claims.
- It deploys **TinyFish browser automation** to research public registries (such as the official GST portal) and company footprints.
- It deterministically reconciles discovered evidence against invoice claims.
- It computes a transparent, explainable **Deterministic Policy Risk Index**.
- It enforces a strict **Human-in-the-Loop** workflow: the AI never authorizes payments; human reviewers make the final decision with mandatory audit rationales.

> **Foundational Axiom:**  
> *TinyFish researches; VendorShield decides.*  
> Web agents gather public signals; deterministic compliance rules and human reviewers evaluate risk.

---

## 2. Target Users & Core Use Cases

| Target Persona | Key Responsibilities | How VendorShield Empowers Them |
| :--- | :--- | :--- |
| **Accounts Payable Analyst / Clerk** | First-line invoice processing, data entry, and claim checking. | Automatically extracts claims, validates arithmetic, detects duplicates, and surfaces registry discrepancies. |
| **Accounts Payable Manager** | Approving high-value disbursements, handling exceptions and escalations. | Reviews fail-closed dossiers (`MANUAL_REVIEW`, `BLOCK`), inspects evidence provenance, and signs off with audit rationale. |
| **Compliance Officer / Risk Manager** | Enforcing anti-fraud policies, statutory tax compliance, and vendor master integrity. | Reviews hard-gate violations, verifies trade aliases against legal corporate entities, and ensures zero phantom vendors. |
| **Internal & External Auditors** | Post-payment review, compliance verification, and statutory inspection. | Downloads cryptographically chained, tamper-evident audit trails with timestamps, actor roles, and SHA-256 snapshots. |

---

## 3. End-to-End Workflow

```
[Supplier Invoice (PDF/Form)]
              │
              ▼
   ┌────────────────────────────────────────────────────────┐
   │ 1. INGESTION & PARSING                                 │
   │    - Backend validation: Magic bytes, 10MB limit, 25pgs│
   │    - SHA-256 file fingerprint & duplicate detection    │
   │    - PyMuPDF text & regex extraction                   │
   │    - GSTIN Modulo-36 checksum verification              │
   │    - CGST/SGST/IGST tax arithmetic reconciliation      │
   │    - Uncertainty labeling: EXTRACTED / INFERRED        │
   └────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────┐
   │ 2. BOUNDED WEB RESEARCH (TinyFish API)                 │
   │    - Official GST search portal lookup                 │
   │    - MCA corporate footprint query                     │
   │    - RBI IFSC directory branch check                   │
   │    - Provenance tagged: LIVE vs. SIMULATED fallback   │
   └────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────┐
   │ 3. DETERMINISTIC EVIDENCE RECONCILIATION               │
   │    - Business name normalization & suffix stripping     │
   │    - Trade name alias vs. legal corporate entity match │
   │    - Active vs. suspended registration check           │
   │    - Beneficiary ownership invariant check (IFSC only)  │
   └────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────┐
   │ 4. RISK SCORING & POLICY ROUTING                       │
   │    - Deterministic compliance index (0-100)            │
   │    - Hard safety gates (GST inactive, name conflict)   │
   │    - Fail-closed outcome: PASS / MANUAL_REVIEW / BLOCK │
   │    - Evidence completeness: COMPLETE / PARTIAL / etc.  │
   └────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────┐
   │ 5. HUMAN REVIEWER SIGN-OFF                             │
   │    - Legal state transitions enforced                  │
   │    - Actions: APPROVE, APPROVE_WITH_EXCEPTION,         │
   │      REQUEST_DOCUMENTS, ESCALATE, REJECT               │
   │    - Mandatory audit rationale recorded                │
   │    - Interactive claim correction triggers reassessment│
   └────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────┐
   │ 6. TAMPER-EVIDENT CHAINED AUDIT TRAIL                  │
   │    - Cryptographic SHA-256 hash chaining of all events  │
   │    - Persistent SQLite / PostgreSQL storage            │
   │    - Downloadable Markdown audit dossier report        │
   └────────────────────────────────────────────────────────┘
```

---

## 4. System Architecture & Technology Stack

The project is structured as a modular monorepo:

```
VendorShield/
├── backend/                       # Python 3.12+ FastAPI Application
│   ├── app/
│   │   ├── api/                   # REST API Routers
│   │   │   ├── cases.py           # Case CRUD, file upload, claim corrections
│   │   │   ├── investigate.py     # TinyFish investigation orchestration
│   │   │   ├── review.py          # Human reviewer workflow & state transitions
│   │   │   └── reports.py         # Markdown audit report & audit trail exports
│   │   ├── db/                    # Persistent Storage Layer (SQLAlchemy 2)
│   │   │   ├── database.py        # Engine, SessionLocal, Base, init_db
│   │   │   ├── models.py          # CaseModel, InvoiceModel, EvidenceItemModel, etc.
│   │   │   └── repository.py      # CaseRepository CRUD & audit event chaining
│   │   ├── schemas/               # Canonical Pydantic v2 Contracts
│   │   │   ├── case.py            # Case, CaseSummary
│   │   │   ├── invoice.py         # InvoiceClaim, LineItem, TaxBreakdown, InvoiceCorrection
│   │   │   ├── evidence.py        # EvidenceItem, FieldCheckResult
│   │   │   ├── assessment.py      # RiskAssessment, RuleTrigger
│   │   │   ├── review.py          # ReviewAction
│   │   │   └── enums.py           # CaseStatus, SourceMode, RecommendationOutcome, etc.
│   │   ├── services/              # Core Domain Services
│   │   │   ├── parser/            # invoice_parser.py (PDF text, tax math, uncertainty)
│   │   │   ├── validators/        # gstin_validator.py, arithmetic_validator.py
│   │   │   ├── tinyfish/          # client.py (TinyFish API client & simulation fixtures)
│   │   │   ├── reconciler/        # evidence_reconciler.py (entity normalization & matching)
│   │   │   ├── rules/             # engine.py (deterministic rule engine & fail-closed logic)
│   │   │   └── audit/             # trail.py (SHA-256 hashing, markdown generation)
│   │   ├── config.py              # Application settings, environment variables
│   │   └── main.py                # FastAPI entrypoint, lifespan startup, CORS
│   └── tests/                     # 33 Automated Pytest Suites
├── frontend/                      # Next.js 15 App Router Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Pre-payment due-diligence dashboard queue
│   │   │   ├── upload/page.tsx    # Invoice intake, file dropzone & preset loader
│   │   │   ├── cases/[id]/page.tsx# Case evidence dossier, corrections, review sign-off
│   │   │   ├── globals.css        # Tailwind styling & dark theme tokens
│   │   │   └── layout.tsx         # Root layout with top navigation header
│   │   ├── lib/
│   │   │   └── api.ts             # Complete type-safe API client connecting to FastAPI
│   │   └── types/
│   │       └── api.ts             # TypeScript interfaces mirroring backend Pydantic models
│   ├── package.json               # Dependencies (React 19, Tailwind, Lucide, Autoprefixer)
│   └── tsconfig.json              # TypeScript strict configuration
├── docs/                          # Project Guides, Role Guides & Architecture Specs
│   ├── PROJECT_GUIDE.md           # Central master guide (this file)
│   ├── TEAM_ROLES.md              # Official team roles & responsibility matrix
│   ├── START_AGENT_RESEARCH.md    # Universal prompt template for AI research agents
│   └── agents/                    # Personalized agent research guides
│       ├── TANMAY_AGENT_GUIDE.md  # Guide for Tanmay Jain
│       ├── PRACHI_AGENT_GUIDE.md  # Guide for Prachi Bhalla
│       └── GARV_AGENT_GUIDE.md    # Guide for Garv Goyal
├── sample_data/                   # Benchmark test cases (INV-2026-8841, etc.)
├── .env.example                   # Environment configuration template
└── README.md                      # Main project presentation & quickstart
```

---

## 5. Detailed Module Explanations

### 5.1 Document Ingestion & Invoice Parser (`backend/app/services/parser/invoice_parser.py`)
- **Text & Scan Handling:** Uses `pymupdf` (fitz) to read PDF bytes. Enforces a 25-page DoS protection limit. Detects scanned or image-only documents when text length is minimal (< 30 characters).
- **Dynamic Tax Breakdown:** Does NOT assume 18% GST. Extracts explicit CGST, SGST, IGST rates (e.g., 5%, 12%, 18%, 28%), discounts, and round-offs.
- **Uncertainty Flagging:** When tax figures are not stated in the invoice text, they are labeled as `INFERRED` rather than presented as verified facts.
- **Structured Error Handling:** Parsing issues are returned in `parsing_errors` and `parsing_warnings` lists rather than injected into text.

### 5.2 Validators (`backend/app/services/validators/`)
- **GSTIN Format & Checksum (`gstin_validator.py`):** Validates the 15-character statutory format and computes the 15th character checksum using the GSTN Modulo 36 algorithm.
- **Invoice Arithmetic (`arithmetic_validator.py`):** Reconciles $\text{Taxable} + \text{CGST} + \text{SGST} + \text{IGST} + \text{Round-Off} - \text{Discount} = \text{Total Amount}$ within a ₹1.00 tolerance.

### 5.3 Evidence Reconciler (`backend/app/services/reconciler/evidence_reconciler.py`)
- **Name Normalization:** Strips common business suffixes (`Private Limited`, `Pvt Ltd`, `LLP`, `Inc`, `Corp`, `Co`), removes punctuation, expands `&` to `and`, and collapses whitespace.
- **Trade Alias vs. Legal Entity:**
  - If invoice supplier matches legal entity $\rightarrow$ `MATCH`.
  - If invoice supplier matches registered trade alias, but differs from legal entity $\rightarrow$ `POSSIBLE_MATCH` (`LEGAL_NAME_MISMATCH`), prompting human verification of the trade alias.
  - Never marks a match merely because a `trade_name` field exists in the data.
  - Conflicting entities $\rightarrow$ `MISMATCH` (`CRITICAL_NAME_MISMATCH`).
- **Beneficiary Ownership Invariant:** Public IFSC lookups verify the bank branch, but CANNOT prove beneficiary account ownership. This check is kept as `POSSIBLE_MATCH` (`BANK_OWNERSHIP_UNVERIFIED`) requiring cancelled cheque or penny-drop confirmation.

### 5.4 Deterministic Rule Engine (`backend/app/services/rules/engine.py`)
- **Deterministic Policy Risk Index:** A score from 0 to 100 derived from explicit point deductions (e.g., -30 for invalid GSTIN, -20 for arithmetic mismatch, -20 for trade vs. legal name mismatch).
- **Explaining the Score:** The UI and reports clearly label this as a **deterministic policy compliance index**, not an uncalibrated statistical fraud probability.
- **Fail-Closed Recommendations:**
  - `BLOCK`: Hard safety gates triggered (`GST_STATUS_INACTIVE_CONFIRMED`, `CRITICAL_NAME_MISMATCH`).
  - `MANUAL_REVIEW`: Any discrepancies, missing registry data, duplicate invoices, or score < 75.
  - `PASS`: Clean statutory match with verified active registration.
- **Evidence Completeness:** Classifies evidence as `COMPLETE`, `PARTIAL`, `INSUFFICIENT`, `CONFLICTING`, or `SIMULATED_VERIFIED`.

### 5.5 TinyFish Integration & Provenance (`backend/app/services/tinyfish/client.py`)
- **Safe Encoding & Input Sanitization:** Search queries are URL-encoded (`urllib.parse.quote_plus`). Extracted web content is stripped of HTML and prompt-injection keywords.
- **Mode Tracking:** Every evidence item records its mode: `LIVE`, `SIMULATED`, or `UNAVAILABLE`.
- **Transparent Fallback:** If live calls fail or time out, the system falls back to simulated fixtures, visibly marking every item with `is_fallback: True` and detailing the fallback reason. Simulated evidence is never presented as live research.

### 5.6 Persistent Storage & Cryptographic Audit Chain (`backend/app/db/` & `backend/app/services/audit/trail.py`)
- **Database Storage:** Uses SQLAlchemy 2 with SQLite (`vendorshield.db`) for local zero-setup operation, with a clean design ready for PostgreSQL in production.
- **Append-Only Tamper-Evident Hash Chain:** Every lifecycle event (`CASE_CREATED`, `INVESTIGATION_COMPLETED`, `INVOICE_FIELDS_CORRECTED`, `REVIEW_DECISION_RECORDED`) stores:
  $$\text{event\_hash} = \text{SHA-256}(\text{prev\_hash} \parallel \text{timestamp} \parallel \text{event\_type} \parallel \text{actor} \parallel \text{event\_data})$$
- **Case Digest:** A canonical JSON snapshot digest is computed at every milestone.

### 5.7 Duplicate Invoice Detection
- **File SHA-256 Hash:** Identifies exact file re-uploads even if renamed.
- **Normalized Invoice Key:** Combines normalized vendor name and invoice number to identify:
  - `EXACT_INVOICE_DUPLICATE`: Same vendor, same invoice number, and same amount.
  - `SUSPECT_INVOICE_REUSE`: Same vendor and invoice number, but different amount.
- **Policy Routing:** Duplicates trigger `MANUAL_REVIEW` with clear warnings; they are not automatically treated as fraudulent without human review.

---

## 6. Current Implementation Status

| Feature | Status | Implementation Details |
| :--- | :--- | :--- |
| **PDF Ingestion & Text Extraction** | ✅ Verified | PyMuPDF text stream extraction with 25-page limit and scan detection. |
| **GSTIN Checksum & Arithmetic Validation** | ✅ Verified | Modulo 36 checksum algorithm + tax breakdown mathematical verification. |
| **Duplicate Invoice Detection** | ✅ Verified | File SHA-256 hashing + normalized vendor/invoice number index. |
| **Persistent Database Storage** | ✅ Verified | SQLAlchemy 2 SQLite storage surviving restarts; PostgreSQL ready. |
| **Evidence Reconciliation** | ✅ Verified | Business suffix stripper, normalization, trade alias disambiguation. |
| **Deterministic Risk Scoring** | ✅ Verified | Rule triggers with weights, hard safety gates, and fail-closed routing. |
| **Reviewer Workflow & State Machine** | ✅ Verified | Transitions (`PARSED` $\rightarrow$ `READY_FOR_REVIEW` $\rightarrow$ `RESOLVED`/`PENDING_DOCUMENTS`/`ESCALATED`). |
| **Interactive Invoice Corrections** | ✅ Verified | Reviewers can correct claims; automatic re-assessment and audit logging. |
| **Chained Audit Trail** | ✅ Verified | Cryptographically linked SHA-256 event chain and markdown report exporter. |
| **Next.js 15 Frontend & API Client** | ✅ Verified | Full type-safe API client, evidence dossier view, and activity history. |
| **Automated Test Suite** | ✅ Verified | 33 passing pytest unit and integration tests across all services. |
| **Live TinyFish Browser Automation** | 🟡 Configurable | Works live when `TINYFISH_API_KEY` is set; transparent `SIMULATED` fallback when unset. |
| **Bank Account Penny-Drop Verification** | ⚪ Planned | Public IFSC verifies branch; live beneficiary lookup requires banking partner API. |
| **Cloud OCR for Handwritten Invoices** | ⚪ Planned | Scans detected and flagged; cloud vision OCR planned for photo scans. |

---

## 7. Security, Privacy & Known Limitations

1. **Banking Privacy:** Bank account numbers are masked (`XXXX-XXXX-9921`) in all logs, displays, and audit exports.
2. **Upload Security:** File size capped at 10MB; magic byte verification prevents executable uploads; filenames are sanitized against path traversal.
3. **CORS Security:** Restricted to explicit configured origins (`localhost:3000`, `127.0.0.1:3000`, and custom production domains); credentials enabled without wildcards.
4. **Development Authentication Notice:** The MVP reviewer endpoint includes a clearly documented development mode (`REVIEWER_DEV_MODE=True`). In production, this must be backed by an enterprise SSO/OAuth2 provider.
5. **System Limitations:**
   - VendorShield does not guarantee 100% fraud prevention; it verifies statutory consistency and corroborates public evidence.
   - Public web data cannot prove bank account beneficiary ownership without offline confirmation.

---

## 8. Local Setup & Testing Instructions

### Backend (Python 3.12+)
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
python -m pip install -r requirements.txt

# Run the 33-test automated test suite
python -m pytest backend/tests

# Start FastAPI development server
python -m uvicorn backend.app.main:app --reload --port 8000
```
Interactive Swagger API documentation: `http://localhost:8000/docs`

### Frontend (Node.js 20+)
```bash
cd frontend

# Install dependencies
npm install

# Verify TypeScript type checking
npx tsc --noEmit

# Run Next.js production build
npm run build

# Start local Next.js development server
npm run dev
```
Web application interface: `http://localhost:3000`

---

## 9. Technical Glossary

- **GSTIN (Goods and Services Tax Identification Number):** A 15-character statutory business identifier in India. Characters 1–2 represent the state code, 3–12 are the PAN (taxpayer identifier), 13 is entity number, 14 is the letter 'Z', and 15 is the Modulo-36 checksum.
- **ITC (Input Tax Credit):** Tax credit businesses claim for taxes paid on business purchases. If a supplier's GST registration is cancelled or suspended, the buyer cannot claim ITC, resulting in a tax loss.
- **Modulo 36 Checksum:** The mathematical algorithm defined by India's GSTN to structurally validate the 15th character of a GSTIN.
- **Fail-Closed:** A security principle where any missing, ambiguous, or failed verification defaults to a restrictive state (`MANUAL_REVIEW` or `BLOCK`) rather than automatically approving.
- **Trade Name vs. Legal Name:** A company's registered statutory corporate entity (e.g., "Apex Global Logistics Private Limited") versus its commercial brand name (e.g., "Apex Courier").
- **Hard Safety Gate:** A deterministic rule that immediately halts automatic processing and requires a block or manual review, regardless of other positive scoring factors.
- **Tamper-Evident Hash Chain:** An append-only sequence of audit events where each record embeds the SHA-256 cryptographic digest of the preceding event, ensuring history cannot be altered without detection.
- **TinyFish API:** A web agent research API (`agent.tinyfish.ai`) used to automate public browser lookups across government portals and company registries.
