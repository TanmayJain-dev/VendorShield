# VendorShield AI 🛡️

> **Tagline:** *Know your vendor before you pay.*  
> **Hackathon:** [HackIIITD — Esya '26 (IIIT Delhi)](https://unstop.com/hackathons/hackiiitd-esya26-indraprastha-institute-of-information-technology-iiit-delhi-1761212) | **Track:** FinTech & Enterprise Automation  
> **Team Astra-X:** Tanmay Jain (`@TanmayJain-dev`), Prachi Bhalla (`@pra27-06`), Garv Goyal (`@garvgoyal01`)  
> **Partner Technology:** **TinyFish API** (Agentic Web Research & Live Data Extraction)

---

## 📌 Executive Summary

**VendorShield AI** is an evidence-first vendor due-diligence and risk mitigation assistant for Accounts Payable (AP) and finance operations teams.

When a supplier invoice is received, VendorShield:
1. **Extracts Claims:** Converts invoice PDF / CSV data into structured claims (Trade Name, Legal Name, GSTIN, Address, Line Items, Bank/IFSC details).
2. **Researches Public Footprint via TinyFish:** Orchestrates bounded, live-web browser investigations across public registries, corporate directories, and web footprints using the **TinyFish API**.
3. **Deterministically Reconciles:** Compares invoice claims against discovered web evidence field-by-field using strict mathematical and checksum rules.
4. **Delivers an Explainable Dossier:** Categorizes findings into **Verified Facts**, **Potential Discrepancies**, and **Unknown/Unverified** items, recommending an outcome: **`PASS`**, **`MANUAL REVIEW`**, or **`BLOCK`**.
5. **Enforces Human-in-the-Loop Sign-Off:** Requires authorized human sign-off with rationale, exporting a timestamped, SHA-256 cryptographically hashed audit trail.

> **Core Axiom:** *TinyFish researches; VendorShield decides.*  
> The browser agent is an evidence collector, not a final fraud arbiter. Deterministic rules govern the recommendation. Weak, conflicting, or unreachable evidence fails closed to **`MANUAL REVIEW`**.

---

## 🏗️ Architecture & Monorepo Structure

```
VendorShield/
├── .github/
│   ├── workflows/ci.yml             # Automated CI: pytest + typecheck on every PR
│   └── agents/                      # Dedicated AI Agent Instructions for 3-Person Parallel Work
│       ├── AGENT_TANMAY_CORE.md     # Core Rule Engine, TinyFish Client & Case API
│       ├── AGENT_PRACHI_FRONTEND.md # Next.js 15 UI, Evidence Dossier & Review Flow
│       └── AGENT_GARV_INGESTION.md  # PyMuPDF Parser, GSTIN Checksum & Arithmetic Verification
├── backend/                         # FastAPI Python 3.12 Backend
│   ├── app/
│   │   ├── api/                     # REST API endpoints (/cases, /investigate, /review)
│   │   ├── schemas/                 # Canonical Pydantic v2 data models
│   │   ├── services/
│   │   │   ├── parser/              # Document & OCR extraction
│   │   │   ├── validators/          # GSTIN regex/checksum & invoice arithmetic
│   │   │   ├── tinyfish/            # TinyFish REST/SDK agent client & mock fallback
│   │   │   ├── reconciler/          # Field-by-field claim vs evidence matching
│   │   │   ├── rules/               # Deterministic rule engine & hard gates
│   │   │   └── audit/               # SHA-256 audit logs & markdown/PDF exporter
│   │   └── main.py                  # Server entrypoint
│   └── tests/                       # Unit & integration test suites
├── frontend/                        # Next.js 15 App Router Frontend (Tailwind, Lucide)
│   ├── src/app/                     # Dashboard (/), Upload (/upload), Dossier (/cases/[id])
│   ├── src/components/              # Modular UI components
│   └── src/types/                   # TypeScript contracts matching backend schemas
├── sample_data/                     # Synthetic test invoices (INV-2026-8841 benchmark)
├── docs/                            # Architecture specs, API contracts & demo guides
├── .gitignore
└── README.md
```

---

## 👥 3-Way Work Division & Collaboration Protocol

Direct pushes to `main` are strictly blocked. All contributions happen via pull requests created from feature branches.

| Member | GitHub Handle | Primary Scope | Branch Prefix | Agent Guide |
| :--- | :--- | :--- | :--- | :--- |
| **Tanmay Jain** | `@TanmayJain-dev` | Core Rule Engine, TinyFish Orchestration, Audit Trail, Case State | `feat/core-*` | [AGENT_TANMAY_CORE.md](.github/agents/AGENT_TANMAY_CORE.md) |
| **Prachi Bhalla** | `@pra27-06` | Next.js 15 UI, PDF claim correction, Visual Evidence Dossier, Human Review | `feat/ui-*` | [AGENT_PRACHI_FRONTEND.md](.github/agents/AGENT_PRACHI_FRONTEND.md) |
| **Garv Goyal** | `@garvgoyal01` | PyMuPDF/OCR parsing, GSTIN Checksum Validator, Arithmetic Engine, Test Fixtures | `feat/ingestion-*` | [AGENT_GARV_INGESTION.md](.github/agents/AGENT_GARV_INGESTION.md) |

---

## 🚀 Quickstart & Development

### Prerequisites
- Python 3.12+
- Node.js 20+ & `pnpm`
- (Optional) `TINYFISH_API_KEY` from [agent.tinyfish.ai](https://agent.tinyfish.ai/api-keys). If omitted, the engine automatically operates in deterministic `SIMULATED` mode with zero external dependencies.

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run automated unit tests
pytest

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
API docs available at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
pnpm install
pnpm dev
```
Web dashboard available at: `http://localhost:3000`

---

## 🔒 Security & Data Minimization
- Bank account numbers are masked in all logs, UI displays, and external prompts (`XXXX-XXXX-1234`).
- IFSC verification checks branch and bank entity existence; it is **never** overclaimed as proof of account ownership.
- Format-valid GSTINs are tested via Modulo 36 checksum calculation; active status is never assumed without authoritative live proof.
- Webpage content gathered via TinyFish is treated as untrusted data and strictly bounded from altering recommendation rules.

---

## 📄 License
MIT License. Built with pride by Team Astra-X for HackIIITD (Esya '26).
