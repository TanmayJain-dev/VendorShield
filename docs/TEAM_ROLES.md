# VendorShield AI — Official Team Roles & Responsibility Directory

> **Project:** VendorShield AI  
> **Repository:** `https://github.com/TanmayJain-dev/VendorShield.git`  
> **Event:** HackIIITD (Esya '26, IIIT Delhi)  

---

## 1. Official Role Assignments

```
┌────────────────────────────────────────────────────────────────────────┐
│                              TEAM ASTRA-X                              │
├────────────────────────────────┬───────────────────────────────────────┤
│ Tanmay Jain                    │ Team Lead + Tech Lead                 │
│ Prachi Bhalla                  │ Problem Research + Product Strategy   │
│                                │ + User Experience                     │
│ Garv Goyal                     │ Risk Research + Validation + Impact   │
└────────────────────────────────┴───────────────────────────────────────┘
```

---

## 2. Detailed Member Profiles & Responsibilities

### 2.1 Tanmay Jain — Team Lead + Tech Lead
- **Primary Domain:** End-to-end system architecture, technical leadership, core codebase integrity, and mentor technical defense.
- **Key Responsibilities:**
  - Overall project direction, coordination, task sequencing, and technical decision-making.
  - Deep, comprehensive understanding of the entire monorepo: FastAPI backend, Next.js frontend, database models, TinyFish integration, evidence reconciler, rule engine, and audit trail.
  - Understand how all modules interconnect and identify architectural bottlenecks or vulnerabilities.
  - Lead code reviews, system debugging, component integration, and automated testing.
  - Research technical enhancements and clearly explain technical trade-offs (e.g., SQLite vs. PostgreSQL, synchronous vs. asynchronous web agents, deterministic logic vs. generative wrappers).
  - Prepare answers for mentor questions regarding architecture, scalability, reliability, data security, and implementation choices.
- **Primary Deliverables:**
  - Working, verified monorepo with passing tests and production builds.
  - Technical architecture specifications and API contracts (`docs/ARCHITECTURE.md`, `docs/API_SPEC.md`).
  - Technical defense briefing sheet for mentor evaluations.

### 2.2 Prachi Bhalla — Problem Research + Product Strategy + User Experience
- **Primary Domain:** Real-world problem validation, customer persona definition, enterprise workflow alignment, and user journey.
- **Key Responsibilities:**
  - Research accounts payable vendor fraud, invoice verification pain points, and existing market alternatives (e.g., Coupa, SAP Ariba, Tipalti, Manual 3-Way Matching).
  - Define target customer personas (AP clerks, AP managers, CFOs, Compliance auditors) and map their end-to-end operational workflows.
  - Research competitors and identify VendorShield's true differentiators (evidence-first, deterministic fail-closed logic, live web corroboration) vs. generic AI wrappers.
  - Validate the market problem statement, value proposition, and business ROI (e.g., ITC savings, fraud prevention, reduction in manual verification hours).
  - Design and refine the user experience: dashboard queue, evidence dossier inspection, and manual claim correction workflows.
  - Prepare mentor answers on market relevance, customer adoption, business viability, and measurable impact metrics.
- **Primary Deliverables:**
  - Product strategy and competitive differentiation analysis.
  - User journey mapping and dashboard usability feedback.
  - Business and product mentoring Q&A briefing sheet.

### 2.3 Garv Goyal — Risk Research + Validation + Impact
- **Primary Domain:** Fraud threat modeling, risk rule design, test scenario validation, and responsible AI governance.
- **Key Responsibilities:**
  - Research real-world vendor fraud patterns: shell company creation, GST revocation, duplicate billing, trade-alias misdirection, and arithmetic manipulation.
  - Evaluate false positive vs. false negative trade-offs across compliance rules and determine when fail-closed actions (`MANUAL_REVIEW`, `BLOCK`) are required.
  - Distinguish authoritative primary sources (official GSTN registry, MCA) from weak signals (unverified blogs, search snippets) and enforce strict evidence requirements.
  - Develop comprehensive test scenarios, benchmark cases, edge cases, and regression fixtures.
  - Assess data privacy (bank account masking), upload security, explainability, auditability, and responsible AI practices.
  - Research system performance measurement without making unsupported accuracy claims (avoiding uncalibrated "99.9% fraud detection" statements).
  - Prepare mentor answers on system limitations, risk scoring methodology, verification boundaries, human oversight, and impact measurement.
- **Primary Deliverables:**
  - Comprehensive risk rule specifications and boundary conditions.
  - Synthetic test fixtures and edge-case regression matrix (`sample_data/`).
  - Risk governance and validation mentoring Q&A briefing sheet.

---

## 3. Leadership & Decision Matrix

| Decision Domain | Leading Role | Collaborating Roles |
| :--- | :--- | :--- |
| **System Architecture & Stack Selection** | Tanmay Jain | Garv Goyal (Risk/Storage), Prachi Bhalla (UX needs) |
| **Product Roadmap & Feature Prioritization** | Prachi Bhalla | Tanmay Jain (Feasibility), Garv Goyal (Impact) |
| **Risk Scoring Model & Rule Thresholds** | Garv Goyal | Tanmay Jain (Engine code), Prachi Bhalla (User clarity) |
| **User Experience & Dossier Visuals** | Prachi Bhalla | Tanmay Jain (API integration) |
| **Security & Privacy Invariants** | Garv Goyal & Tanmay Jain | Prachi Bhalla (Operational usability) |
| **Test Fixtures & Edge-Case Coverage** | Garv Goyal | Tanmay Jain (CI execution) |
| **Mentor Pitch & Storyline** | Prachi Bhalla & Tanmay Jain | Garv Goyal (Technical/risk defense) |

---

## 4. Cross-Functional Responsibility Matrix (RACI)

- **R = Responsible** (Does the work)
- **A = Accountable** (Final sign-off / decision owner)
- **C = Consulted** (Provides input)
- **I = Informed** (Kept updated)

| Activity / Area | Tanmay Jain | Prachi Bhalla | Garv Goyal |
| :--- | :---: | :---: | :---: |
| **Codebase & Architecture** | **A / R** | C | C |
| **FastAPI Backend & Persistence** | **A / R** | I | C |
| **Frontend UI & Dossier Experience** | C | **A / R** | C |
| **Problem Research & Market Sizing** | C | **A / R** | C |
| **Risk Rules & Fraud Scenarios** | C | C | **A / R** |
| **TinyFish Integration Architecture** | **A / R** | I | C |
| **Test Scenarios & Regression Matrix** | C | I | **A / R** |
| **Security & Data Minimization** | **A / R** | I | **R** |
| **Mentor Q&A Preparation** | **A / R** | **A / R** | **A / R** |
