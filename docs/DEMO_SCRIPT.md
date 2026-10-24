# VendorShield AI — Hackathon Mentor Demo Script (5 Minutes)

This script outlines the exact live demonstration sequence for hackathon mentors, illustrating the end-to-end accounts payable vendor verification flow from PDF upload to audit seal.

---

## ⏱️ Live Demo Timeline

```
0:00 - 0:30 | Problem Framing & The "Invoice Trap"
0:30 - 1:30 | Real Invoice Upload & Layered Extraction Review
1:30 - 2:30 | Deterministic Rules, Fail-Closed Policy & Why This Verdict
2:30 - 3:45 | Public Registry Attestation & Automatic Re-assessment
3:45 - 4:30 | Reviewer Sign-Off & Cryptographic SHA-256 Hash Chain
4:30 - 5:00 | 60-Second Fallback & Mentorship Q&A
```

---

## 🎬 Step-by-Step Walkthrough

### 1. Problem Framing (0:00 - 0:30)
- **Speaker:** *"In Indian B2B commerce, Accounts Payable teams face a statutory trap under CGST Section 16(2)(c): if your vendor fails to pay tax or has a cancelled GST registration, the buyer is liable for 100% tax clawback, 18% annual interest, and penalties. VendorShield AI verifies vendor claims before payment release."*
- Navigate to the landing page at `http://localhost:3000`. Point out the restrained trust posture: **no fake 99.9% claims**, deterministic fail-closed architecture, and human sign-off.

### 2. Real Invoice Upload & Extraction Review (0:30 - 1:30)
- Navigate to **Intake Invoice** (`/upload`).
- Drag and drop a real vendor invoice PDF (e.g. `data/sample_invoices/01_clean_intra_state.pdf`).
- Point out that:
  - Form defaults are completely unpopulated (no hardcoded "Apex Courier" values).
  - Multi-file batch intake is supported.
- Click **"Upload & Ingest Invoice"**.
- Land on the **Side-by-Side Extraction Review** view on `/cases/[id]`:
  - **Left Pane:** Displays the rendered original PDF document.
  - **Right Pane:** Displays structured extracted claims with explicit **Provenance Chips** (`QR Code`, `Text Layer`, `LLM Extracted`) and Confidence percentages.
  - Highlight that inferred values are never silently disguised as verified facts.

### 3. Fail-Closed Verification & Explain Verdict (1:30 - 2:30)
- Click **"Confirm & Run Checks"**.
- Switch to the **Evidence Dossier** view:
  - Show that the recommendation is **`MANUAL_REVIEW`** with score ~65/100.
  - **Key Talking Point:** *"Notice that we do not fabricate a 'PASS'. Because no live GST registry API key is configured, our engine fails closed to MANUAL_REVIEW. Missing evidence is never treated as proof of safety."*
  - Expand the **"Why This Verdict"** and **"What Would Change It"** explanations.
  - Point out that **`UNAVAILABLE`** registry checks are rendered in **neutral grey**, not alarming red.

### 4. Public Registry Attestation & Dynamic Re-Assessment (2:30 - 3:45)
- Under Section 1 (Extracted Invoice Claims), click **"Add GST Registry Details"**.
- Click **"Copy GSTIN"** and show the direct link to the official government portal: `https://services.gst.gov.in/services/searchtp`.
- In the attestation modal, fill in the verified registration facts:
  - **Legal Name:** `Apex Global Logistics Pvt Ltd`
  - **Trade Name:** `Apex Global Logistics`
  - **Status:** `Active`
  - **Reg Date:** `2021-04-01`
- Click **"Record Evidence & Re-assess"**.
- **The Wow Moment:** The dossier immediately re-evaluates in real-time. The active status is reconciled, trade-name similarity is verified, and the recommendation flips to **`PASS`**!

### 5. Reviewer Sign-Off & Cryptographic Audit Seal (3:45 - 4:30)
- Scroll down to Section 4: **Human Reviewer Decision & Audit Seal**.
- Note the role pill in the navigation header: authenticated as `Reviewer (Garv Goyal)`.
- Select Action: **`APPROVE`** (Clean Pass).
- Enter mandatory audit rationale: *"Verified active GSTIN on public portal. Legal entity and bank branch match invoice claims."*
- Click **"Record Decision & Seal Case"**.
- Click **"Verify Audit Chain"**:
  - Show the green verification banner: `✓ SHA-256 Hash Chain Verified Intact (4 events checked)`.
  - Explain that each audit event stores the cryptographic hash of the prior event, preventing silent tampering in the database.

---

## ⚡ 60-Second Fallback Demo (If Internet/Files Unavailable)
1. Go to `/upload` and expand the collapsed **"Demo Scenarios (Synthetic Benchmark Fixtures)"** drawer.
2. Click **Apex Courier Benchmark** or **Specter Cloud Ghost Vendor**.
3. Note the prominent **`DEMO DATA`** amber badge across the queue and dossier.
4. Show that Specter Cloud immediately hits a **Critical BLOCK** (ghost vendor, zero registry footprint).
