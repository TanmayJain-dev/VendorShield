# VendorShield AI 🛡️

> **Tagline:** *Know your vendor before you pay.*  
> **Hackathon:** [HackIIITD — Esya '26 (IIIT Delhi)](https://unstop.com/hackathons/hackiiitd-esya26-indraprastha-institute-of-information-technology-iiit-delhi-1761212) | **Track:** FinTech & Enterprise Automation  
> **Team Astra-X:** Tanmay Jain (`@TanmayJain-dev`), Prachi Bhalla (`@pra27-06`), Garv Goyal (`@garvgoyal01`)  
> **Partner Technology:** **TinyFish API** (Agentic Web Research & Live Data Extraction)

---

## 📌 Executive Summary

**VendorShield AI** is an evidence-first vendor due-diligence and risk mitigation platform for Accounts Payable (AP) and finance operations teams.

When a supplier invoice is received, VendorShield:
1. **Extracts Claims:** Converts invoice PDF / intake data into structured claims (Trade Name, Legal Name, GSTIN, Address, Line Items, Bank/IFSC details).
2. **Researches Public Footprint via TinyFish:** Orchestrates bounded, live-web browser investigations across public registries, corporate directories, and web footprints using the **TinyFish API**.
3. **Deterministically Reconciles:** Compares invoice claims against discovered web evidence field-by-field using normalized corporate identifiers and strict mathematical rules.
4. **Delivers an Explainable Dossier:** Categorizes findings into **Verified Facts**, **Potential Discrepancies**, and **Unknown/Unverified** items, recommending an outcome: **`PASS`**, **`MANUAL REVIEW`**, or **`BLOCK`**.
5. **Enforces Human-in-the-Loop Sign-Off:** Requires authorized human sign-off with rationale, exporting a timestamped, SHA-256 cryptographically hashed audit trail.

> **Core Axiom:** *TinyFish researches; VendorShield decides.*  
> The browser agent is an evidence collector, not a final fraud arbiter. Deterministic rules govern the recommendation. Weak, conflicting, or unreachable evidence fails closed to **`MANUAL REVIEW`**.

---

## 🏗️ Architecture & Monorepo Structure

```
VendorShield/
├── .github/
│   ├── workflows/ci.yml             # Automated CI: pytest + npm build on every PR
│   └── agents/                      # GitHub role instructions
├── backend/                         # FastAPI Python 3.12+ Backend
│   ├── app/
│   │   ├── api/                     # REST API endpoints (/cases, /investigate, /review, /reports)
│   │   ├── db/                      # SQLAlchemy 2 persistence (SQLite MVP, PostgreSQL ready)
│   │   ├── schemas/                 # Canonical Pydantic v2 data models
│   │   ├── services/
│   │   │   ├── parser/              # Document extraction & multi-rate tax calculations
│   │   │   ├── validators/          # Modulo-36 GSTIN checksum & invoice arithmetic
│   │   │   ├── tinyfish/            # TinyFish REST agent client & transparent fallback simulator
│   │   │   ├── reconciler/          # Field-by-field claim vs evidence matching & normalization
│   │   │   ├── rules/               # Deterministic rule engine & fail-closed hard gates
│   │   │   └── audit/               # Cryptographically chained SHA-256 audit logs
│   │   └── main.py                  # Server entrypoint with CORS & lifespan initialization
│   └── tests/                       # 33 Unit & integration tests
├── frontend/                        # Next.js 15 App Router Frontend (Tailwind, Lucide)
│   ├── src/app/                     # Dashboard (/), Upload (/upload), Dossier (/cases/[id])
│   ├── src/lib/                     # Type-safe API client (api.ts)
│   └── src/types/                   # TypeScript contracts matching backend schemas
├── sample_data/                     # Synthetic benchmark test invoices (INV-2026-8841, etc.)
├── docs/                            # Project Guides, Team Directory & AI Agent Prompts
│   ├── PROJECT_GUIDE.md             # Master project guide & architecture overview
│   ├── TEAM_ROLES.md                # Official team roles & RACI responsibility matrix
│   ├── START_AGENT_RESEARCH.md      # Reusable prompt template for AI agent onboarding
│   └── agents/                      # Personalized research guides for each team member
│       ├── TANMAY_AGENT_GUIDE.md    # Guide for Tanmay Jain (Team Lead + Tech Lead)
│       ├── PRACHI_AGENT_GUIDE.md    # Guide for Prachi Bhalla (Problem + Product + UX)
│       └── GARV_AGENT_GUIDE.md      # Guide for Garv Goyal (Risk + Validation + Impact)
├── .gitignore
└── README.md
```

---

## 👥 Team & AI Research Guides

Team members and external contributors can pass this repository URL along with their name to any AI research or coding assistant to immediately activate deep, role-specific onboarding and mentor preparation.

| Member | Official Role | GitHub Handle | Personalized Agent Guide |
| :--- | :--- | :--- | :--- |
| **Tanmay Jain** | **Team Lead + Tech Lead** | [`@TanmayJain-dev`](https://github.com/TanmayJain-dev) | [docs/agents/TANMAY_AGENT_GUIDE.md](docs/agents/TANMAY_AGENT_GUIDE.md) |
| **Prachi Bhalla** | **Problem Research + Product Strategy + User Experience** | [`@pra27-06`](https://github.com/pra27-06) | [docs/agents/PRACHI_AGENT_GUIDE.md](docs/agents/PRACHI_AGENT_GUIDE.md) |
| **Garv Goyal** | **Risk Research + Validation + Impact** | [`@garvgoyal01`](https://github.com/garvgoyal01) | [docs/agents/GARV_AGENT_GUIDE.md](docs/agents/GARV_AGENT_GUIDE.md) |

### 📚 Core Documentation Links
- 📖 **[Master Project Guide](docs/PROJECT_GUIDE.md):** Complete architecture, domain workflow, data flow, implemented vs. planned features, and technical glossary.
- 👥 **[Official Team Directory](docs/TEAM_ROLES.md):** Detailed role descriptions, RACI responsibility matrix, and decision ownership.
- ⚡ **[Quick-Start AI Agent Prompt](docs/START_AGENT_RESEARCH.md):** Copy-paste prompt template to activate an AI agent with repository inspection and 15+ mentor defense questions.

---

## 🚀 Quickstart & Development

### Prerequisites
- Python 3.12+
- Node.js 20+ & `npm`
- (Optional) `TINYFISH_API_KEY` from [agent.tinyfish.ai](https://agent.tinyfish.ai/api-keys). If omitted, the engine automatically operates in deterministic `SIMULATED` mode with zero external dependencies.

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows (or source venv/bin/activate on Unix)

# Install dependencies
pip install -r requirements.txt

# Run automated test suite (33 passing tests)
pytest

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
Interactive API documentation: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Verify TypeScript type checking
npx tsc --noEmit

# Verify Next.js production build
npm run build

# Start Next.js development server
npm run dev
```
Web application dashboard: `http://localhost:3000`

---

## 🔒 Security & Data Minimization
- **Banking Privacy:** Bank account numbers are masked in all logs, displays, and audit exports (`XXXX-XXXX-9921`).
- **Statutory Invariant:** IFSC verification checks branch and bank entity existence; it is **never** overclaimed as proof of account ownership.
- **Checksum Verification:** Format-valid GSTINs are tested via Modulo 36 checksum calculation; active status is never assumed without authoritative live proof.
- **Upload Hardening:** Maximum 10MB file limit, magic byte validation (PDF/PNG/JPEG), and filename sanitization against path traversal.
- **Tamper-Evident Chaining:** All case state changes and reviewer decisions are cryptographically chained using SHA-256 digests.

---

## 📄 License
MIT License. Built with pride by Team Astra-X for HackIIITD (Esya '26).
