import hashlib
import json
from typing import Dict, Any
from datetime import datetime
from ...schemas.case import Case

class AuditTrailService:
    """
    Cryptographic audit hashing and report generation.
    Generates deterministic SHA-256 digests over case snapshots for tamper detection.
    """
    def compute_case_hash(self, case: Case) -> str:
        """
        Computes SHA-256 over canonical sorted JSON representation of the case payload.
        """
        payload = {
            "case_id": case.case_id,
            "invoice": case.invoice.model_dump() if case.invoice else None,
            "evidence": [e.model_dump() for e in case.evidence_items],
            "assessment": case.assessment.model_dump() if case.assessment else None,
            "review": case.review.model_dump() if case.review else None,
            "ruleset_version": case.assessment.ruleset_version if case.assessment else "1.0.0"
        }
        canonical_json = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def generate_markdown_report(self, case: Case) -> str:
        """Generates a human-readable audit report in Markdown."""
        inv = case.invoice
        assess = case.assessment
        rev = case.review

        md = []
        md.append(f"# VendorShield Due-Diligence Audit Report")
        md.append(f"**Case Reference:** `{case.case_reference}` | **Case ID:** `{case.case_id}`")
        md.append(f"**Generated At:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        md.append(f"**SHA-256 Digest:** `{case.audit_hash_sha256 or 'PENDING_FINALIZATION'}`\n")
        
        md.append("## 1. Invoice Claims")
        if inv:
            md.append(f"- **Supplier Trade Name:** {inv.supplier_name}")
            md.append(f"- **Invoice Number:** {inv.invoice_number}")
            md.append(f"- **Total Amount:** ₹{inv.total_amount:,.2f}")
            md.append(f"- **GSTIN:** `{inv.gstin or 'NOT PROVIDED'}` (Format: {'VALID' if inv.gstin_format_valid else 'INVALID/UNKNOWN'})")
            md.append(f"- **Bank / IFSC:** A/C {inv.bank_account_masked or 'N/A'} | IFSC `{inv.ifsc_code or 'N/A'}`")
            md.append(f"- **Arithmetic Reconciled:** {'YES' if inv.arithmetic_valid else 'NO'}\n")

        md.append("## 2. Risk Assessment & Decision")
        if assess:
            md.append(f"- **Outcome:** **`{assess.recommendation.value}`**")
            md.append(f"- **Composite Safety Score:** {assess.risk_score}/100")
            md.append(f"- **Triggered Reason Codes:** `{', '.join(assess.reason_codes) or 'NONE'}`")
            md.append(f"- **Hard Safety Gates:** `{', '.join(assess.hard_gates_triggered) or 'NONE'}`")
            md.append(f"- **Evidence Completeness:** {assess.evidence_completeness}")

            if assess.forensic_vectors:
                fv = assess.forensic_vectors
                md.append("\n### 2.1 The 5-Vector Forensic Topology")
                md.append(f"- **1. ITC Clawback Risk Index:** `{fv.itc_clawback_risk_index:.2f}` / 1.00")
                md.append(f"- **2. Director Shell Contagion Score:** `{fv.director_shell_contagion_score:.2f}` / 1.00")
                md.append(f"- **3. Address Collocation Density:** `{fv.address_collocation_density}` distinct entities at same address")
                md.append(f"- **4. Operational Grounding Index:** `{fv.operational_grounding_score:.2f}` / 1.00")
                md.append(f"- **5. Pop-Up Velocity Factor:** `{fv.popup_velocity_factor:.2f}` / 1.00")

            if assess.itc_exposure:
                itc = assess.itc_exposure
                md.append("\n### 2.2 Direct Rupee Financial Exposure (CGST Sec 16(2)(c) & Sec 74)")
                md.append(f"- **Claimed GST Component:** ₹{itc.tax_amount_claimed:,.2f}")
                md.append(f"- **Statutory 100% Penalty:** ₹{itc.statutory_penalty_inr:,.2f}")
                md.append(f"- **Estimated 18% p.a. Interest:** ₹{itc.estimated_interest_inr:,.2f}")
                md.append(f"- **Total Financial Liability:** **₹{itc.total_financial_liability_inr:,.2f}**")
                md.append(f"- **Risk Classification:** `{itc.risk_tier}`")
                md.append(f"- **CFO Advisory:** *\"{itc.cfo_advisory}\"*")

            if assess.entity_graph:
                eg = assess.entity_graph
                md.append(f"\n### 2.3 Forensic Knowledge Graph Summary")
                md.append(f"- **Total Nodes:** {eg.total_nodes} (Vendor, Directors, Addresses, Litigation)")
                md.append(f"- **Flagged Contagion Edges:** {eg.total_flagged_edges}\n")


        md.append("## 3. Evidence Provenance Trail")
        for ev in case.evidence_items:
            md.append(f"### Source: [{ev.source_name}]({ev.source_url})")
            md.append(f"- **Claim Supported:** {ev.claim_supported}")
            md.append(f"- **Retrieved At:** `{ev.retrieved_at}`")
            md.append(f"- **Raw Excerpt:** *\"{ev.raw_excerpt}\"*")

        if rev:
            md.append("\n## 4. Human Reviewer Sign-Off")
            md.append(f"- **Reviewer ID:** `{rev.reviewer_id}`")
            md.append(f"- **Action Recorded:** **`{rev.action.value}`**")
            md.append(f"- **Reviewer Rationale:** {rev.rationale}")
            md.append(f"- **Timestamp:** `{rev.recorded_at}`")

        md.append("\n---\n*VendorShield AI — Built for HackIIITD (Esya '26). Axiom: TinyFish researches; VendorShield decides.*")
        return "\n".join(md)
