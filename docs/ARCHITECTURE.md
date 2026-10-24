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
1. **TinyFish researches; VendorShield decides:** The external autonomous browser agent traverses stateful public portals (GSTN, MCA, Zauba, Maps, NCLT) to collect multi-hop relational evidence. VendorShield's deterministic forensic engine calculates risk topologies and recommendations.
2. **Beyond Surface Checklists:** Fraudulent shell vendors possess valid GSTINs and active portal status. VendorShield investigates relational topology: promoter shell contagion, address collocation density, operational grounding, and direct ₹ ITC clawback liability under CGST Section 16(2)(c).
3. **Fail-Closed to Manual Review:** Missing evidence, timeouts, conflicting sources, or ambiguous trade vs legal entity names never default to PASS.
4. **Evidence Grounding:** Every claim compared must cite its source URL, retrieval timestamp, and raw excerpt.
5. **Data Minimization & Masking:** Bank account numbers are masked (`XXXX-XXXX-1234`). Only public vendor claims are queried over the web.

## 3. The 4-Hop Autonomous Forensic Traversal
```
[Invoice Claim]
       │
       ▼ (Hop 1: Entity Discovery)
[GSTN / MCA Portal] ──────────► Legal Entity, Filing Status, Incorporation Date
       │
       ▼ (Hop 2: Director Graph Traversal)
[Zauba / Tofler / MCA] ───────► Promoters' DINs ──► Traverses all co-directorships
       │                                            - Struck-off company ratio (Sec 248)
       │                                            - Mule/Benami director detection
       ▼ (Hop 3: Physical Reality Check)
[Maps / Street View / GIS] ───► Address Collocation Density
       │                        - Are 40 other distinct GSTINs registered in the same room?
       │                        - Is a heavy goods supplier registered in a residential tea stall?
       ▼ (Hop 4: Litigation & Insolvency Sweep)
[eCourts / NCLT / GeM] ───────► Section 7/9 IBC insolvency petitions, debarment records
```

## 4. The 5-Vector Forensic Risk Topology
1. **ITC Clawback Risk Index:** Computes statutory liability under CGST Section 16(2)(c) & Section 74 (100% mandatory penalty + 18% p.a. interest).
2. **Director Shell Contagion Score:** Ratio of struck-off / suspended sister entities in the promoter's corporate graph.
3. **Address Collocation Density:** "Ghost Hub" detection: count of unrelated commercial entities registered at the identical micro-suite.
4. **Operational Grounding Score:** Premises classification (Industrial/Warehouse vs Residential/Virtual) vs claimed invoice goods.
5. **Pop-Up Velocity Factor:** Newly incorporated entity with immediate high-value billing volume.

## 5. Technology Stack
- **Frontend:** Next.js 15, React 19, Tailwind CSS, Lucide icons, Sonner toasts.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, PyMuPDF (`fitz`), pytest.
- **External Integration:** TinyFish Agent API (`agent.tinyfish.ai/v1/automation/run` or `tinyfish` Python SDK).
- **Audit & Cryptography:** Python standard library `hashlib` (SHA-256 canonical event logs).

