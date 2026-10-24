# Contributing to VendorShield AI

Welcome to the VendorShield AI repository! This project is maintained by **Team Astra-X** for HackIIITD (Esya '26).

---

## 🔒 Branch & PR Policies
1. **Never commit directly to `main`:** The `main` branch is protected. Direct pushes are rejected by GitHub.
2. **Feature Branches:** Create all work on a branch prefixed by your module:
   - Tanmay (Core Backend / Rules / TinyFish): `feat/core-*`
   - Prachi (Next.js Frontend / UI Dossier): `feat/ui-*`
   - Garv (Document Parsing / GSTIN / Data): `feat/ingestion-*`
   - Bugfixes: `fix/*`
3. **Automated CI:** Every PR triggers the automated CI suite (`backend-test` + `frontend-build`). All checks must pass before merging.
4. **Agent Prompts:** If you are using an AI coding assistant (Antigravity, Cursor, Claude Code, Copilot), refer to your role-specific prompt in `.github/agents/`.

---

## 🧪 Running Tests Locally
```bash
# Backend pytest
cd backend
pytest -v

# Frontend typecheck
cd frontend
pnpm tsc --noEmit
```
