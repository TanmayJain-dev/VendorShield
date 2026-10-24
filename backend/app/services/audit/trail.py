import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from ...schemas.case import Case

class AuditTrailService:
    """
    Cryptographic snapshot verification and audit report generation service.
    
    Integrity Architecture:
    1. Computes a deterministic SHA-256 digest over the canonical sorted JSON
       representation of the case snapshot (excluding the digest field itself).
    2. Serves as a point-in-time tamper-evident snapshot integrity check to verify
       that records match their state when finalized.
    3. Storage Scope: In this local deployment, audit events and digests are persisted
       in the local SQLite/PostgreSQL database. It is not an immutable distributed ledger.
    4. Clearly delineates authoritative live registry evidence from simulated demo fixtures.
    """
    def compute_case_hash(self, case: Case) -> str:
        """
        Computes SHA-256 over canonical sorted JSON representation of the case payload.
        Avoids circular hashing by computing only over content fields.
        """
        payload = {
            "case_id": case.case_id,
            "case_reference": case.case_reference,
            "status": case.status.value,
            "source_mode": case.source_mode.value,
            "file_sha256": case.file_sha256,
            "invoice": case.invoice.model_dump() if case.invoice else None,
            "evidence": [e.model_dump() for e in case.evidence_items],
            "assessment": case.assessment.model_dump() if case.assessment else None,
            "review": case.review.model_dump() if case.review else None,
            "ruleset_version": case.assessment.ruleset_version if case.assessment else "1.0.0"
        }
        canonical_json = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def generate_markdown_report(self, case: Case, audit_events: Optional[List[dict]] = None) -> str:
        """Generates a human-readable audit report in Markdown."""
        inv = case.invoice
        assess = case.assessment
        rev = case.review

        md = []
        md.append(f"# VendorShield Due-Diligence Audit Report")
        md.append(f"**Case Reference:** `{case.case_reference}` | **Case ID:** `{case.case_id}`")
        md.append(f"**Generated At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        md.append(f"**Snapshot SHA-256 Digest:** `{case.audit_hash_sha256 or 'PENDING_FINALIZATION'}`")
        md.append(f"**Evidence Provenance Mode:** `{case.source_mode.value}`")
        if case.duplicate_type:
            md.append(f"**Duplicate Status:** `{case.duplicate_type}` (Ref: `{case.duplicate_of_case_id or 'Previous intake'}`)\n")
        else:
            md.append("")
        
        md.append("## 1. Invoice Claims & Extraction Status")
        if inv:
            md.append(f"- **Supplier Trade Name:** {inv.supplier_name}")
            if inv.legal_name:
                md.append(f"- **Legal Entity Name:** {inv.legal_name}")
            md.append(f"- **Invoice Number:** {inv.invoice_number}")
            md.append(f"- **Invoice Date:** {inv.invoice_date or 'Not specified'}")
            md.append(f"- **Total Amount:** ₹{inv.total_amount:,.2f}")
            md.append(f"- **Taxable Amount:** ₹{inv.taxable_amount:,.2f}")
            md.append(f"- **Tax Breakdown:** CGST ₹{inv.cgst:,.2f} | SGST ₹{inv.sgst:,.2f} | IGST ₹{inv.igst:,.2f}")
            md.append(f"- **GSTIN:** `{inv.gstin or 'NOT PROVIDED'}` (Format / Checksum: {'VALID' if inv.gstin_format_valid else 'INVALID/UNKNOWN'})")
            md.append(f"- **Bank / IFSC:** A/C {inv.bank_account_masked or 'N/A'} | IFSC `{inv.ifsc_code or 'N/A'}`")
            md.append(f"- **Arithmetic Reconciled:** {'YES' if inv.arithmetic_valid else 'NO'}")
            if inv.arithmetic_notes:
                md.append(f"  *Notes:* {inv.arithmetic_notes}")
            if inv.parsing_warnings:
                md.append(f"- **Extraction Warnings:** {', '.join(inv.parsing_warnings)}")
            if inv.is_scanned_image:
                md.append(f"- **Scanned Image Document:** YES (OCR: {inv.ocr_status_message or 'Pending'})")
            md.append("")

        md.append("## 2. Risk Assessment & Deterministic Policy Decision")
        if assess:
            md.append(f"- **Recommendation:** **`{assess.recommendation.value}`**")
            md.append(f"- **Deterministic Policy Risk Index:** {assess.risk_score}/100 (Uncalibrated Heuristic Indicator)")
            md.append(f"- **Index Explanation:** {assess.score_explanation}")
            md.append(f"- **Ruleset Version:** `{assess.ruleset_version}`")
            md.append(f"- **Triggered Reason Codes:** `{', '.join(assess.reason_codes) or 'NONE'}`")
            md.append(f"- **Hard Safety Gates:** `{', '.join(assess.hard_gates_triggered) or 'NONE'}`")
            md.append(f"- **Evidence Completeness:** `{assess.evidence_completeness}`")
            if assess.missing_evidence_items:
                md.append(f"- **Missing / Unverified Evidence:** {', '.join(assess.missing_evidence_items)}")

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
                md.append("\n### 2.2 Estimated Potential Financial Exposure (CGST Sec 16(2)(c) & Sec 74 Decision-Support Projection)")
                md.append(f"- **Claimed GST Component:** ₹{itc.tax_amount_claimed:,.2f}")
                md.append(f"- **Illustrative Statutory Penalty (Sec 74):** ₹{itc.statutory_penalty_inr:,.2f}")
                md.append(f"- **Estimated Delayed Tax Interest (Sec 50 @ 18% p.a.):** ₹{itc.estimated_interest_inr:,.2f}")
                md.append(f"- **Estimated Potential Exposure:** **₹{itc.total_financial_liability_inr:,.2f}** (illustrative clawback + penalty & interest)")
                md.append(f"- **Risk Classification:** `{itc.risk_tier}`")
                md.append(f"- **CFO Operational Advisory:** *\"{itc.cfo_advisory}\"*")

            if assess.entity_graph:
                eg = assess.entity_graph
                md.append(f"\n### 2.3 Forensic Knowledge Graph Summary")
                md.append(f"- **Total Nodes:** {eg.total_nodes} (Vendor, Directors, Addresses, Litigation)")
                md.append(f"- **Flagged Contagion Edges:** {eg.total_flagged_edges}\n")
            
            if assess.triggered_rules:
                md.append("\n### Triggered Rules Detail")
                for r in assess.triggered_rules:
                    gate_badge = "[HARD GATE]" if r.is_hard_gate else ""
                    md.append(f"- **{r.rule_name}** ({r.severity}, -{r.weight} pts) {gate_badge}: {r.description}")
            md.append("")

        md.append("## 3. Discovered Evidence Provenance Trail")
        for ev in case.evidence_items:
            fallback_label = " [DEMO FIXTURE]" if ev.is_fallback else f" [{ev.source_mode.value}]"
            md.append(f"### Source: [{ev.source_name}]({ev.source_url}){fallback_label}")
            md.append(f"- **Claim Supported:** {ev.claim_supported}")
            md.append(f"- **Source Type:** `{ev.source_type}` | **Authoritative:** {'YES' if ev.is_authoritative else 'NO'}")
            md.append(f"- **Retrieved At:** `{ev.retrieved_at}`")
            if ev.fallback_reason:
                md.append(f"- **Fallback Reason:** *{ev.fallback_reason}*")
            md.append(f"- **Raw Excerpt:** *\"{ev.raw_excerpt}\"*")
            if ev.match_rationale:
                md.append(f"- **Match Rationale:** {ev.match_rationale}")

        if rev:
            md.append("\n## 4. Human Reviewer Sign-Off")
            md.append(f"- **Reviewer ID:** `{rev.reviewer_id}` ({rev.reviewer_role})")
            md.append(f"- **Action Recorded:** **`{rev.action.value}`**")
            md.append(f"- **Authentication Mode:** `{rev.auth_mode}`")
            md.append(f"- **Reviewer Rationale:** {rev.rationale}")
            md.append(f"- **Timestamp:** `{rev.recorded_at}`")

        if audit_events:
            md.append("\n## 5. Tamper-Evident Chained Audit Trail")
            for e in audit_events:
                md.append(f"- `{e.get('timestamp')}` | **{e.get('event_type')}** by `{e.get('actor')}` (`{e.get('actor_role')}`)")
                md.append(f"  *Hash:* `{e.get('event_hash', '')[:16]}...` (Prev: `{e.get('prev_hash', '')[:16]}...`)")

        md.append("\n---\n*VendorShield AI — Evidence-grounded accounts payable due diligence. Axiom: TinyFish researches; VendorShield decides.*")
        return "\n".join(md)
