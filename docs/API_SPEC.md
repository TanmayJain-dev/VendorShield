# VendorShield AI — REST API Specification

Base URL: `http://localhost:8000/api`

---

### 1. `POST /api/cases`
Upload an invoice file (PDF/CSV) or submit raw claims to initialize a new verification case.

**Request (Multipart Form Data):**
- `file`: PDF or image file (optional if submitting JSON payload)
- `supplier_name`: string (e.g. `"Apex Courier"`)
- `gstin`: string (optional, e.g. `"07AAAAA0000A1Z5"`)
- `invoice_number`: string (optional, e.g. `"INV-2026-8841"`)
- `total_amount`: float (optional, e.g. `482500.00`)

**Response (`201 Created`):**
```json
{
  "case_id": "case_inv_2026_8841",
  "status": "PARSED",
  "created_at": "2026-10-24T07:45:00Z",
  "invoice": {
    "invoice_number": "INV-2026-8841",
    "supplier_name": "Apex Courier",
    "gstin": "07AAAAA0000A1Z5",
    "total_amount": 482500.00,
    "gstin_format_valid": true,
    "arithmetic_valid": true
  }
}
```

---

### 2. `GET /api/cases/{case_id}`
Retrieve complete case details including invoice claims, discovered evidence, and latest assessment.

---

### 3. `PATCH /api/cases/{case_id}/invoice`
Allow reviewer to correct OCR/parsed fields before investigation starts.

**Request:**
```json
{
  "corrected_supplier_name": "Apex Courier",
  "corrected_gstin": "07AAAAA0000A1Z5"
}
```

---

### 4. `POST /api/cases/{case_id}/investigate`
Trigger bounded live-web research via TinyFish API (or simulated fixtures if API key not set).

**Response (`200 OK`):**
```json
{
  "case_id": "case_inv_2026_8841",
  "source_mode": "SIMULATED",
  "evidence_count": 3,
  "evidence_items": [
    {
      "evidence_id": "ev_01",
      "source_url": "https://service.gst.gov.in/services/searchtp",
      "source_name": "GST Portal Directory",
      "claim_supported": "Legal Name & Registration",
      "facts": {
        "legal_name": "Apex Global Logistics Pvt Ltd",
        "trade_name": "Apex Courier",
        "status": "Active"
      },
      "retrieved_at": "2026-10-24T07:46:10Z"
    }
  ]
}
```

---

### 5. `POST /api/cases/{case_id}/assess`
Execute the deterministic rule engine over invoice claims vs discovered evidence.

**Response (`200 OK`):**
```json
{
  "case_id": "case_inv_2026_8841",
  "recommendation": "REVIEW",
  "risk_score": 68,
  "reason_codes": [
    "LEGAL_NAME_MISMATCH",
    "BANK_OWNERSHIP_UNVERIFIED"
  ],
  "hard_gates_triggered": [],
  "evidence_completeness": "PARTIAL",
  "human_signoff_required": true
}
```

---

### 6. `POST /api/cases/{case_id}/review`
Record authorized reviewer decision with mandatory rationale.

**Request:**
```json
{
  "reviewer_id": "analyst_prachi",
  "action": "APPROVE_WITH_EXCEPTION",
  "rationale": "Trade name matches public registered alias. Cancelled cheque verified offline.",
  "requested_documents": []
}
```

---

### 7. `GET /api/cases/{case_id}/report`
Export cryptographically hashed audit report (JSON or Markdown).
