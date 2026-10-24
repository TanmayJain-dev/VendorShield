# VendorShield AI — REST API Specification

Base URL: `http://localhost:8000/api`

All responses follow standard HTTP status codes. Unhandled exceptions return `500 Internal Server Error`, while policy or state-machine validation errors return `400 Bad Request` or `422 Unprocessable Content`.

---

### 1. `POST /api/cases`
Upload an invoice file (PDF/PNG/JPEG) or submit invoice claims to initialize a new verification case.

**Request (`multipart/form-data`):**
- `file`: PDF or image file (optional if submitting form fields)
- `supplier_name`: string (e.g. `"Apex Courier"`)
- `legal_name`: string (optional, e.g. `"Apex Courier Pvt Ltd"`)
- `gstin`: string (optional, e.g. `"07AAAAA0000A1Z5"`)
- `invoice_number`: string (optional, e.g. `"INV-2026-8841"`)
- `invoice_date`: string (optional, e.g. `"2026-10-20"`)
- `taxable_amount`: float (optional, e.g. `100000.00`)
- `cgst`: float (optional, e.g. `9000.00`)
- `sgst`: float (optional, e.g. `9000.00`)
- `igst`: float (optional, e.g. `0.00`)
- `total_amount`: float (optional, e.g. `118000.00`)

**Response (`201 Created`):**
Returns the full initialized `Case` object in `SUBMITTED` or `PARSED` status.

---

### 2. `GET /api/cases`
List summaries of all created cases for dashboard display, ordered chronologically.

**Response (`200 OK`):**
Array of `CaseSummary` objects containing `case_id`, `case_reference`, `supplier_name`, `invoice_number`, `total_amount`, `status`, `recommendation`, `created_at`, `risk_score`.

---

### 3. `GET /api/cases/{case_id}`
Retrieve complete case dossier including invoice claims, discovered evidence items, forensic risk assessment, review sign-off, and audit digest.

**Response (`200 OK`):**
Returns canonical `Case` object.

---

### 4. `PATCH /api/cases/{case_id}/invoice`
Allows a reviewer to correct OCR/parsed fields (e.g. correcting supplier name, GSTIN, or tax amounts). Automatically triggers a fresh forensic assessment over the corrected data.

**Request (`application/json`):**
```json
{
  "corrected_supplier_name": "Apex Courier",
  "corrected_gstin": "07AAAAA0000A1Z5",
  "correction_notes": "Corrected OCR trade alias"
}
```

**Response (`200 OK`):**
Returns updated `Case` with recomputed assessment and recalculation audit event.

---

### 5. `POST /api/cases/{case_id}/investigate`
Executes bounded 4-hop multi-hop investigation via TinyFish API (or deterministic simulated demonstration fixtures if `TINYFISH_API_KEY` is not configured). Automatically runs the 5-vector forensic risk engine and computes potential ITC exposure.

**Research Traversal:**
- **Hop 1:** Entity & Constitution Verification (GSTN / MCA)
- **Hop 2:** Director Portfolio & Shell Contagion Traversal (DIN / MCA Section 248)
- **Hop 3:** Geolocation Grounding & Address Hub Analysis (Ghost Hub detection)
- **Hop 4:** Regulatory, NCLT & Litigation Sweep (Insolvency / IBC)

**Response (`200 OK`):**
Returns updated `Case` in `READY_FOR_REVIEW` status (or `RESOLVED` / `BLOCKED`) with populated `evidence_items`, `assessment.forensic_vectors`, and `assessment.itc_exposure`.

---

### 6. `POST /api/cases/{case_id}/review`
Records an authorized human reviewer's final decision with mandatory rationale.

**Security & Identity Trust Boundary:**
- **Authentication Headers:** `Authorization: Bearer <token>` or `X-Reviewer-Token: <token>`.
- In production (`ENVIRONMENT=production`), unsafe dev defaults are strictly rejected; valid token required.
- In authenticated mode, caller-supplied `reviewer_id` and `reviewer_role` CANNOT override the server-authenticated identity (`authorized_ap_reviewer`).
- In local development mode (`REVIEWER_DEV_MODE=True`), requests without tokens are permitted and explicitly tagged as `dev_unauthenticated:<id>` in audit logs.

**Request (`application/json`):**
```json
{
  "action": "APPROVE",
  "rationale": "Verified supplier constitution on GST portal and clean promoter graph.",
  "requested_documents": []
}
```

Allowed actions: `APPROVE`, `APPROVE_WITH_EXCEPTION`, `REJECT`, `REQUEST_DOCUMENTS`, `ESCALATE`.

**Response (`200 OK`):**
Returns updated `Case` with server-generated `action_id`, audit hash, and status transition.

---

### 7. `GET /api/cases/{case_id}/report`
Exports a human-readable due-diligence audit report in Markdown format (`text/markdown; charset=utf-8`).

---

### 8. `GET /api/cases/{case_id}/audit-trail`
Retrieves the complete cryptographically chained tamper-evident audit trail for the case (`application/json`). Each event contains `event_id`, `event_type`, `actor`, `actor_role`, `timestamp`, `event_hash`, and `prev_hash`.
