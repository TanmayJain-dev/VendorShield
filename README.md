# VendorShield AI 🛡️

> **Tagline:** *Know your vendor before you pay.*  
> **Hackathon:** [HackIIITD — Esya '26 (IIIT Delhi)](https://unstop.com/hackathons/hackiiitd-esya26-indraprastha-institute-of-information-technology-iiit-delhi-1761212) | **Track:** FinTech & Enterprise Automation  
> **Team Astra-X:** Tanmay Jain (`@TanmayJain-dev`), Prachi Bhalla (`@pra27-06`), Garv Goyal (`@garvgoyal01`)  
> **Partner Technology:** **TinyFish API** (Agentic Web Research & Live Data Extraction)

---

## 📌 Executive Summary

**VendorShield AI** is an evidence-grounded accounts payable due-diligence and pre-payment risk mitigation sentinel designed for Indian B2B commerce.

Under Section 16(2)(c) of the CGST Act, buyers claiming Input Tax Credit (ITC) face direct statutory liability (100% tax clawback + 18% interest + penalties) if their vendor fails to pay tax or holds a cancelled registration. VendorShield evaluates vendor invoices, extracts claims with multi-layer provenance, verifies facts against government registries and GSTR-2B returns, and enforces tamper-evident human sign-off before payment release.

> **Core Axiom:** *TinyFish researches; VendorShield decides.*  
> The browser agent is an evidence collector, not a final fraud arbiter. Deterministic rules govern the recommendation. Weak, conflicting, or unreachable evidence fails closed to **`MANUAL REVIEW`**.

---

## 📊 Capability Matrix: What is Real vs. Demo vs. Experimental vs. Roadmap

| Capability | Status | Description & Implementation |
| :--- | :---: | :--- |
| **Invoice File Intake** | **REAL** | Native PDF text extraction (PyMuPDF), scanned image handling, PNG/JPEG support, multi-file batch upload. |
| **e-Invoice QR Code JWT** | **REAL** | Decodes B2B e-invoice QR codes via OpenCV/PyMuPDF; validates inner claims (`SellerGstin`, `TotInvVal`, `Irn`). |
| **Deterministic Mod-36 Checksum** | **REAL** | Verifies official 15-character GSTIN Modulo-36 algorithm. Confirmed bad format triggers hard BLOCK. |
| **Mathematical Reconciliation** | **REAL** | Multi-rate tax breakdown, CGST+SGST (intra-state), IGST (inter-state), discount, round-off validation. |
| **GSTR-2B Return Ingestion** | **REAL** | Tolerantly parses GST Portal GSTR-2B JSON returns; matches supplier invoices; flags payment hold if missing. |
| **Bank IFSC Code Lookup** | **REAL** | Razorpay IFSC API query with SQLite caching (30-day TTL). Strictly flags `BANK_OWNERSHIP_UNVERIFIED`. |
| **Cryptographic Audit Trail** | **REAL** | Tamper-evident SHA-256 hash chains across all state transitions; includes on-demand verification endpoint. |
| **Reviewer Authentication & RBAC** | **REAL** | Bearer token authentication (`USERS_JSON`) with server-derived roles (`ap_analyst`, `reviewer`). |
| **Public Portal Search** | **ATTESTED** | Direct reviewer manual attestation with GST Search Taxpayer link (`services.gst.gov.in`); flips review to PASS. |
| **TinyFish Autonomous Agent** | **EXPERIMENTAL** | Headless browser agent researching public registry footprint when `TINYFISH_API_KEY` is configured. |
| **5-Vector Forensic Topology** | **EXPERIMENTAL** | Heuristic prioritization indicator (ITC Clawback, Shell Contagion, Collocation Ghost Hub, Pop-up Velocity). |
| **Direct GSTN API Auto-Sync** | **ROADMAP** | Automated enterprise GSP sync without manual JSON export download. |

---

## 🏗️ Architecture & Monorepo Structure

```
VendorShield/
├── .github/
│   ├── workflows/ci.yml             # Automated CI: backend tests + pnpm typecheck + pnpm build + health check
│   └── agents/                      # GitHub role instructions (Tanmay, Prachi, Garv)
├── backend/                         # FastAPI Python 3.12+ Backend
│   ├── app/
│   │   ├── api/                     # REST endpoints (/cases, /investigate, /review, /reports, /gstr2b)
│   │   ├── auth/                    # Minimal token auth & rate limiting (security.py)
│   │   ├── db/                      # SQLAlchemy 2 persistence & SQLite repository (repository.py, models.py)
│   │   ├── schemas/                 # Canonical Pydantic v2 data models
│   │   ├── services/
│   │   │   ├── extraction/          # Layered extraction pipeline (QR + Text + LLM merge)
│   │   │   ├── providers/           # Pluggable registry providers (Manual, TinyFish, HttpKyc, Demo)
│   │   │   ├── reconciler/          # GSTR-2B parser, business name normalization, evidence reconciliation
│   │   │   ├── rules/               # Deterministic rule engine, assessment service, explainability
│   │   │   ├── validators/          # Mod-36 GSTIN checksum, arithmetic validators
│   │   │   └── audit/               # Cryptographically chained SHA-256 audit logs
│   │   └── main.py                  # Server entrypoint with CORS & lifespan initialization
│   ├── tests/                       # 120+ Unit, security, extraction, GSTR-2B, and E2E tests
│   └── requirements-dev.txt         # Dev dependencies including pytest and reportlab
├── frontend/                        # Next.js 15 App Router Frontend (Tailwind, Lucide)
│   ├── src/app/                     # Landing (/), Upload (/upload), Dossier (/cases/[id]), Queue (/queue)
│   ├── src/components/              # Navbar with Auth Token modal, ThemeProvider, Hero3DScene
│   ├── src/lib/                     # Type-safe API client (api.ts)
│   └── src/types/                   # TypeScript contracts matching backend schemas (api.ts)
├── data/sample_invoices/            # 13 Synthetic benchmark invoice PDFs and matching .expected.json pairs
├── scripts/                         # Evaluation harness & corpus generator
│   ├── make_sample_invoices.py      # Generates synthetic invoice corpus with valid Mod-36 GSTINs
│   └── eval_extraction.py           # Per-field extraction benchmark accuracy evaluator
├── docs/                            # Project Documentation
│   ├── MVP_STATUS.md                # Comprehensive execution log, test outputs & unverified list
│   ├── DATA_SOURCES.md              # Complete catalogue of data sources, costs, limits & fail-closed modes
│   ├── DEMO_SCRIPT.md               # 5-minute hackathon mentor demo script & 60-second fallback
│   ├── PROJECT_GUIDE.md             # Master project guide & architecture overview
│   └── TEAM_ROLES.md                # Official team roles & RACI responsibility matrix
├── .env.example                     # Environment template with pre-configured team tokens
└── README.md
```

---

## 👥 Team & Official Roles

| Member | Official Role | Focus Area |
| :--- | :--- | :--- |
| **Tanmay Jain** | **Team Lead + Tech Lead** | Core backend systems, API contracts, database persistence, layered extraction pipeline, and audit architecture. |
| **Prachi Bhalla** | **Problem Research + Product Strategy + UX** | Domain research (ITC clawback under Sec 16(2)(c)), AP analyst workflow, side-by-side extraction review UX, demo storyline. |
| **Garv Goyal** | **Risk Research + Validation + Impact** | Risk scoring auditability, GSTR-2B reconciliation, fail-closed policy gates, synthetic corpus validation, mentor defense. |

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.12+
- Node.js 20+ & `pnpm` (or `npx pnpm`)

### 1. Backend Setup
```bash
# Copy environment configuration
cp .env.example backend/.env

# Create and activate virtual environment
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Run full automated test suite (122 passing tests)
python -m pytest -q tests

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
Interactive API documentation: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
pnpm install

# Check TypeScript type safety (0 errors)
pnpm tsc --noEmit

# Compile Next.js production build (7/7 routes compiled)
pnpm build

# Start Next.js development server
pnpm dev
```
Web application dashboard: `http://localhost:3000`

---

## 🧪 Benchmark Evaluation Harness

VendorShield includes an automated benchmark harness to measure extraction precision on accounts payable invoices:

```bash
# Generate the 13 synthetic invoice PDFs with valid Mod-36 GSTINs
python scripts/make_sample_invoices.py

# Evaluate field-by-field extraction accuracy
python scripts/eval_extraction.py data/sample_invoices
```

**Benchmark Results:**
- **Overall Field Accuracy:** **89.2%** (116/130 field facts matched)
- **Supplier GSTIN Accuracy:** **100.0%**
- **Buyer GSTIN Accuracy:** **100.0%**
- **Taxable Amount Accuracy:** **92.3%**
- **Invoice Number Accuracy:** **92.3%**

---

## 🔒 Security, Trust Boundary & Governance

- **Token Authentication:** Caller-supplied `reviewer_id` is never trusted. Identity is strictly derived from the authenticated Bearer token configured in `USERS_JSON`.
- **Fail-Closed Guarantee:** When public registries are unavailable, unreached, or timed out, the engine **fails closed to `MANUAL_REVIEW`**; missing evidence is never treated as verified safe.
- **Tamper-Evident SHA-256 Audit Trail:** Every state change and sign-off is hashed with its previous event digest; on-demand verification (`GET /api/cases/{id}/audit/verify`) detects database modification.
- **Privacy Hardening:** Bank account numbers are strictly masked (`XXXX-XXXX-9921`). IFSC validation checks routing existence but never falsely claims proof of account ownership.

---

## 📄 License
MIT License. Built with pride by Team Astra-X for HackIIITD (Esya '26).
