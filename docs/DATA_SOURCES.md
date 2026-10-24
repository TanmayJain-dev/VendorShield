# VendorShield AI — Data Sources & Evidence Registry

This document catalogues every external data source, extraction mechanism, public registry, and verification channel utilized by **VendorShield AI**, detailing acquisition method, cost, reliability, statutory limits, and fail-closed behaviors.

---

## 📊 Summary of Data Sources

| Data Source | Type | Acquisition Method | Cost | Reliability | Failure Mode & Fallback |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B2B e-Invoice QR Code** | Cryptographic Document | PyMuPDF / OpenCV JWT decoding | Free | 100% when QR is present | Falls back to text / LLM extraction layer |
| **PDF Text Layer** | Document Text | PyMuPDF line extraction + regex | Free | High on native digital PDFs | Flags scanned document; routes to OCR/LLM |
| **LLM Multimodal Extractor** | AI Document Parser | Gemini 1.5 / Claude via REST API | Free / Low API fee | High across varied invoice formats | Falls back to text layer when `LLM_PROVIDER=none` |
| **GST Search Taxpayer Portal** | Public Web Registry | Reviewer manual attestation / TinyFish browser agent | Free | Authoritative government source | Fails closed to `UNAVAILABLE` (`MANUAL_REVIEW`) |
| **GSTR-2B B2B Return** | Government Return | User-uploaded GST Portal JSON export | Free | Authoritative statutory filing | Flags `ITC_NOT_IN_GSTR2B` (payment hold advice) |
| **Razorpay IFSC Directory** | Open Financial Dataset | `https://ifsc.razorpay.com/<IFSC>` + SQLite cache | Free | 99.9% uptime (cached 30 days) | Fails closed to `IFSC_UNVERIFIED` |
| **Commercial GSP / KYC API** | B2B REST Endpoint | Configurable HTTP API via `HttpKycProvider` | Paid (per call) | High | Sequences to next configured provider |
| **Synthetic Fixtures** | Offline Mock Data | In-memory demo fixtures | Free | Isolated to `is_demo=True` | Never used for real production cases |

---

## 🔍 Detailed Data Source Specifications

### 1. B2B e-Invoice QR Code (IRP Payload)
- **Source:** Mandatory B2B e-invoices issued under Rule 48(4) of the CGST Rules (invoices above ₹5 Cr aggregate turnover).
- **Extraction Mechanism:** PyMuPDF renders PDF at 200 DPI into a pixmap; OpenCV (`cv2.QRCodeDetector`) decodes the QR symbol. Payload is a base64-encoded JWT issued by the Invoice Registration Portal (IRP).
- **Extracted Fields:** `SellerGstin`, `BuyerGstin`, `DocNo`, `DocDt`, `TotInvVal`, `ItemCnt`, `MainHsnCode`, `Irn`.
- **Cryptographic Trust:**
  - Signature status labeled `UNVERIFIED` when no government public key PEM is provided.
  - If `IRP_PUBLIC_KEY_PEM` is configured, verifies RSA-256 digital signature against official NIC public key.
  - **Hard Gate:** If a verified QR code payload contradicts the printed total or invoice number, triggers `EINVOICE_QR_MISMATCH` (**Critical BLOCK**).

### 2. Public GST Search Taxpayer Portal
- **Source:** Official GST Portal (`https://services.gst.gov.in/services/searchtp`).
- **Acquisition Mechanism:**
  - **Manual Entry:** Direct reviewer attestation with 1-click clipboard copy of the GSTIN and portal link.
  - **TinyFish Browser Agent:** Automated headless browser automation querying the public search page when `TINYFISH_API_KEY` is configured.
- **Retrieved Facts:** Legal Name of Business, Trade Name, Registration Status (`Active`, `Cancelled`, `Suspended`), Registration Date, Taxpayer Type (`Regular`, `Composition`).
- **Fail-Closed Semantics:** If the portal is down, CAPTCHA fails, or API key is absent, status is tagged `SourceMode.UNAVAILABLE`. The case **fails closed to `MANUAL_REVIEW`**; missing evidence is never treated as proof of active status or proof of fraud.

### 3. GSTR-2B Reconciliation
- **Source:** Auto-drafted Input Tax Credit (ITC) statement generated on the 14th of every month on the GST Portal, listing invoices uploaded by suppliers in their GSTR-1 filings.
- **Acquisition Mechanism:** Recipient accounts payable team downloads the GSTR-2B JSON file from the GST Portal and uploads it via `POST /api/gstr2b/import`.
- **Reconciliation Logic:**
  - Matches invoices on normalized `(supplier_gstin, invoice_number)`.
  - Compares gross invoice total with reported GSTR-2B value.
  - Checks statutory `itc_available` flag (`Y` / `N`).
- **Rule Outcomes:**
  - `ITC_NOT_IN_GSTR2B`: Invoice not in GSTR-2B return → **MEDIUM Severity** (payment hold advised until supplier files).
  - `GSTR2B_VALUE_MISMATCH`: Gross amount differs by more than ₹2.00 → **HIGH Severity**.
  - `GSTR2B_ITC_NOT_AVAILABLE`: Supplier flagged ITC ineligible → **MEDIUM Severity**.

### 4. Razorpay IFSC API & Cache
- **Source:** Open IFSC routing dataset maintained at `https://ifsc.razorpay.com/`.
- **Acquisition Mechanism:** Asynchronous HTTP GET query with 5.0s timeout. Responses are cached in the SQLite `ifsc_cache` table with a 30-day Time-To-Live (TTL).
- **Statutory Limitation:**
  - Validates bank name, branch, city, and state code.
  - **Never claims account ownership:** Account ownership cannot be confirmed via IFSC alone. Rules engine always preserves `BANK_OWNERSHIP_UNVERIFIED` (Low severity advisory) and advises penny-drop or cancelled cheque verification.

### 5. Configurable HTTP KYC Provider (`HttpKycProvider`)
- **Source:** Paid GSP / corporate identity vendors (e.g. Karza, Signzy, Cashfree, Perfios).
- **Configuration:** Set via `GSTIN_API_URL_TEMPLATE`, `GSTIN_API_AUTH_HEADER`, and `GSTIN_API_FIELD_MAP` in environment variables.
- **Sequencing:** Sequenced via `GSTIN_PROVIDERS=http_kyc,manual`. If the paid API is unavailable, the pipeline falls closed to manual reviewer entry without application crash.
