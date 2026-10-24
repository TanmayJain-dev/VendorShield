from typing import List, Dict, Any, Optional
from ...schemas.invoice import InvoiceClaim
from ...schemas.forensic_graph import ITCExposureDetails

# Configurable statutory benchmark parameters (subject to CA verification)
STATUTORY_PENALTY_RATE: float = 1.0  # 100% under CGST Sec 74 / Sec 74A (Finance Act 2024)
STATUTORY_INTEREST_RATE: float = 0.18  # 18% p.a. under CGST Sec 50(1) (or 24% under Sec 50(3) for utilized credit)

class ITCExposureCalculator:
    """
    Computes illustrative financial exposure and Input Tax Credit (ITC) clawback risk estimates.
    
    Statutory Framework:
    - CGST Act Section 16(2)(c): Statutory condition of actual tax deposit by supplier.
    - CGST Act Section 74 / Section 74A (Finance Act 2024): Recovery with illustrative 100% penalty.
    - CGST Act Section 50(1) / Section 50(3): Delayed tax interest at 18% to 24% p.a.
    - CGST Rules, Rule 86A: Potential blocking of Electronic Credit Ledger.

    IMPORTANT STATUTORY NOTICE:
    As amended by the Finance Act 2024, Section 74A governs demands for FY 2024-25 onward.
    Section 50(3) specifies a 24% p.a. interest rate for ITC wrongly availed AND utilized.
    All outputs are illustrative decision-support estimates; NOT formal statutory tax demands.
    Always verify with a certified Chartered Accountant (CA) before financial provisioning.
    """
    def __init__(
        self,
        penalty_rate: float = STATUTORY_PENALTY_RATE,
        interest_rate: float = STATUTORY_INTEREST_RATE
    ):
        self.penalty_rate = penalty_rate
        self.interest_rate = interest_rate

    def calculate(
        self,
        invoice: InvoiceClaim,
        director_contagion_score: float,
        address_ghost_hub: bool,
        gst_inactive: bool,
        filing_delay_months: int = 0
    ) -> ITCExposureDetails:
        # 1. Total GST tax component claimed on this invoice (strictly from extracted non-inferred tax)
        gst_amount = round(invoice.cgst + invoice.sgst + invoice.igst, 2)
        if gst_amount <= 0.0 and invoice.total_amount > 0 and invoice.taxable_amount > 0:
            if invoice.total_amount > invoice.taxable_amount:
                gst_amount = round(invoice.total_amount - invoice.taxable_amount, 2)
            else:
                gst_amount = 0.0
        elif gst_amount <= 0.0:
            gst_amount = 0.0

        # 2. ITC Risk Score (Heuristic index from 0.0 to 1.0, not a statistical probability)
        risk_score = 0.05  # baseline compliance friction
        if gst_inactive:
            risk_score = 1.0  # confirmed inactive supplier registration = immediate disallowance under Sec 16(2)(c)
        else:
            if director_contagion_score > 0.4:
                risk_score += 0.45
            elif director_contagion_score > 0.1:
                risk_score += 0.20

            if address_ghost_hub:
                risk_score += 0.25

            if filing_delay_months >= 2:
                risk_score += 0.15

        risk_score = min(1.0, max(0.0, risk_score))

        # 3. Determine Risk Tier
        if risk_score >= 0.75:
            risk_tier = "CRITICAL"
        elif risk_score >= 0.4:
            risk_tier = "HIGH"
        elif risk_score >= 0.2:
            risk_tier = "MODERATE"
        else:
            risk_tier = "LOW"

        # 4. Illustrative Financial Liability Exposure Calculation
        # For LOW risk: clean vendor -> estimated exposure is nominal (₹0.00)
        if risk_tier == "LOW" or gst_amount <= 0.0:
            statutory_penalty = 0.0
            statutory_interest = 0.0
            total_liability = 0.0
            applicable_sections = ["CGST Act 2017, Sec 16(2) (Routine credit matching)"]
            cfo_advisory = (
                f"PROCEED WITH NORMAL CYCLE. Supplier displays consistent tax compliance and clean promoter graph. "
                f"Estimated clawback exposure is nominal (₹0.00). Claimed GST: ₹{gst_amount:,.2f}. "
                f"Decision-support projection (verify with Chartered Accountant)."
            )
        elif risk_tier == "MODERATE":
            statutory_penalty = 0.0
            statutory_interest = 0.0
            total_liability = gst_amount
            applicable_sections = ["CGST Act 2017, Sec 16(2)(c) (Tax deposit verification)"]
            cfo_advisory = (
                f"VERIFY GSTR-1 REFLECTION. Confirm invoice appears in buyer's GSTR-2B before claiming ITC "
                f"on monthly return. Potential Section 16(2)(c) reversal exposure of ₹{gst_amount:,.2f}. "
                f"Monitor supplier return filing cadence. (Verify with Chartered Accountant)."
            )
        elif risk_tier == "HIGH":
            if risk_score >= 0.5:
                statutory_penalty = round(gst_amount * self.penalty_rate, 2)
                statutory_interest = round(gst_amount * self.interest_rate, 2)
                total_liability = round(gst_amount + statutory_penalty + statutory_interest, 2)
                applicable_sections = [
                    "CGST Act 2017, Sec 16(2)(c)",
                    "CGST Act 2017, Sec 74 / Sec 74A (Illustrative 100% Penalty for Willful Misstatement)",
                    "CGST Act 2017, Sec 50(1) (Illustrative 18% p.a. Delayed Tax Interest)",
                    "CGST Rules, Rule 86A (Electronic Credit Ledger Freeze)"
                ]
            else:
                statutory_penalty = 0.0
                statutory_interest = 0.0
                total_liability = gst_amount
                applicable_sections = ["CGST Act 2017, Sec 16(2)(c)"]

            cfo_advisory = (
                f"WITHHOLD GST COMPONENT. Pay only taxable base after obtaining proof of GSTR-3B tax payment "
                f"and GSTR-2B reflection. Potential Section 16(2)(c) reversal exposure of ₹{gst_amount:,.2f} "
                f"(illustrative total exposure ₹{total_liability:,.2f} if contested under Sec 74/74A). "
                f"(Verify with Chartered Accountant)."
            )
        else:  # CRITICAL
            statutory_penalty = round(gst_amount * self.penalty_rate, 2)
            statutory_interest = round(gst_amount * self.interest_rate, 2)
            total_liability = round(gst_amount + statutory_penalty + statutory_interest, 2)
            applicable_sections = [
                "CGST Act 2017, Sec 16(2)(c) (Immediate Reversal)",
                "CGST Act 2017, Sec 74 / Sec 74A (Illustrative 100% Penalty for Willful Misstatement)",
                "CGST Act 2017, Sec 50(1) (Illustrative 18% p.a. Delayed Tax Interest)",
                "CGST Rules, Rule 86A (Electronic Credit Ledger Freeze)"
            ]
            cfo_advisory = (
                f"DO NOT RELEASE PAYMENT. Potential immediate clawback of ₹{gst_amount:,.2f} ITC plus "
                f"illustrative statutory penalties/interest totaling ₹{total_liability:,.2f}. Vendor exhibits "
                f"severe shell company contagion or inactive registration. Hold invoice and escalate to Tax Compliance. "
                f"(Verify with Chartered Accountant)."
            )

        return ITCExposureDetails(
            tax_amount_claimed=gst_amount,
            itc_clawback_probability=round(risk_score, 2),
            statutory_penalty_inr=statutory_penalty,
            estimated_interest_inr=statutory_interest,
            total_financial_liability_inr=total_liability,
            applicable_sections=applicable_sections,
            risk_tier=risk_tier,
            cfo_advisory=cfo_advisory
        )
