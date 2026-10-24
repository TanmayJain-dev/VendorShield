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
│   ├── cases.py          # Case creation, retrieval, and state transitions
│   ├── investigate.py    # Trigger TinyFish web investigation
│   └── review.py         # Record human reviewer decisions with rationale
├── services/
│   ├── tinyfish/client.py        # Verified TinyFish API / SDK client with fallback simulator
│   ├── reconciler/evidence_reconciler.py  # Field-by-field claim vs evidence matching
│   ├── rules/engine.py           # 3-tier risk model: hard gates, risk scoring, reason codes
│   └── audit/trail.py            # SHA-256 evidence hashing, audit events, PDF/markdown export
└── schemas/                      # Canonical Pydantic contracts
```

---

## 📡 API Contract Guidelines
- Case Status Flow: `SUBMITTED` ➔ `PARSED` ➔ `INVESTIGATING` ➔ `READY_FOR_REVIEW` ➔ `RESOLVED`.
- Hard Gates (Auto-Review/Block regardless of score):
  - `GSTIN_FORMAT_INVALID`: Review/Block
  - `GST_STATUS_INACTIVE_CONFIRMED`: Block
  - `LEGAL_NAME_MISMATCH`: Review (requires alias clarification)
  - `EVIDENCE_INSUFFICIENT`: Review
  - `BANK_OWNERSHIP_UNVERIFIED`: Review (IFSC alone cannot verify ownership)
- SHA-256 Hashing: Hash canonical JSON of `(case_id, invoice_claim, evidence_items, risk_assessment, timestamp)`.

---

## 🧪 Testing Requirements
Before submitting a PR:
- Run `pytest backend/tests/test_rules_engine.py`
- Run `pytest backend/tests/test_tinyfish_service.py`
- Run `pytest backend/tests/test_cases_api.py`

## 🌿 Git & PR Workflow
- Branch naming: `feat/core-<short-description>` (e.g., `feat/core-tinyfish-orchestrator`)
- PR Target: `main`
- Never push directly to `main`.
