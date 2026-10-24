import uuid
from typing import List, Dict, Any, Optional
from ...schemas.invoice import InvoiceClaim
from ...schemas.evidence import FieldCheckResult, EvidenceItem
from ...schemas.forensic_graph import (
    ForensicVectorScores,
    ITCExposureDetails,
    DirectorProfile,
    AddressClusterProfile,
    GraphNode,
    GraphEdge,
    EntityGraph
)
from ...schemas.assessment import RiskAssessment
from ...schemas.enums import RecommendationOutcome, CheckStatus, SourceMode
from .itc_calculator import ITCExposureCalculator

class ForensicRiskEngine:
    """
    VendorShield 2.0 Forensic Risk Topology & Entity Graph Engine.
    Evaluates:
      1. ITC Clawback Risk Index (under CGST Sec 16(2)(c) & Sec 74)
      2. Director Shell Contagion Score (promoter struck-off company ratio)
      3. Address Collocation Density ("Ghost Hub" detection)
      4. Operational Grounding Index (physical premises reality check)
      5. Pop-Up Velocity Factor (age vs billing spike)
    """
    def __init__(self, version: str = "2.0.0"):
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

        # ----------------------------------------------------
        # 2. Compute Vector 3: Address Collocation Density
        # ----------------------------------------------------
        density = address_cluster.collocated_gstins_count
        if address_cluster.is_ghost_hub or density > 15:
            hard_gates_triggered.append("GHOST_HUB_ADDRESS_DETECTED")
            reason_codes.append(f"GHOST_HUB_COLLOCATION_{density}_ENTITIES")

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

        # ----------------------------------------------------
        # 4. Compute Vector 5: Pop-Up Velocity Factor
        # ----------------------------------------------------
        popup_factor = 0.1
        # Check if invoice amount is high (> ₹2.5L) on entity with recent registration
        gst_evidence = next((e for e in evidence_items if "gst" in e.source_name.lower()), None)
        filing_delay = 0
        gst_inactive = False
        if gst_evidence and "facts" in gst_evidence.model_dump():
            facts = gst_evidence.facts
            filing_delay = facts.get("filing_delay_months", 0)
            gst_inactive = facts.get("status", "").lower() in ["inactive", "cancelled", "suspended"]
            if facts.get("cash_tax_ratio", 1.0) < 0.01:
                reason_codes.append("CIRCULAR_TRADING_ZERO_CASH_TAX")

        if invoice.total_amount > 250000.0 and (max_contagion > 0.2 or density > 10):
            popup_factor = 0.85
            reason_codes.append("POPUP_VENDOR_HIGH_VELOCITY_RISK")

        # ----------------------------------------------------
        # 5. Compute Vector 1: ITC Clawback Risk & Direct ₹ Liability
        # ----------------------------------------------------
        itc_exposure = self.itc_calc.calculate(
            invoice=invoice,
            director_contagion_score=max_contagion,
            address_ghost_hub=address_cluster.is_ghost_hub,
            gst_inactive=gst_inactive,
            filing_delay_months=filing_delay
        )
        itc_index = itc_exposure.itc_clawback_probability

        # Pack 5 Forensic Vectors
        forensic_vectors = ForensicVectorScores(
            itc_clawback_risk_index=round(itc_index, 2),
            director_shell_contagion_score=round(max_contagion, 2),
            address_collocation_density=density,
            operational_grounding_score=round(op_score, 2),
            popup_velocity_factor=round(popup_factor, 2)
        )

        # ----------------------------------------------------
        # 6. Check Litigation & Insolvency
        # ----------------------------------------------------
        if litigation_meta.get("active_cases", 0) > 0 or len(litigation_meta.get("nclt_petitions", [])) > 0:
            hard_gates_triggered.append("ACTIVE_INSOLVENCY_PROCEEDING")
            reason_codes.append("NCLT_IBC_INSOLVENCY_PETITION_ACTIVE")

        # ----------------------------------------------------
        # 7. Check Field Reconciliations & Basic Rules
        # ----------------------------------------------------
        if invoice.gstin_format_valid is False:
            hard_gates_triggered.append("GSTIN_FORMAT_INVALID")
            reason_codes.append("GSTIN_FORMAT_INVALID")

        if invoice.arithmetic_valid is False:
            reason_codes.append("INVOICE_ARITHMETIC_MISMATCH")

        for chk in field_checks:
            if chk.reason_code and chk.reason_code not in reason_codes:
                reason_codes.append(chk.reason_code)
            if chk.reason_code == "GST_STATUS_INACTIVE_CONFIRMED":
                hard_gates_triggered.append("GST_STATUS_INACTIVE_CONFIRMED")
            elif chk.reason_code == "CRITICAL_NAME_MISMATCH":
                hard_gates_triggered.append("CRITICAL_NAME_MISMATCH")

        # ----------------------------------------------------
        # 8. Construct Entity Knowledge Graph
        # ----------------------------------------------------
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # Vendor Node
        vendor_node_risk = "CRITICAL" if len(hard_gates_triggered) > 0 else "WARNING" if len(reason_codes) > 0 else "NORMAL"
        nodes.append(GraphNode(
            id="node_vendor",
            label=invoice.supplier_name,
            type="VENDOR",
            risk_level=vendor_node_risk,
            metadata={"gstin": invoice.gstin, "amount": invoice.total_amount}
        ))

        # Director Nodes & Edges
        for idx, d in enumerate(directors):
            d_node_id = f"node_dir_{idx}"
            d_risk = "CRITICAL" if d.contagion_ratio > 0.3 else "WARNING" if d.contagion_ratio > 0 else "NORMAL"
            nodes.append(GraphNode(
                id=d_node_id,
                label=f"{d.name} (DIN: {d.din})",
                type="DIRECTOR",
                risk_level=d_risk,
                metadata={
                    "total_companies": d.associated_companies_count,
                    "struck_off": d.struck_off_companies_count,
                    "contagion": d.contagion_ratio
                }
            ))
            edges.append(GraphEdge(
                source="node_vendor",
                target=d_node_id,
                relationship="DIRECTED_BY",
                is_flagged=(d.contagion_ratio > 0.2),
                weight=1.0 + d.contagion_ratio
            ))

            # If struck-off companies exist, add a contagion cluster node
            if d.struck_off_companies_count > 0:
                sister_node_id = f"node_struckoff_{idx}"
                nodes.append(GraphNode(
                    id=sister_node_id,
                    label=f"{d.struck_off_companies_count} Struck-Off Firms (Sec 248)",
                    type="SISTER_COMPANY",
                    risk_level="CRITICAL",
                    metadata={"reason": "Non-operational / Bogus shell removal"}
                ))
                edges.append(GraphEdge(
                    source=d_node_id,
                    target=sister_node_id,
                    relationship="PROMOTED_DELETERIOUS_SHELLS",
                    is_flagged=True,
                    weight=2.0
                ))

        # Address Node & Edge
        addr_risk = "CRITICAL" if address_cluster.is_ghost_hub else "NORMAL"
        nodes.append(GraphNode(
            id="node_address",
            label=f"Address Hub ({address_cluster.collocated_gstins_count} GSTINs)",
            type="ADDRESS",
            risk_level=addr_risk,
            metadata={"premises": address_cluster.premises_type, "collocated_count": address_cluster.collocated_gstins_count}
        ))
        edges.append(GraphEdge(
            source="node_vendor",
            target="node_address",
            relationship="REGISTERED_AT",
            is_flagged=address_cluster.is_ghost_hub,
            weight=1.5 if address_cluster.is_ghost_hub else 1.0
        ))

        # Litigation Node & Edge if active
        if litigation_meta.get("active_cases", 0) > 0:
            nodes.append(GraphNode(
                id="node_nclt",
                label="NCLT Insolvency Petition (IBC Sec 9)",
                type="LITIGATION",
                risk_level="CRITICAL",
                metadata={"petitions": litigation_meta.get("nclt_petitions", [])}
            ))
            edges.append(GraphEdge(
                source="node_vendor",
                target="node_nclt",
                relationship="INSOLVENCY_DEFENDANT",
                is_flagged=True,
                weight=3.0
            ))

        entity_graph = EntityGraph(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_flagged_edges=sum(1 for e in edges if e.is_flagged)
        )

        # ----------------------------------------------------
        # 9. Composite Safety Score & Outcome Decision
        # ----------------------------------------------------
        score = 100
        # Deduct mathematically based on the 5 vectors
        score -= int(itc_index * 35)                    # up to -35 for ITC clawback risk
        score -= int(max_contagion * 30)                 # up to -30 for shell promoter contagion
        score -= int(min(1.0, density / 20.0) * 20)      # up to -20 for ghost hub density
        score -= int((1.0 - op_score) * 15)              # up to -15 for premises mismatch
        score -= int(popup_factor * 10)                  # up to -10 for popup spike

        score = max(0, min(100, score))

        # Recommendation
        critical_blockers = [
            "GST_STATUS_INACTIVE_CONFIRMED",
            "CRITICAL_NAME_MISMATCH",
            "DIRECTOR_SHELL_CONTAGION_CRITICAL",
            "ACTIVE_INSOLVENCY_PROCEEDING"
        ]
        if any(g in hard_gates_triggered for g in critical_blockers):
            recommendation = RecommendationOutcome.BLOCK
        elif hard_gates_triggered or len(reason_codes) > 0 or score < 75:
            recommendation = RecommendationOutcome.MANUAL_REVIEW
        else:
            recommendation = RecommendationOutcome.PASS

        # Completeness
        has_unavailable_evidence = any(e.source_mode == SourceMode.UNAVAILABLE for e in evidence_items)
        has_unavailable_checks = any(c.status in (CheckStatus.UNAVAILABLE, CheckStatus.NOT_FOUND) for c in field_checks)
        if len(evidence_items) == 0 or all(e.source_mode == SourceMode.UNAVAILABLE for e in evidence_items):
            completeness = "INSUFFICIENT"
        elif has_unavailable_evidence or has_unavailable_checks:
            completeness = "PARTIAL"
        else:
            completeness = "COMPLETE"

        # Fail closed principle: Missing, incomplete, or unavailable evidence must never produce an unverified PASS
        if completeness in ("PARTIAL", "INSUFFICIENT"):
            if "INCOMPLETE_EVIDENCE_FAIL_CLOSED" not in reason_codes:
                reason_codes.append("INCOMPLETE_EVIDENCE_FAIL_CLOSED")
            if recommendation == RecommendationOutcome.PASS:
                recommendation = RecommendationOutcome.MANUAL_REVIEW

        return RiskAssessment(
            assessment_id=f"assess_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            ruleset_version=self.version,
            recommendation=recommendation,
            risk_score=score,
            reason_codes=reason_codes,
            field_checks=field_checks,
            hard_gates_triggered=hard_gates_triggered,
            forensic_vectors=forensic_vectors,
            itc_exposure=itc_exposure,
            entity_graph=entity_graph,
            evidence_completeness=completeness,
            human_signoff_required=True
        )
