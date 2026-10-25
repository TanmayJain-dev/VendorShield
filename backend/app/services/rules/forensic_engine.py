import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from ...schemas.invoice import InvoiceClaim
from ...schemas.evidence import FieldCheckResult, EvidenceItem
from ...schemas.forensic_graph import (
    ForensicVectorScores,
    ITCExposureDetails,
    DirectorProfile,
    AddressClusterProfile,
    GraphNode,
    GraphEdge,
    EntityGraph,
    TreasurySettlementDetails,
    ProcurementPriceBenchmark,
    JudicialDocketSummary,
    EnforcementRadarSummary
)
from ...schemas.assessment import RiskAssessment, RuleTrigger
from ...schemas.enums import RecommendationOutcome, CheckStatus, SourceMode
from .itc_calculator import ITCExposureCalculator

class ForensicRiskEngine:
    """
    VendorShield AI — Upgraded Forensic Risk Topology, Pre-Disbursal Payment Gate
    and Dynamic GST Split-Settlement Engine.

    Evaluates the 5-Vector Forensic Risk Topology:
      1. ITC Clawback Risk Index (under CGST Sec 16(2)(c) & Sec 74)
      2. Director Shell Contagion Score (promoter struck-off company ratio)
      3. Address Collocation Density ("Ghost Hub" detection)
      4. Operational Grounding Index (physical premises & transit proof)
      5. Pop-Up Velocity & Bank Mutation Factor (age vs turnover + BEC guard)
      
    Generates 3-Tier Dynamic Treasury Split Settlement Instruction & GSTN IMS Action:
      🟢 FULL_DISBURSAL: Release 100% (GSTN IMS: ACCEPT)
      🟡 STATUTORY_GST_ESCROW: Release Base (Sec 43B(h)), Hold GST (Sec 16(2)(c)) (GSTN IMS: PENDING_HOLD)
      🔴 FORENSIC_FREEZE: Hold 100% (GSTN IMS: REJECT)
    """
    def __init__(self, version: str = "2.1.0"):
        self.version = version
        self.itc_calc = ITCExposureCalculator()

    def evaluate(
        self,
        case_id: str,
        invoice: InvoiceClaim,
        field_checks: List[FieldCheckResult],
        directors: List[DirectorProfile],
        address_cluster: AddressClusterProfile,
        litigation_meta: Dict[str, Any],
        evidence_items: List[EvidenceItem]
    ) -> RiskAssessment:
        reason_codes: List[str] = []
        hard_gates_triggered: List[str] = []
        triggered_rules: List[RuleTrigger] = []

        # ----------------------------------------------------
        # 1. Compute Vector 2: Director Shell Contagion
        # ----------------------------------------------------
        max_contagion = 0.0
        for d in directors:
            if d.contagion_ratio > max_contagion:
                max_contagion = d.contagion_ratio
            if d.is_benami_flagged or d.struck_off_companies_count >= 3:
                hard_gates_triggered.append("DIRECTOR_SHELL_CONTAGION_CRITICAL")
                reason_codes.append(f"DIRECTOR_SHELL_CONTAGION_{int(d.contagion_ratio * 100)}PCT")
                triggered_rules.append(RuleTrigger(
                    rule_id="RULE_DIRECTOR_SHELL_CONTAGION",
                    rule_name="Director Network Struck-Off Contagion",
                    severity="CRITICAL",
                    weight=50,
                    is_hard_gate=True,
                    description=f"Director {d.name} associated with {d.struck_off_companies_count} struck-off entities.",
                    reason_code="DIRECTOR_SHELL_CONTAGION_CRITICAL"
                ))

        # ----------------------------------------------------
        # 2. Compute Vector 3: Address Collocation Density
        # ----------------------------------------------------
        density = address_cluster.collocated_gstins_count
        if address_cluster.is_ghost_hub or density > 15:
            hard_gates_triggered.append("GHOST_HUB_ADDRESS_DETECTED")
            reason_codes.append(f"GHOST_HUB_COLLOCATION_{density}_ENTITIES")
            triggered_rules.append(RuleTrigger(
                rule_id="RULE_GHOST_HUB_COLLOCATION",
                rule_name="Address Ghost Hub Multi-Tenant Shell Density",
                severity="CRITICAL",
                weight=40,
                is_hard_gate=True,
                description=f"Address '{address_cluster.raw_address}' shared by {density} unverified GST entities.",
                reason_code="GHOST_HUB_ADDRESS_DETECTED"
            ))

        # ----------------------------------------------------
        # 3. Compute Vector 4: Operational Grounding Score
        # ----------------------------------------------------
        if address_cluster.premises_type in ["INDUSTRIAL_WAREHOUSE", "COMMERCIAL_HUB"]:
            op_score = 1.0
        elif address_cluster.premises_type == "VIRTUAL_OFFICE":
            op_score = 0.2
            reason_codes.append("VIRTUAL_OFFICE_PREMISES_MISMATCH")
        elif address_cluster.premises_type == "RESIDENTIAL":
            op_score = 0.1
            reason_codes.append("RESIDENTIAL_PREMISES_HIGH_VALUE_COMMERCIAL")
        else:
            op_score = 0.5

        # Factor in e-Way Bill and IRN readiness
        if invoice.eway_bill_missing:
            reason_codes.append("EWAY_BILL_MISSING_HIGH_VALUE")
            op_score = max(0.1, op_score - 0.25)
            triggered_rules.append(RuleTrigger(
                rule_id="RULE_EWAY_BILL_MISSING",
                rule_name="Missing Statutory e-Way Bill for High-Value Goods",
                severity="HIGH",
                weight=20,
                is_hard_gate=False,
                description="Consignment exceeds ₹50,000 threshold without mandatory transit e-Way Bill.",
                reason_code="EWAY_BILL_MISSING_HIGH_VALUE"
            ))

        # ----------------------------------------------------
        # 4. Compute Vector 5: Pop-Up Velocity & Bank Mutation
        # ----------------------------------------------------
        popup_factor = 0.1
        gst_inactive = False
        filing_delay = 0

        # Check Hop 1 GST facts
        gst_evidence = next((e for e in evidence_items if "gst" in e.source_name.lower()), None)
        if gst_evidence and "facts" in gst_evidence.model_dump():
            facts = gst_evidence.facts
            filing_delay = facts.get("filing_delay_months", 0)
            status_val = str(facts.get("gst_status", "")).lower()
            if status_val in ["inactive", "cancelled", "suspended", "cancelled_suo_motu"]:
                gst_inactive = True
                hard_gates_triggered.append("GST_STATUS_INACTIVE_CONFIRMED")
                reason_codes.append("GST_STATUS_INACTIVE_CONFIRMED")
                triggered_rules.append(RuleTrigger(
                    rule_id="RULE_GST_STATUS_INACTIVE",
                    rule_name="GST Registration Inactive or Cancelled",
                    severity="CRITICAL",
                    weight=50,
                    is_hard_gate=True,
                    description=f"Supplier GST status is {status_val.upper()} on public registries.",
                    reason_code="GST_STATUS_INACTIVE_CONFIRMED"
                ))

        # Bank Account BEC Mutation Check
        if getattr(invoice, "bank_mutation_detected", False):
            hard_gates_triggered.append("CRITICAL_BANK_ACCOUNT_MUTATION")
            reason_codes.append("CRITICAL_BANK_ACCOUNT_MUTATION")
            popup_factor = 1.0
            triggered_rules.append(RuleTrigger(
                rule_id="RULE_BANK_MUTATION_BEC",
                rule_name="Remittance Bank Account Mutation Detected",
                severity="CRITICAL",
                weight=50,
                is_hard_gate=True,
                description="Invoice bank account differs from verified historical vendor master. Potential BEC fraud.",
                reason_code="CRITICAL_BANK_ACCOUNT_MUTATION"
            ))
        elif invoice.total_amount > 250000.0 and (max_contagion > 0.2 or density > 10):
            popup_factor = 0.85
            reason_codes.append("POPUP_VENDOR_HIGH_VELOCITY_RISK")

        # ----------------------------------------------------
        # 5. Extended Signals: Judicial Dockets & Procurement Pricing
        # ----------------------------------------------------
        # Hop 2: Judicial Kanoon Dockets
        judicial_contagion = 0.0
        nclt_cases = litigation_meta.get("active_cases", 0)
        nclt_petitions = litigation_meta.get("nclt_petitions", [])
        if nclt_cases > 0 or len(nclt_petitions) > 0:
            judicial_contagion = min(1.0, 0.5 + (0.25 * nclt_cases))
            hard_gates_triggered.append("ACTIVE_INSOLVENCY_PROCEEDING")
            hard_gates_triggered.append("NCLT_INSOLVENCY_PROCEEDINGS_ACTIVE")
            reason_codes.append("NCLT_INSOLVENCY_PROCEEDINGS_ACTIVE")
            triggered_rules.append(RuleTrigger(
                rule_id="RULE_NCLT_INSOLVENCY",
                rule_name="Active NCLT / IBC Insolvency Proceedings",
                severity="CRITICAL",
                weight=50,
                is_hard_gate=True,
                description=f"Active insolvency docket identified on Indian Kanoon: {nclt_petitions[:1]}",
                reason_code="NCLT_INSOLVENCY_PROCEEDINGS_ACTIVE"
            ))

        # Hop 3: DGGI Enforcement Radar
        enforcement_radar = litigation_meta.get("enforcement_radar")
        if enforcement_radar and getattr(enforcement_radar, "enforcement_hit", False):
            judicial_contagion = max(judicial_contagion, 0.9)
            hard_gates_triggered.append("DGGI_FAKE_ITC_ENFORCEMENT_RAID")
            reason_codes.append("DGGI_FAKE_ITC_ENFORCEMENT_RAID")
            triggered_rules.append(RuleTrigger(
                rule_id="RULE_DGGI_ENFORCEMENT",
                rule_name="DGGI Fake-ITC Circular Trading Enforcement Action",
                severity="CRITICAL",
                weight=50,
                is_hard_gate=True,
                description=f"Vendor named in enforcement notice: {enforcement_radar.allegation_summary}",
                reason_code="DGGI_FAKE_ITC_ENFORCEMENT_RAID"
            ))

        # Hop 4: IndiaMART B2B Procurement Price Benchmark
        price_anomaly_score = 0.0
        proc_bench = litigation_meta.get("procurement_benchmark")
        if proc_bench:
            infl_pct = getattr(proc_bench, "price_inflation_pct", 0.0)
            if infl_pct > 50.0:
                price_anomaly_score = min(1.0, infl_pct / 200.0)
                reason_codes.append(f"PROCUREMENT_PRICE_OVERINVOICED_{int(infl_pct)}PCT")
                triggered_rules.append(RuleTrigger(
                    rule_id="RULE_PRICE_INFLATION_ANOMALY",
                    rule_name="B2B Procurement Over-Invoicing & Kickback Risk",
                    severity="HIGH" if infl_pct < 100 else "CRITICAL",
                    weight=30,
                    is_hard_gate=(infl_pct >= 150.0),
                    description=f"Invoice price ₹{proc_bench.billed_unit_price:,.2f} is {infl_pct}% above IndiaMART wholesale median ₹{proc_bench.market_median_price_inr:,.2f}.",
                    reason_code=f"PROCUREMENT_PRICE_OVERINVOICED_{int(infl_pct)}PCT"
                ))
                if infl_pct >= 150.0:
                    hard_gates_triggered.append("CRITICAL_PROCUREMENT_OVERBILLING")

        # Soft Discrepancies & Critical Mismatches from Field Checks
        for fc in field_checks:
            if fc.status == CheckStatus.MISMATCH:
                if fc.reason_code and fc.reason_code not in reason_codes:
                    reason_codes.append(fc.reason_code)
                if fc.reason_code == "GST_STATUS_INACTIVE_CONFIRMED" and "GST_STATUS_INACTIVE_CONFIRMED" not in hard_gates_triggered:
                    hard_gates_triggered.append("GST_STATUS_INACTIVE_CONFIRMED")
                elif fc.reason_code == "CRITICAL_NAME_MISMATCH" and "CRITICAL_NAME_MISMATCH" not in hard_gates_triggered:
                    hard_gates_triggered.append("CRITICAL_NAME_MISMATCH")
            elif fc.status == CheckStatus.POSSIBLE_MATCH:
                if fc.reason_code and fc.reason_code not in reason_codes:
                    reason_codes.append(fc.reason_code)

        # ----------------------------------------------------
        # 6. Compute Vector 1: ITC Clawback Risk & Direct ₹ Liability
        # ----------------------------------------------------
        itc_exposure = self.itc_calc.calculate(
            invoice=invoice,
            director_contagion_score=max_contagion,
            address_ghost_hub=address_cluster.is_ghost_hub,
            gst_inactive=gst_inactive,
            filing_delay_months=filing_delay
        )

        vector_scores = ForensicVectorScores(
            itc_clawback_risk_index=round(itc_exposure.itc_clawback_probability, 3),
            director_shell_contagion_score=round(max_contagion, 3),
            address_collocation_density=density,
            operational_grounding_score=round(op_score, 3),
            popup_velocity_factor=round(popup_factor, 3),
            judicial_insolvency_contagion=round(judicial_contagion, 3),
            procurement_price_anomaly=round(price_anomaly_score, 3),
            popup_velocity_and_bank_mutation=round(max(popup_factor, 1.0 if getattr(invoice, 'bank_mutation_detected', False) else 0.0), 3)
        )

        # ----------------------------------------------------
        # 7. Deterministic Policy Risk Score (0-100) & Outcome
        # ----------------------------------------------------
        # Evidence Completeness
        has_unavailable_evidence = any(e.source_mode == SourceMode.UNAVAILABLE for e in evidence_items)
        has_unavailable_checks = any(c.status in (CheckStatus.UNAVAILABLE, CheckStatus.NOT_FOUND) for c in field_checks)
        if len(evidence_items) == 0 or all(e.source_mode == SourceMode.UNAVAILABLE for e in evidence_items):
            completeness = "INSUFFICIENT"
        elif has_unavailable_evidence or has_unavailable_checks or len(evidence_items) < 4:
            completeness = "PARTIAL"
        else:
            completeness = "COMPLETE"

        policy_score = 100
        critical_blockers = [
            "GST_STATUS_INACTIVE_CONFIRMED",
            "CRITICAL_NAME_MISMATCH",
            "DIRECTOR_SHELL_CONTAGION_CRITICAL",
            "ACTIVE_INSOLVENCY_PROCEEDING",
            "NCLT_INSOLVENCY_PROCEEDINGS_ACTIVE",
            "CRITICAL_BANK_ACCOUNT_MUTATION",
            "DGGI_FAKE_ITC_ENFORCEMENT_RAID"
        ]

        if any(g in hard_gates_triggered for g in critical_blockers):
            policy_score = 0
            outcome = RecommendationOutcome.BLOCK
        else:
            if "LEGAL_NAME_MISMATCH" in reason_codes:
                policy_score -= 20
            if "BANK_OWNERSHIP_UNVERIFIED" in reason_codes:
                policy_score -= 12
            if "EWAY_BILL_MISSING_HIGH_VALUE" in reason_codes:
                policy_score -= 15
            if price_anomaly_score > 0.3:
                policy_score -= int(price_anomaly_score * 30)
            if invoice.arithmetic_valid is False:
                policy_score -= 20

            policy_score = max(0, min(100, policy_score))

            if policy_score >= 85 and len(reason_codes) == 0 and not hard_gates_triggered:
                outcome = RecommendationOutcome.PASS
            else:
                outcome = RecommendationOutcome.MANUAL_REVIEW

        # Fail closed principle: Missing, incomplete, or unavailable evidence must never produce an unverified PASS
        if completeness in ("PARTIAL", "INSUFFICIENT"):
            if "INCOMPLETE_EVIDENCE_FAIL_CLOSED" not in reason_codes:
                reason_codes.append("INCOMPLETE_EVIDENCE_FAIL_CLOSED")
            if outcome == RecommendationOutcome.PASS:
                outcome = RecommendationOutcome.MANUAL_REVIEW
                policy_score = min(policy_score, 75)

        # ----------------------------------------------------
        # 8. Dynamic Treasury Split-Settlement & GSTN IMS Gate
        # ----------------------------------------------------
        gst_tax_claimed = round(invoice.cgst + invoice.sgst + invoice.igst, 2)
        if gst_tax_claimed <= 0.0 and invoice.total_amount > invoice.taxable_amount > 0:
            gst_tax_claimed = round(invoice.total_amount - invoice.taxable_amount, 2)
        base_taxable = round(max(0.0, invoice.total_amount - gst_tax_claimed), 2)
        
        # Statutory Clawback Avoided: Tax + 100% Sec 74 Penalty + 18% Delayed Interest
        clawback_avoided = round(gst_tax_claimed * 2.18, 2)

        now_iso = datetime.now(timezone.utc).isoformat()

        if outcome == RecommendationOutcome.BLOCK:
            settlement_mode = "FORENSIC_FREEZE"
            release_now = 0.0
            escrow_hold = round(invoice.total_amount, 2)
            ims_action = "REJECT"
            msme_compliant = False
            rationale = (
                f"FORENSIC FREEZE: Total payment release halted (₹0.00 disbursed). Critical hard safety gate triggered "
                f"({', '.join(hard_gates_triggered[:2])}). GSTN IMS Portal Action set to REJECT to prevent buyer liability."
            )
        elif outcome == RecommendationOutcome.MANUAL_REVIEW:
            settlement_mode = "STATUTORY_GST_ESCROW"
            release_now = base_taxable
            escrow_hold = gst_tax_claimed
            ims_action = "PENDING_HOLD"
            msme_compliant = True
            rationale = (
                f"STATUTORY GST ESCROW (SPLIT PAYOUT): Disbursing base taxable amount ₹{release_now:,.2f} satisfies MSME Section 43B(h) mandate. "
                f"Retaining GST component ₹{escrow_hold:,.2f} in automated tax escrow safeguards buyer against CGST Sec 16(2)(c) clawback "
                f"(₹{clawback_avoided:,.2f} total exposure avoided) until GSTR-3B filing is confirmed on the 20th. GSTN IMS Action: PENDING."
            )
        else:
            settlement_mode = "FULL_DISBURSAL"
            release_now = round(invoice.total_amount, 2)
            escrow_hold = 0.0
            ims_action = "ACCEPT"
            msme_compliant = True
            rationale = (
                f"FULL DISBURSAL: Supplier verified clean across all 4 forensic hops. "
                f"Zero adverse NCLT dockets, GSTR-3B filings regular, and bank account verified. 100% payout released. GSTN IMS Action: ACCEPT."
            )

        ims_action_payload = {
            "ims_version": "2026.1",
            "gstin_supplier": invoice.gstin,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "total_invoice_value": invoice.total_amount,
            "taxable_value": invoice.taxable_amount or base_taxable,
            "igst_amount": invoice.igst,
            "cgst_amount": invoice.cgst,
            "sgst_amount": invoice.sgst,
            "ims_action": ims_action,
            "action_timestamp": now_iso,
            "settlement_recommendation": settlement_mode,
            "release_now_inr": release_now,
            "escrow_hold_gst_inr": escrow_hold,
            "rejection_reason_codes": reason_codes
        }

        treasury_settlement = TreasurySettlementDetails(
            recommendation=settlement_mode,
            release_now_inr=release_now,
            escrow_hold_gst_inr=escrow_hold,
            statutory_clawback_risk_avoided_inr=clawback_avoided,
            msme_43b_compliant=msme_compliant,
            gstn_ims_action=ims_action,
            settlement_rationale=rationale,
            ims_action_payload=ims_action_payload
        )

        # ----------------------------------------------------
        # 9. Construct Forensic Entity Graph
        # ----------------------------------------------------
        nodes = [
            GraphNode(id="vendor", label=invoice.supplier_name, type="VENDOR", risk_level="WARNING" if outcome != RecommendationOutcome.PASS else "NORMAL")
        ]
        edges = []

        for i, d in enumerate(directors):
            d_id = f"dir_{i}"
            nodes.append(GraphNode(
                id=d_id,
                label=d.name,
                type="DIRECTOR",
                risk_level="CRITICAL" if d.struck_off_companies_count > 0 or d.is_benami_flagged else "NORMAL",
                metadata={"din": d.din, "struck_off": d.struck_off_companies_count, "contagion": d.contagion_ratio}
            ))
            edges.append(GraphEdge(
                source=d_id,
                target="vendor",
                relationship="DIRECTED_BY",
                is_flagged=bool(d.struck_off_companies_count > 0 or d.is_benami_flagged),
                weight=1.5 if d.struck_off_companies_count > 0 else 1.0
            ))

        nodes.append(GraphNode(
            id="addr_node",
            label=address_cluster.raw_address[:35] + ("..." if len(address_cluster.raw_address) > 35 else ""),
            type="ADDRESS",
            risk_level="CRITICAL" if address_cluster.is_ghost_hub else "NORMAL",
            metadata={"premises": address_cluster.premises_type, "collocated_count": density}
        ))
        edges.append(GraphEdge(
            source="vendor",
            target="addr_node",
            relationship="REGISTERED_AT",
            is_flagged=address_cluster.is_ghost_hub,
            weight=2.0 if address_cluster.is_ghost_hub else 1.0
        ))

        entity_graph = EntityGraph(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_flagged_edges=sum(1 for e in edges if e.is_flagged)
        )

        # Determine streaming URL from evidence items if any live run captured it
        live_streaming_url = None
        live_run_id = None
        for ev in evidence_items:
            if getattr(ev, "streaming_url", None):
                live_streaming_url = ev.streaming_url
            if getattr(ev, "run_id", None):
                live_run_id = ev.run_id

        return RiskAssessment(
            assessment_id=f"ass_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            ruleset_version=self.version,
            recommendation=outcome,
            risk_score=policy_score,
            score_explanation=(
                f"Deterministic policy compliance score ({policy_score}/100) reflecting explicit statutory penalties. "
                f"Treasury instruction: {settlement_mode}."
            ),
            reason_codes=reason_codes,
            field_checks=field_checks,
            hard_gates_triggered=hard_gates_triggered,
            triggered_rules=triggered_rules,
            forensic_vectors=vector_scores,
            itc_exposure=itc_exposure,
            entity_graph=entity_graph,
            treasury_settlement=treasury_settlement,
            gstn_ims_action=ims_action,
            ims_action_json=ims_action_payload,
            streaming_url=live_streaming_url,
            run_id=live_run_id,
            evidence_completeness=completeness,
            evidence_provenance_mode=SourceMode.LIVE_TINYFISH_SSE if any(e.source_mode == SourceMode.LIVE for e in evidence_items) else SourceMode.SIMULATED,
            human_signoff_required=True
        )
