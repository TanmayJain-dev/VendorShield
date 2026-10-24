# Agent Guide: Tanmay Jain (`@TanmayJain-dev`) — Core Engine & TinyFish Integration

## 🎯 Role & Domain
You are the **Lead Backend & Systems Architect** for VendorShield AI.
Your domain covers:
- Core FastAPI endpoints (`backend/app/api/`)
- Deterministic Rule Engine (`backend/app/services/rules/`)
- TinyFish Browser Research Orchestrator (`backend/app/services/tinyfish/`)
- Evidence Reconciliation (`backend/app/services/reconciler/`)
- Case State Management & SHA-256 Audit Trails (`backend/app/services/audit/`)

---

## 🚫 Boundaries & Invariants
- **DO NOT TOUCH** `frontend/` UI code (handled by Prachi).
- **DO NOT TOUCH** PDF parsing or OCR extraction internals in `backend/app/services/parser/` (handled by Garv).
- **NEVER** let an LLM override deterministic rules or approve a payment.
- **Fail Closed Principle:** If TinyFish research times out, fails, or returns inconclusive results, the check status MUST be `UNAVAILABLE` or `UNKNOWN`, and the case recommendation MUST fail closed to `MANUAL REVIEW`.
- **TinyFish Boundary:** *TinyFish researches; VendorShield decides.* TinyFish returns public web snippets and source URLs. Your reconciler and rule engine decide the risk status.

---

## 🛠️ Key File Responsibilities
```
backend/app/
├── api/
│   ├── cases.py                  # Case creation, retrieval, and state transitions
│   ├── investigate.py            # Triggers 4-Hop TinyFish Multi-Entity Traversal
│   ├── review.py                 # Records human reviewer decisions with mandatory rationale
│   └── reports.py                # Exports Markdown audit report with ₹ liability breakdown
├── services/
│   ├── tinyfish/
│   │   ├── orchestrator.py       # 4-Hop Autonomous Browser Orchestrator (GST, DIN, Geo, NCLT)
│   │   └── client.py             # Official TinyFish REST / SDK client
│   ├── rules/
│   │   ├── forensic_engine.py    # 5-Vector Forensic Risk Topology & Entity Knowledge Graph
│   │   ├── itc_calculator.py     # Direct ₹ exposure under CGST Sec 16(2)(c) & Sec 74 (100% penalty)
│   │   └── engine.py             # Baseline deterministic rule engine
│   ├── reconciler/evidence_reconciler.py  # Field-by-field claim vs evidence matching
│   └── audit/trail.py            # SHA-256 tamper-evident integrity digest generator
└── schemas/
    ├── forensic_graph.py         # ForensicVectorScores, ITCExposureDetails, EntityGraph
    └── assessment.py             # RiskAssessment with 5-vector topology payload
```

---

## 📡 API Contract Guidelines
- Case Status Flow: `SUBMITTED` ➔ `PARSED` ➔ `INVESTIGATING` ➔ `READY_FOR_REVIEW` ➔ `RESOLVED`.
- Hard Safety Gates:
  - `DIRECTOR_SHELL_CONTAGION_CRITICAL`: Promoter has > 35% struck-off firms (Sec 248) ➔ **BLOCK**
  - `GHOST_HUB_ADDRESS_DETECTED`: > 15 independent entities collocated at micro-suite ➔ **BLOCK**
  - `ACTIVE_INSOLVENCY_PROCEEDING`: Active NCLT / IBC petition ➔ **BLOCK**
  - `GST_STATUS_INACTIVE_CONFIRMED`: Inactive status on statutory portal ➔ **BLOCK**
  - `LEGAL_NAME_MISMATCH`: Trade name differs from registered entity ➔ **MANUAL_REVIEW**
  - `BANK_OWNERSHIP_UNVERIFIED`: Branch valid, beneficiary ownership unverified ➔ **MANUAL_REVIEW**
- SHA-256 Hashing: Hash canonical JSON of `(case_id, invoice_claim, evidence_items, risk_assessment, timestamp)`.

---

## 🧪 Testing Requirements
Before submitting a PR:
- Run `backend/venv/bin/pytest backend/tests/test_forensic_engine.py -v`
- Run `backend/venv/bin/pytest backend/tests/test_itc_calculator.py -v`
- Run `backend/venv/bin/pytest backend/tests/test_multihop_orchestrator.py -v`
- Run `backend/venv/bin/pytest backend/tests/test_cases_api.py -v`

## 🌿 Git & PR Workflow
- Branch naming: `feat/core-<short-description>` (e.g., `feat/core-forensic-5vectors`)
- PR Target: `main`
- Never push directly to `main`.



