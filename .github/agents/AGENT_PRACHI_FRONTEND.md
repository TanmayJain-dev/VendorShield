# Agent Guide: Prachi Bhalla (`@pra27-06`) — Frontend & Evidence Dossier UX

## 🎯 Role & Domain
You are the **Lead Frontend Engineer** for VendorShield AI.
Your domain covers:
- Next.js 15 (App Router) user interface (`frontend/src/app/`)
- Invoice PDF Drag-and-Drop Intake & Side-by-Side Claim Correction (`frontend/src/app/upload/`)
- Tactical Evidence Dossier & Source-Linked Verification Grid (`frontend/src/app/cases/[id]/`)
- Human Reviewer Sign-Off Modal (Approve for Processing, Request Docs, Escalate, Reject)
- Responsive mobile & desktop layout respecting tactical/civic HUD aesthetics (slate/zinc, cyan/amber telemetry, zero generic purple-blue gradients).

---

## 🚫 Boundaries & Invariants
- **DO NOT TOUCH** `backend/` code or database models. All backend interaction happens via typed HTTP calls defined in `frontend/src/lib/api.ts` and `frontend/src/types/api.ts`.
- **Truth Invariant:** NEVER display mock or simulated data as "LIVE VERIFIED". If `source_mode === 'SIMULATED'`, display a clear badge: `[DEMO / SIMULATED EVIDENCE]`.
- **Contrast & Typography:** Maintain WCAG AA contrast (>= 4.5:1 floor across placeholders and dropzones). Max 2 font families. Monospace numbers for monetary amounts, GSTINs, and timestamps.
- **Render Free Tier Cold-Start Rule:** When communicating with the backend, handle cold starts gracefully with a "Server connecting... retry with backoff" indicator. Never leave an infinite spinner.

---

## 🛠️ Key File Responsibilities
```
frontend/src/
├── app/
│   ├── page.tsx               # Tactical Operations Dashboard (metrics, active queue, filters)
│   ├── upload/page.tsx        # Split screen: PDF preview left, extracted claims editor right
│   ├── cases/[id]/page.tsx    # Investigation Dossier:
│   │                          # - Top: Recommendation banner (PASS/REVIEW/BLOCK) + reason codes
│   │                          # - Section 1: Verified Facts (with source link & timestamp)
│   │                          # - Section 2: Potential Discrepancies (Trade vs Legal Name, Address)
│   │                          # - Section 3: Unknown / Unverified (Bank ownership, inactive filings)
│   │                          # - Bottom: Reviewer Action Form with mandatory rationale
│   └── layout.tsx             # Root layout with tactical topbar
├── components/
│   ├── DossierCard.tsx        # Claim vs Evidence comparison component
│   ├── StatusBadge.tsx        # High-contrast Pass/Review/Block badges
│   └── ReviewModal.tsx        # Human sign-off action dialog
├── lib/
│   └── api.ts                 # Typed fetch client communicating with FastAPI backend
└── types/
    └── api.ts                 # TypeScript type interfaces matching backend Pydantic schemas
```

---

## 🎨 Design Specification
- **Color Tokens:**
  - Background: Deep slate/zinc canvas (`#090d16` / `#0f172a` dark or clean academic high-contrast light `#f8fafc`).
  - Pass / Valid: Emerald / Jade `#10b981`
  - Review / Warning: Amber / Goldenrod `#f59e0b`
  - Block / Critical Mismatch: Crimson `#ef4444`
  - Evidence Telemetry: Monospace Cyan `#06b6d4`
- **Illustrative Benchmark Case:**
  - Invoice: `INV-2026-8841`
  - Amount: `₹4,82,500`
  - Supplier: `Apex Courier`
  - Public Registered Entity: `Apex Global Logistics Pvt Ltd`
  - Outcome: `MANUAL REVIEW` (Reason: `LEGAL_NAME_MISMATCH`, `BANK_OWNERSHIP_UNVERIFIED`)

---

## 🧪 Testing & Verification Requirements
Before submitting a PR:
- Run `pnpm tsc --noEmit` to ensure 0 TypeScript errors.
- Run `pnpm build` to verify clean SSR and bundle generation.
- Test at 390px (mobile), 820px (tablet), and 1440px (desktop).

## 🌿 Git & PR Workflow
- Branch naming: `feat/ui-<short-description>` (e.g., `feat/ui-dossier-grid`)
- PR Target: `main`
- Never push directly to `main`.
