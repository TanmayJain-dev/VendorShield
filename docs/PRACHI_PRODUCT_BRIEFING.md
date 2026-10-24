# VendorShield AI — Product Strategy, Problem Research & UX Briefing

> **Prepared For:** Prachi Bhalla  
> **Official Role:** Problem Research + Product Strategy + User Experience  
> **Team:** Astra-X | **Hackathon:** HackIIITD (Esya '26, IIIT Delhi)  
> **Repository:** `https://github.com/TanmayJain-dev/VendorShield.git`  

---

## 1. Executive Summary

**VendorShield AI** is an evidence-first, pre-payment due-diligence platform designed for Accounts Payable (AP) and enterprise finance teams. It bridges a dangerous, multi-billion-dollar blind spot in enterprise procurement: traditional ERPs verify internal purchase orders, but remain blind to external vendor fraud, suspended GST registrations, phantom suppliers, and bank misdirection.

By leveraging **TinyFish browser automation** to collect public registry evidence and processing that evidence through a **deterministic compliance policy engine**, VendorShield categorizes risks into transparent, fail-closed recommendations (`PASS`, `MANUAL_REVIEW`, `BLOCK`) with a cryptographically chained, tamper-evident audit trail.

---

## 2. Real-World Problem Research & Statutory Context

### 2.1 The Accounts Payable Fraud Epidemic
- **ACFE Global Fraud Study Insights:** Organizations lose an estimated **5% of annual revenue** to occupational fraud, with billing schemes and vendor fraud representing the single most frequent and costly category (median duration: 18 months before discovery).
- **The Core Threat Vectors:**
  1. **Ghost / Phantom Vendors:** Invoices created for non-existent companies or using fake/stolen GSTINs, often routed to internal accomplice bank accounts.
  2. **Trade Name vs. Legal Entity Misdirection:** An invoice claims to be from a well-known brand (e.g., "Apex Courier"), but the payment beneficiary belongs to an unrelated shell company.
  3. **Suspended / Cancelled Tax Registrations:** Fraudulent suppliers continue issuing invoices after their GST registration has been revoked.
  4. **Duplicate Billing:** Resubmitting previously paid invoices with altered dates or amounts to exploit manual processing fatigue.

### 2.2 The Indian Enterprise Context: GST ITC Disallowance
In India, vendor compliance is not just an operational issue—it is a direct financial liability under **Section 16(2)(c) of the CGST Act**:
- A buyer can **only claim Input Tax Credit (ITC)** if the supplier has actually remitted the tax collected to the government and holds an **Active** GST registration.
- If an enterprise pays ₹10,00,000 on an invoice with ₹1,80,000 in GST to a vendor whose registration is suspended or cancelled, **tax authorities recover the ₹1,80,000 from the buyer, plus an 18% per annum interest penalty and up to a 100% tax penalty**.
- **The Financial Impact:** Paying a non-compliant or ghost vendor results in an immediate double loss: paying for potentially fake goods/services and losing the statutory tax credit.

---

## 3. Market Sizing & Quantified Business ROI

### 3.1 Target Customer Profile (ICP)
- **Primary ICP:** Mid-market enterprises (₹100 Cr – ₹2,500 Cr revenue) processing **200 to 2,000 invoices monthly**.
- **Why Mid-Market?** Large enterprises have 50-person internal forensic audit teams; small businesses have single-owner oversight. Mid-market enterprises have decentralized procurement, high transaction volume, and small AP teams (3–6 analysts), making them the prime targets for billing schemes.

### 3.2 Concrete Financial ROI Model (Example: 500 Invoices/Month Enterprise)
| Cost Driver / Risk Category | Without VendorShield | With VendorShield AI | Annual Net Benefit |
| :--- | :--- | :--- | :--- |
| **Disallowed GST ITC Losses** | ~₹18,00,000/year (1–2 non-compliant suppliers) | **₹0** (Blocked pre-payment) | **₹18,00,000 saved** |
| **Phantom / Duplicate Invoices** | ~₹12,00,000/year (detected post-audit) | **₹0** (Hard-gated on intake) | **₹12,00,000 saved** |
| **Manual Analyst Research Time** | 35 mins/vendor $\times$ 500 = **291 hrs/mo** | 2 mins/vendor $\times$ 500 = **16.6 hrs/mo** | **94% efficiency gain** (~₹9.5L in labor cost reallocated) |
| **Total Measurable Annual ROI** | — | — | **~₹39.5 Lakhs saved annually** |

---

## 4. Competitive Differentiation Matrix

| Dimension | Traditional ERPs (SAP, Oracle, Tally) | P2P Suites (Coupa, Tipalti) | Generic AI Wrappers ("Ask LLM") | **VendorShield AI** |
| :--- | :--- | :--- | :--- | :--- |
| **Core Verification Method** | Internal 3-Way Match (PO vs. Receipt vs. Invoice) | Static vendor onboarding questionnaire forms | Probabilistic LLM text prompt ("Is this fraud?") | **Live statutory registry corroboration + Deterministic rules** |
| **Statutory GST Compliance** | Blind to real-time portal status; requires batch exports | Limited to pre-cleared portal vendors | Hallucinates registration numbers; no checksum math | **Live TinyFish search + Modulo 36 checksum verification** |
| **Trade Alias Handling** | Fails silently or rejects matching names without explanation | Requires manual vendor master update | Guesses similarity probabilistically | **Normalizes business suffixes; flags aliases for human sign-off** |
| **Auditability & Explainability**| Database row updates; no external evidence snapshots | Proprietary internal event logs | Black-box output; cannot be defended before auditors | **Tamper-evident SHA-256 hash chain + Downloadable Markdown dossier** |
| **Decision Philosophy** | Open by default if PO matches | Workflow approval chains | Suggestive advice without bounds | **Fail-Closed policy; human in the loop required** |

---

## 5. User Journey & UX Design Teardown

VendorShield's user experience (`frontend/src/app/`) is architected to eliminate **alert fatigue** and provide **instant cognitive clarity** for accounts payable staff:

```
[1. Queue Dashboard]          [2. Frictionless Intake]        [3. Evidence Dossier]         [4. Review & Seal]
(/)                           (/upload)                      (/cases/[id])                  (/cases/[id]#review)
• 4 KPI telemetry cards       • Drag-and-drop dropzone       • Clear Recommendation banner  • Legal state actions
• Auto-sorted by submission   • Fast benchmark presets       • Field-by-field check badges  • Mandatory audit rationale
• High-contrast risk badges   • Immediate format validation  • Interactive Claim Correction • Cryptographic SHA-256 seal
```

### UX Design Invariants & Why They Matter:
1. **Decision Triage Banner (`/cases/[id]`):**  
   AP clerks do not have time to read 20 pages of logs. The top banner immediately displays the decision state in high-contrast color tokens:
   - 🟢 `PASS`: All statutory checks match active public records.
   - 🟡 `MANUAL_REVIEW`: Discrepancies, trade alias mismatches, or missing data require documented sign-off.
   - 🔴 `BLOCK`: Critical safety gate triggered (suspended GSTIN, entity conflict, duplicate invoice).
2. **Interactive Claim Correction Workflow (`showEditModal`):**  
   If an invoice is scanned or OCR misreads a character, analysts don't have to delete the case and start over. Clicking **"Correct Claims"** lets them update fields, which immediately triggers an automatic re-assessment and records the correction in the chained audit trail.
3. **Evidence Dossier with Provenance Badges:**  
   Every single material claim links to its live public source URL with verbatim excerpts. Reviewers never have to take the software's word for granted; they can inspect the exact evidence backing every finding.

---

## 6. Mentor Evaluation Defense Playbook (15 Q&As for Prachi)

### Problem & Market Strategy
1. **Q: Why can't companies just use SAP or Tally to stop this?**  
   *Answer:* SAP and Tally only verify internal records (matching the invoice against a purchase order created inside the company). If an employee or supplier creates a fake PO or alters the vendor's bank account, the ERP pays it. VendorShield validates external ground truth against statutory registries before money leaves the bank.
2. **Q: Who is your buyer persona versus your user persona?**  
   *Answer:* The **buyer** is the CFO or VP of Finance, whose primary concern is audit risk, working capital protection, and preventing disallowed tax credits. The **user** is the AP Analyst and AP Manager, who need fast, zero-fatigue due diligence without 30 minutes of manual web searches per vendor.
3. **Q: What is your pricing model?**  
   *Answer:* A tiered B2B SaaS model based on monthly invoice volume: Starter (up to 250 invoices/mo), Growth (1,500 invoices/mo), and Enterprise (unlimited invoices with custom ERP webhook integration and dedicated compliance audit logs).
4. **Q: How does this fit into an existing AP workflow?**  
   *Answer:* VendorShield acts as an automated due-diligence gate before payment execution. Invoices flow in via upload or API; clean invoices (`PASS`) proceed directly to payment scheduling, while exceptions (`MANUAL_REVIEW`, `BLOCK`) trigger analyst review.

### Product Differentiation & AI
5. **Q: Why did you choose TinyFish over a standard Google search scraper?**  
   *Answer:* Traditional scrapers break on JavaScript-heavy government portals and bot protections. TinyFish provides an agentic browser runtime capable of navigating dynamic portals (like `service.gst.gov.in`) and extracting structured facts from complex enterprise directories.
6. **Q: How do you differentiate from generic AI wrappers?**  
   *Answer:* Generic wrappers ask an LLM to guess if an invoice is fake, which is legally indefensible in a tax audit. VendorShield uses TinyFish solely for evidence collection, and then applies deterministic, explainable rule logic that provides a reproducible audit trail.
7. **Q: How do you prevent alert fatigue for AP teams?**  
   *Answer:* We prioritize issues by severity: minor unverified items (like branch lookups) are tagged as low-severity notes, while hard safety gates (inactive tax registration, conflicting entity names) trigger clear blocking warnings with specific reason codes.
8. **Q: What happens if an invoice is in an unsupported format or handwriting?**  
   *Answer:* The system detects image/scanned documents, flags them with a visual alert, and opens the manual correction panel so the analyst can verify claims without system crashes.

### Regulatory & Security Compliance
9. **Q: Why does your system not automatically authorize payments?**  
   *Answer:* Internal controls (such as SOX Section 404 and COSO guidelines) mandate dual-authorization and human oversight for corporate disbursements. Automated payment release creates extreme financial liability.
10. **Q: How does your product handle bank account ownership privacy?**  
    *Answer:* Indian public directories only verify bank branch codes (IFSC), not beneficiary names. We refuse to fake verification: we explicitly tag account ownership as unverified and instruct analysts to confirm with a cancelled cheque or penny-drop.
11. **Q: What prevents a rogue reviewer from approving a fraudulent invoice?**  
    *Answer:* Every action requires a mandatory rationale of at least 5 characters and is cryptographically chained into an append-only audit trail containing the reviewer's ID, timestamp, and SHA-256 hash. Any retroactive alteration breaks the hash chain.
12. **Q: What is the significance of Section 16(2)(c) of the GST Act to your product?**  
    *Answer:* It legally binds buyers to their suppliers' compliance. If a supplier fails to remit tax, the government demands the credit back from the buyer with interest. VendorShield turns this legal hazard into a compelling enterprise sales trigger.

### Go-To-Market & Traction
13. **Q: What is your primary Go-To-Market (GTM) motion?**  
    *Answer:* Product-led adoption targeting mid-market finance teams through a free web tier that audits 25 invoices/month. Once teams experience the time savings and uncover tax credit discrepancies, they upgrade to connect their ERPs.
14. **Q: How do you measure Customer Lifetime Value (LTV) and Net Retention?**  
    *Answer:* Net retention is driven by invoice volume growth: as companies scale their supplier network, their tier automatically expands. LTV is anchored by the high cost of replacement once audit logs are embedded into compliance workflows.
15. **Q: What are the next 3 features on the product roadmap?**  
    *Answer:* (1) Automated penny-drop banking verification API integration, (2) Direct two-way sync with Tally and SAP via secure webhooks, and (3) Automated vendor clarification portal for requesting missing tax documents.

---

## 7. Prachi's 2-Minute Mentoring & Demo Pitch Script

*(Stand tall, speak with confidence, and guide the mentors through the live UI)*

> "Hi mentors, I'm **Prachi Bhalla**, leading Problem Research, Product Strategy, and User Experience for **VendorShield AI**.
>
> In corporate procurement, there is a multi-billion-dollar blind spot. When an enterprise receives an invoice, their ERP checks internal purchase orders—but it has no idea if the vendor's tax registration was revoked last week, if the supplier is a ghost company, or if the bank account belongs to an unauthorized third party. In India, paying a vendor with a cancelled GST registration doesn't just lose you the invoice amount—under Section 16(2)(c) of the GST Act, tax authorities disallow your Input Tax Credit, clawing back the 18% tax with heavy penalties.
>
> That's why we built **VendorShield AI**. We are not an AI wrapper asking an LLM to hallucinate fraud probability. We built an **evidence-first due-diligence platform**.
>
> *(Point to the Dashboard Queue on screen)*  
> When an invoice arrives, our ingestion pipeline extracts statutory claims and deploys **TinyFish browser automation** to research official public registries in real time. Our deterministic rule engine reconciles claims field-by-field, categorizing invoices into **Pass**, **Manual Review**, or **Block**.
>
> *(Navigate into the Case Dossier)*  
> Here in the Evidence Dossier, an analyst doesn't get a vague risk score. They see the exact statutory facts: whether the GSTIN checksum is valid, whether the trade name matches the registered legal entity, and verbatim source excerpts with links back to authoritative registries. If an OCR misread occurs, our interactive **Claim Correction** workflow allows reviewers to adjust claims, immediately recalculating compliance and updating our cryptographically chained audit trail.
>
> We believe in the core principle: *TinyFish researches; VendorShield decides; and authorized humans sign off.* Thank you, and we'd love to take your questions."
