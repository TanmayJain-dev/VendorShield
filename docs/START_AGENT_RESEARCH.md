# Quick-Start AI Agent Prompt Template

> **Purpose:** Any team member can copy the prompt template below directly into their AI coding/research assistant (e.g., Gemini, Claude, ChatGPT, Cursor, GitHub Copilot Workspace, Antigravity) along with their name to immediately activate role-specific deep research and mentor preparation.

---

## 📋 The Copy-Paste Prompt Template

Copy the block below into your AI agent:

```markdown
You are an expert AI research and coding partner working directly on the VendorShield AI project.

Repository URL: https://github.com/TanmayJain-dev/VendorShield.git
My Name: [INSERT YOUR NAME HERE: Tanmay Jain / Prachi Bhalla / Garv Goyal]

Your instructions:
1. Inspect the official role assignments in `docs/TEAM_ROLES.md` and identify my exact assigned role.
2. Read the master project guide in `docs/PROJECT_GUIDE.md` to understand the problem statement, architecture, data flow, implemented features, and technical terminology.
3. Read my personalized agent guide:
   - If I am Tanmay Jain: read `docs/agents/TANMAY_AGENT_GUIDE.md`
   - If I am Prachi Bhalla: read `docs/agents/PRACHI_AGENT_GUIDE.md`
   - If I am Garv Goyal: read `docs/agents/GARV_AGENT_GUIDE.md`
4. Inspect the actual repository files, code, configuration, tests, and documentation using your file reading tools. Do NOT make assumptions without inspecting the codebase.
5. Clearly distinguish verified code facts, technical hypotheses, recommendations, and planned/unimplemented features.
6. Conduct role-specific research aligned with my responsibilities and produce a comprehensive, structured briefing containing:
   a. A simple, jargon-free explanation of VendorShield AI and the core problem it solves.
   b. A verified architecture and feature summary based on the actual codebase.
   c. Role-specific research findings, market/threat context, and domain insights.
   d. Identified weaknesses, bottlenecks, and prioritized recommendations with trade-offs.
   e. At least 15 potential mentor/judge questions tailored to my role with concise, defensible answers.
   f. A 2-minute elevator pitch and speaking script tailored to my assigned role.
   g. File paths, class names, function names, and external sources supporting every major claim.

Begin your work now by inspecting the repository.
```

---

## 🚀 How Team Members Use This

| Team Member | Official Role | Guide to Load | What the Agent Delivers |
| :--- | :--- | :--- | :--- |
| **Tanmay Jain** | Team Lead + Tech Lead | [`docs/agents/TANMAY_AGENT_GUIDE.md`](agents/TANMAY_AGENT_GUIDE.md) | Full-stack architectural breakdown, scaling bottlenecks, database design, API resilience, and technical mentor defense. |
| **Prachi Bhalla** | Problem Research + Product Strategy + User Experience | [`docs/agents/PRACHI_AGENT_GUIDE.md`](agents/PRACHI_AGENT_GUIDE.md) | Real-world AP fraud validation, target persona workflows, competitive differentiation, UX audit, and product pitch scripts. |
| **Garv Goyal** | Risk Research + Validation + Impact | [`docs/agents/GARV_AGENT_GUIDE.md`](agents/GARV_AGENT_GUIDE.md) | Fraud threat modeling, risk rule audit, test coverage review, responsible AI compliance, and risk defense Q&A. |

---

## 🔍 What the Agent Must Deliver

When executing the prompt, the agent must output these 7 standard sections:

1. **Simple Project Explanation:** What VendorShield AI does in 3 plain-English paragraphs accessible to any non-technical audience.
2. **Verified Architecture & Features:** What features actually exist in the code (verified via `backend/app/`, `frontend/src/`, and passing tests) versus what is simulated or planned.
3. **Role-Specific Research Findings:** Deep dive into the member's assigned domain (engineering, product, or risk).
4. **Identified Weaknesses & Prioritized Recommendations:** Concrete areas for improvement with realistic implementation trade-offs.
5. **15+ Mentoring Round Questions & Answers:** The toughest questions judges will ask about this role, with crisp, grounded answers.
6. **Role-Specific Speaking Script:** A natural, professional 2-minute talking script for the member's presentation portion.
7. **Evidence & Citation Index:** Table of real file paths, line numbers, function names, and statutory/regulatory references.
