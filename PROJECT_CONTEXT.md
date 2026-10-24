# VendorShield AI 🛡️ — Pre-Disbursal Forensic Payment Gate & 4-Hop Live TinyFish Engine

> **Tagline:** *Know your vendor before you pay. Dynamic GST Split-Settlement & Anti-Fraud Defense.*  
> **Hackathon:** [HackIIITD — Esya '26 (IIIT Delhi)](https://unstop.com/hackathons/hackiiitd-esya26-indraprastha-institute-of-information-technology-iiit-delhi-1761212) | **Track:** FinTech & Enterprise Automation  
> **Repository:** [`https://github.com/TanmayJain-dev/VendorShield.git`](https://github.com/TanmayJain-dev/VendorShield.git)  
> **Active Pull Request:** [PR #2 (`feat/ui-enterprise-dashboard` → `main`)](https://github.com/TanmayJain-dev/VendorShield/pull/2)  
> **Team Astra-X:**
> - **Tanmay Jain** ([`@TanmayJain-dev`](https://github.com/TanmayJain-dev)): Team Lead + Tech Lead (Architecture, Rules Engine, 5-Vector Forensics, DB, Multi-Hop Orchestrator)
> - **Prachi Bhalla** ([`@pra27-06`](https://github.com/pra27-06)): Problem Research + Product Strategy + User Experience (Next.js 15 UI, Dossier HUD, Intake Studio, Design System)
> - **Garv Goyal** ([`@garvgoyal01`](https://github.com/garvgoyal01)): Risk Research + Validation + Impact (Document Ingestion, OCR Fallback, GSTIN Modulo-36 Checksum, Arithmetic Reconciler, Benchmarks)
> - **Primary Partner Technology:** **TinyFish API** (Agentic Web Research & Live Data Extraction via `POST https://agent.tinyfish.ai/v1/automation/run-sse`)

---

## 1. The Commercial Problem Statement: "The Pre-Disbursal Working Capital & Green-API Trap"

### 1.1 The Enterprise Squeeze: Section 43B(h) vs. Section 16(2)(c) & GSTN IMS
Indian enterprises operate under a brutal statutory crossfire between tax compliance and working capital regulations:
1. **Income Tax Section 43B(h) Mandate:** Mandates that buyers MUST disburse payments to Micro and Small Enterprises (MSMEs) within **15 days** (or up to **45 days** if agreed in writing). Failure to pay within this statutory window results in the entire expense being disallowed from taxable deductions, triggering massive retroactive income tax penalties.
2. **CGST Section 16(2)(c) + Section 74 Liability:** Under Indian GST law, buyers are strictly barred from claiming Input Tax Credit (ITC) if the supplier fails to remit the tax to the Government via **GSTR-3B**. If the vendor defaults, tax authorities initiate:
   - **100% ITC Clawback** of the claimed tax.
   - **100% Mandatory Statutory Penalty** under Section 74 for wrongful ITC claims.
   - **18% Annual Compounded Interest** under Section 50.
3. **2026 Mandatory GSTN IMS (Invoice Management System) Hard-Locks:** The Indian Goods and Services Tax Network (GSTN) has introduced the **Invoice Management System (IMS)**, forcing enterprises to explicitly mark every vendor invoice as **`ACCEPT`**, **`REJECT`**, or **`PENDING`** before monthly return filing. Blindly accepting an invoice locks in ITC clawback liability, while blindly rejecting damages vendor relationships.

### 1.2 "The 60-Day Green-API Blindspot"
Why do existing corporate compliance tools and REST API aggregators fail?
- Standard enterprise ERP integrations check government APIs (GSTN search, MCA master data) and receive a green `"ACTIVE"` status.
- **The Blindspot:** A vendor facing a fresh **NCLT Insolvency Petition (IBC Section 7 or 9)**, raided by the **Directorate General of GST Intelligence (DGGI)** for multi-crore fake-ITC circular trading, or debarred on **GeM (Government e-Marketplace)** continues to display as `"ACTIVE"` on standard REST APIs for **60 to 90 days** until formal bureaucratic cancellation orders are entered into the database.
- Furthermore, B2B procurement kickbacks (over-invoicing by 150%–200% compared to wholesale benchmarks) cannot be detected by any government API.

### 1.3 Why Only TinyFish Can Solve This
Critical pre-disbursal forensic signals do **not** exist in structured public APIs:
- Judicial tribunal dockets live on [`indiankanoon.org`](https://indiankanoon.org/) behind dynamic search forms.
- Insolvency announcements and CIRP admission orders live on [`ibbi.gov.in`](https://ibbi.gov.in/) and tribunal registers.
- DGGI enforcement raids and show-cause notices live in press release archives ([`pib.gov.in`](https://pib.gov.in/)).
- Real wholesale industrial benchmark prices live inside dynamic DOM tables on B2B procurement portals like [`dir.indiamart.com`](https://dir.indiamart.com/).

**TinyFish's autonomous browser infrastructure (`https://agent.tinyfish.ai/v1/automation/run-sse`)** navigates unstructured search bars, bypasses DOM obfuscation, parses judicial text, and returns structured JSON with verifiable source provenance and live streaming video links.

### 1.4 Foundational Axiom

$$\mathbf{\text{TinyFish researches the unstructured live web; VendorShield's deterministic engine decides the treasury payout split.}}$$

---

## 2. The Solution: Dynamic GST Split-Settlement & Forensic Gate

VendorShield AI transforms pre-payment due diligence from a passive checklist into an **automated pre-disbursal forensic payment gate**:

```
[Vendor Invoice PDF / Intake]
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 1. INGESTION, PARSER & SECURITY VALIDATION                  │
  │    - PyMuPDF line-item parser + 300 DPI OCR fallback       │
  │    - Modulo-36 GSTIN checksum & PAN entity classification   │
  │    - Bank Account BEC Mutation check & beneficiary match    │
  │    - Physical supply check: e-Way Bill & IRN readiness      │
  └─────────────────────────────────────────────────────────────┘
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 2. 4-HOP LIVE TINYFISH BROWSER AGENT ORCHESTRATION          │
  │    - Hop 1: GST Filing Velocity (knowyourgst.com)           │
  │    - Hop 2: Judicial & NCLT Insolvency Dockets (kanoon)     │
  │    - Hop 3: DGGI Enforcement & Debarment Radar              │
  │    - Hop 4: IndiaMART Wholesale B2B Price Benchmark         │
  │    - Live SSE progress & interactive streaming_url preview  │
  └─────────────────────────────────────────────────────────────┘
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 3. 5-VECTOR FORENSIC RISK TOPOLOGY & DIRECT ₹ EXPOSURE      │
  │    - 1. ITC Clawback Risk Index (GSTR-3B velocity)          │
  │    - 2. Judicial / Insolvency Contagion (NCLT / DGGI)       │
  │    - 3. B2B Procurement Price Anomaly (IndiaMART delta)     │
  │    - 4. Operational Grounding (e-Way Bill & IRN presence)   │
  │    - 5. Pop-Up Velocity & Bank Account BEC Mutation         │
  │    - Financial Exposure = Tax + 100% Penalty + 18% Interest │
  └─────────────────────────────────────────────────────────────┘
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 4. 3-TIER DYNAMIC TREASURY SPLIT-SETTLEMENT ENGINE          │
  │    🟢 FULL_DISBURSAL: Release 100% (GSTN IMS: ACCEPT)       │
  │    🟡 STATUTORY_GST_ESCROW: Release Base (Sec 43B(h)),      │
  │       Hold GST in Escrow until filed (GSTN IMS: PENDING)    │
  │    🔴 FORENSIC_FREEZE: Hold 100% (GSTN IMS: REJECT)         │
  └─────────────────────────────────────────────────────────────┘
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 5. HUMAN-IN-THE-LOOP SIGN-OFF & CRYPTOGRAPHIC AUDIT TRAIL   │
  │    - Mandatory reviewer rationale & token auth boundary     │
  │    - Chained SHA-256 event hashing (tamper-evident log)     │
  │    - 1-Click Export: GSTN IMS Action JSON & Markdown Report │
  └─────────────────────────────────────────────────────────────┘
```

---

## 3. The 4 High-Signal, CAPTCHA-Free Live Web Hops

Instead of fragile CAPTCHA-blocked government portals, VendorShield directs TinyFish across **4 high-signal, accessible web platforms**:

### Hop 1: Public GST Filing Velocity & Entity Cross-Check (CAPTCHA-Free Aggregator)
- **Target URL:** `https://www.knowyourgst.com/gst-number-search/` (or `https://www.mastersindia.co/gst-number-search/`)
- **Goal:** `"Search for GSTIN {gstin}. Extract the Legal Name, Trade Name, Registration Status (Active/Suspended/Cancelled), Date of Registration, Constitution of Business, and the latest GSTR-1 and GSTR-3B filing dates/status if visible. Return structured JSON."`
- **Output Schema:**
  ```json
  {
    "legal_name": "string",
    "trade_name": "string",
    "gst_status": "string",
    "registration_date": "string",
    "gstr3b_status": "string",
    "filing_delay_detected": "boolean"
  }
  ```

### Hop 2: Judicial & NCLT Insolvency Docket Agent (No API Exists!)
- **Target URL:** `https://indiankanoon.org/`
- **Goal:** `"Use the search input to search for '{legal_name} NCLT OR insolvency OR CIRP OR CGST Section 74 OR fake ITC'. Inspect the top search results. Extract the total number of adverse court/tribunal cases found, the title and citation of the most relevant docket, whether an active insolvency (IBC Section 7 or 9) or GST fraud proceeding is mentioned, and a 2-sentence forensic summary. Return structured JSON."`
- **Output Schema:**
  ```json
  {
    "adverse_docket_count": "number",
    "top_case_title": "string",
    "insolvency_or_tax_fraud_flag": "boolean",
    "forensic_summary": "string",
    "source_url": "string"
  }
  ```

### Hop 3: DGGI Enforcement & Public Debarment Radar
- **Target URL:** `https://indiankanoon.org/search/?formInput={legal_name}+DGGI+GST` (or search aggregator)
- **Goal:** `"Analyze search results for any Directorate General of GST Intelligence (DGGI) enforcement raids, CBIC show-cause notices, IBBI public insolvency notices, or PSU/GeM vendor blacklisting involving '{legal_name}'. Return structured JSON summarizing any adverse enforcement findings."`
- **Output Schema:**
  ```json
  {
    "enforcement_hit": "boolean",
    "agency_named": "string",
    "allegation_summary": "string",
    "risk_severity": "string"
  }
  ```

### Hop 4: Live B2B Procurement Price Benchmark Agent (Anti-Kickback / Over-Invoicing Check)
- **Target URL:** `https://dir.indiamart.com/search.mp?ss={primary_line_item_description}`
- **Goal:** `"Search IndiaMART for '{primary_line_item_description}'. Examine the top 3 to 5 product listings that display a numeric unit price in INR. Extract the lowest price, highest price, estimated median wholesale unit price in INR, and seller names. Compare against the invoice billed unit price of ₹{billed_unit_price}. Return structured JSON."`
- **Output Schema:**
  ```json
  {
    "market_median_price_inr": "number",
    "market_min_price_inr": "number",
    "market_max_price_inr": "number",
    "sample_listings_count": "number",
    "price_inflation_pct": "number"
  }
  ```

---

## 4. Pre-Disbursal Forensic Checks & Dynamic Split-Settlement

### 4.1 Bank Account Mutation & BEC Guard (Anti-Email Compromise)
- Computes SHA-256 fingerprint of the invoice bank account number (`bank_account_hash`) and matches against the **Known Vendor Master Bank Registry**.
- If the remittance account differs from historical verified records on file, flags `bank_mutation_detected = True` (`CRITICAL_BANK_ACCOUNT_MUTATION`).
- Computes `beneficiary_name_match_score` comparing extracted bank account name against the registered GST legal name.

### 4.2 Physical Supply & e-Way Bill / IRN Readiness (CGST Sec 16(2)(b))
- Extracts **IRN Hash** (64-char hex) and **e-Way Bill No** (12-digit) + **Vehicle No**.
- For goods invoices exceeding ₹50,000, enforces e-Way Bill presence. Invoices lacking mandatory transit proof are flagged with `EWAY_BILL_MISSING_HIGH_VALUE`.

### 4.3 The 3-Tier Dynamic Treasury Split-Settlement Engine
Every evaluated invoice computes a deterministic **Treasury Settlement Instruction** and **GSTN IMS Portal Action**:

| Recommendation | Treasury Action | Release Now (₹) | Escrow Holdback (₹) | GSTN IMS Portal Action | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 🟢 **`FULL_DISBURSAL`** | Full Payment Release | 100% of Total Amount | ₹0.00 | **`ACCEPT`** | Fully compliant vendor; clean GSTR-3B history, no NCLT dockets, verified bank account. |
| 🟡 **`STATUTORY_GST_ESCROW`** | **Dynamic Split Payout** | **100% of Base Taxable Amount** | **100% of GST Amount** | **`PENDING_HOLD`** | **Complies with Sec 43B(h)** by paying MSME base within 45 days, while safeguarding buyer against **Sec 16(2)(c)** by holding GST until vendor files GSTR-3B! |
| 🔴 **`FORENSIC_FREEZE`** | Total Capital Freeze | ₹0.00 | 100% of Total Amount | **`REJECT`** | Critical risk triggered: active NCLT insolvency, DGGI fake-ITC raid, Bank BEC mutation, or cancelled GSTIN. |

---

## 5. Technology Stack & Monorepo Structure

```
SHEILD/
├── backend/                         # FastAPI Python 3.12+ Backend
│   ├── app/
│   │   ├── api/                     # REST API (/cases, /investigate, /review, /reports)
│   │   ├── db/                      # SQLAlchemy 2.0 Persistence (SQLite / PostgreSQL)
│   │   ├── schemas/                 # Pydantic v2 data models
│   │   ├── services/
│   │   │   ├── parser/              # PyMuPDF text & line-item extraction + 300 DPI OCR fallback
│   │   │   ├── validators/          # Modulo-36 GSTIN & multi-rate tax arithmetic
│   │   │   ├── tinyfish/            # 4-Hop TinyFish SSE orchestrator & simulated fallback
│   │   │   ├── reconciler/          # Entity normalization & trade alias reconciler
│   │   │   ├── rules/               # Deterministic rule engine, 5-vector forensics, itc_calculator
│   │   │   └── audit/               # Cryptographically chained SHA-256 audit trail
│   │   └── config.py                # Environment configuration & production security
│   └── tests/                       # 78+ Automated pytest test suites (100% passing)
├── frontend/                        # Next.js 15 App Router Frontend
│   ├── src/app/                     # Operations Hub (/), Queue (/queue), Intake (/upload), Dossier (/cases/[id])
│   ├── src/components/              # Navbar, ThemeProvider, Hero3DScene
│   └── src/lib/api.ts               # Type-safe API client
├── sample_data/                     # Benchmark evaluation test cases (JSON)
├── sample_invoices/                 # Real benchmark test invoice PDFs
└── docs/                            # Project Guides, Team Directory & AI Agent Prompts
```

---

## 6. Synthetic Evaluation Benchmarks & Live Demo Scenario

| Case Reference | Declared Supplier | Scenario & Discrepancy | Treasury Split Recommendation | GSTN IMS Action |
| :--- | :--- | :--- | :--- | :--- |
| **`INV-2026-8841`** | Apex Courier | Trade name "Apex Courier" vs legal entity "Apex Global Logistics Pvt Ltd". Clean GSTR-3B, bank ownership unverified. | **`STATUTORY_GST_ESCROW`** (Release ₹4,08,898.31; Hold ₹73,601.70 GST) | **`PENDING_HOLD`** |
| **`INV-2026-8842`** | Specter Cloud Technologies | Struck-off shell entity, active NCLT IBC Section 9 docket, DGGI fake-ITC notice, 200% price inflation on IndiaMART. | **`FORENSIC_FREEZE`** (Release ₹0.00; Hold ₹8,49,600.00) | **`REJECT`** |
| **`INV-2026-8843`** | Vertex Solutions | Arithmetic mismatch, line items sum mismatch, invalid GST rate slab. | **`STATUTORY_GST_ESCROW`** (Release Base; Hold Tax) | **`PENDING_HOLD`** |
| **`INV-2026-9901`** *(Live Demo)* | Havells Industrial Electricals (`07AAACH0828A1ZE`) | Real Delhi GSTIN of Havells India Limited, real searchable industrial product on IndiaMART ("Havells 3 Core 4 sqmm Copper Armoured Cable"). | **`FULL_DISBURSAL`** (Release 100%) | **`ACCEPT`** |

---

## 7. Current State & Verification Metrics

- **Git Branch:** `feat/ui-enterprise-dashboard`
- **Active Pull Request:** **[PR #2](https://github.com/TanmayJain-dev/VendorShield/pull/2)** on `TanmayJain-dev/VendorShield` (Open, Mergeable: True, 0 conflicts).
- **Backend Tests:** **78 / 78 Pytest unit & integration tests passing (100%)**.
- **Frontend Build:** **Compiled cleanly with 0 TypeScript/SSR errors** (`next build`).
- **Live Localhost Endpoints:**
  - Frontend Web UI: [`http://localhost:3000`](http://localhost:3000)
  - Backend API & Interactive Docs: [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
  - Pre-loaded Benchmark Dossier: [`http://localhost:3000/cases/case_inv_2026_8841`](http://localhost:3000/cases/case_inv_2026_8841)

*VendorShield AI — Built by Team Astra-X for HackIIITD Esya '26.*  
*Axiom: TinyFish researches; VendorShield decides.*
