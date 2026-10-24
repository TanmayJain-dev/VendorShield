# VendorShield AI — Architectural Specification

## 1. System Overview

VendorShield AI bridges unstructured supplier invoice documents and live public-web registry intelligence through a deterministic, fail-closed verification pipeline.

```
                      +-----------------------------+
                      |   Supplier Invoice (PDF)    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Document Ingestion        |
                      |   - PyMuPDF text extractor  |
                      |   - OCR fallback interface  |
                      +--------------+--------------+
                                     |
                         Extracted Invoice Claims
                                     |
                                     v
                      +-----------------------------+
                      |   Deterministic Validation  |
                      |   - GSTIN Regex & Mod-36    |
                      |   - Arithmetic Reconciliation
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | TinyFish Research Agent     |
                      | - Live browser search/scrape|
                      | - Fallback mock simulator   |
                      +--------------+--------------+
                                     |
                           Discovered Web Evidence
                                     |
                                     v
                      +-----------------------------+
                      |   Evidence Reconciler       |
                      |   - Field-by-field matching |
                      |   - Provenance tracking     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Deterministic Rule Engine |
                      |   - Hard gates              |
                      |   - Explainable reason codes|
                      |   - Pass / Review / Block   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Tactical Reviewer Dossier   |
                      | - Human-in-the-loop sign-off|
                      | - Cryptographic SHA-256 log |
                      +-----------------------------+
```

## 2. Core Architectural Axioms
1. **TinyFish researches; VendorShield decides:** The external browser agent collects public evidence and raw excerpts. VendorShield's own rule engine calculates risk and produces recommendations.
2. **Fail-Closed to Manual Review:** Missing evidence, timeouts, conflicting sources, or ambiguous trade vs legal entity names never default to PASS.
3. **Evidence Grounding:** Every claim compared must cite its source URL, retrieval timestamp, and raw excerpt.
4. **Data Minimization & Masking:** Bank account numbers are masked (`XXXX-XXXX-1234`). Only public vendor claims are queried over the web.

## 3. Technology Stack
- **Frontend:** Next.js 15, React 19, Tailwind CSS, Lucide icons, Sonner toasts.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, PyMuPDF (`fitz`), pytest.
- **External Integration:** TinyFish Agent API (`agent.tinyfish.ai/v1/automation/run` or `tinyfish` Python SDK).
- **Audit & Cryptography:** Python standard library `hashlib` (SHA-256 canonical event logs).
