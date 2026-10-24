from typing import List, Dict, Any, Optional
from ...schemas.invoice import InvoiceClaim
from ...schemas.forensic_graph import ITCExposureDetails

class ITCExposureCalculator:
    """
    Computes direct financial liability and tax clawback vulnerability estimates under:
    - CGST Act Section 16(2)(c): Statutory requirement of actual tax deposit by supplier
    - CGST Act Section 74: Recovery of wrongly availed ITC with illustrative 100% penalty
    - CGST Act Section 50: Illustrative statutory interest at 18% per annum
    - Rule 86A: Potential blocking of Electronic Credit Ledger

    IMPORTANT:
    The output is an illustrative decision-support projection based on Indian GST risk vectors.
    It is NOT a guaranteed statutory legal liability or a formal assessment by tax authorities.
    """
    def calculate(
        self,
        invoice: InvoiceClaim,
        director_contagion_score: float,
        address_ghost_hub: bool,
        gst_inactive: bool,
        filing_delay_months: int = 0
    ) -> ITCExposureDetails:
        # 1. Total GST tax component claimed on this invoice
        gst_amount = round(invoice.cgst + invoice.sgst + invoice.igst, 2)
        if gst_amount <= 0.0 and invoice.total_amount > 0 and invoice.taxable_amount > 0:
            if invoice.total_amount > invoice.taxable_amount:
                # Difference between total and taxable when line-item tax wasn't explicitly broken out
                gst_amount = round(invoice.total_amount - invoice.taxable_amount, 2)
            else:
                # Zero-rated or exempt supply (total equals taxable)
                gst_amount = 0.0
        elif gst_amount <= 0.0:
            gst_amount = 0.0

        # 2. Estimate ITC Disallowance / Clawback Risk Score
        prob = 0.05  # baseline compliance friction
        if gst_inactive:
            prob = 1.0  # confirmed inactive supplier registration = immediate statutory disallowance under Sec 16(2)(c)
        else:
            if director_contagion_score > 0.4:
                prob += 0.45
            elif director_contagion_score > 0.1:
                prob += 0.20

            if address_ghost_hub:
                prob += 0.25

            if filing_delay_months >= 2:
                prob += 0.15

        prob = min(1.0, max(0.0, prob))

        # 3. Determine Risk Tier
        if prob >= 0.75:
            risk_tier = "CRITICAL"
        elif prob >= 0.4:
            risk_tier = "HIGH"
        elif prob >= 0.2:
            risk_tier = "MODERATE"
        else:
            risk_tier = "LOW"

        # 4. Illustrative Financial Liability Exposure Calculation
        # For LOW risk: the vendor is verified clean; estimated clawback liability is nominal (₹0.00)
        if risk_tier == "LOW" or gst_amount <= 0.0:
            statutory_penalty = 0.0
            statutory_interest = 0.0
            total_liability = 0.0
            applicable_sections = ["CGST Act 2017, Sec 16(2) (Routine credit matching)"]
            cfo_advisory = (
                f"PROCEED WITH NORMAL CYCLE. Supplier displays consistent tax compliance and clean promoter graph. "
                f"Estimated clawback exposure is nominal (₹0.00). Claimed GST: ₹{gst_amount:,.2f}. "
                f"Decision-support projection; not a statutory tax demand."
            )
        elif risk_tier == "MODERATE":
            statutory_penalty = 0.0
            statutory_interest = 0.0
            total_liability = gst_amount
            applicable_sections = ["CGST Act 2017, Sec 16(2)(c) (Tax deposit verification)"]
            cfo_advisory = (
                f"VERIFY GSTR-1 REFLECTION. Confirm invoice appears in buyer's GSTR-2B before claiming ITC "
                f"on monthly return. Potential Section 16(2)(c) reversal exposure of ₹{gst_amount:,.2f}. "
                f"Monitor supplier return filing cadence."
            )
        elif risk_tier == "HIGH":
            # For HIGH risk, if prob >= 0.5 include illustrative Sec 74 penalty and Sec 50 interest
            if prob >= 0.5:
                statutory_penalty = round(gst_amount * 1.0, 2)
                statutory_interest = round(gst_amount * 0.18, 2)
                total_liability = round(gst_amount + statutory_penalty + statutory_interest, 2)
                applicable_sections = [
                    "CGST Act 2017, Sec 16(2)(c)",
                    "CGST Act 2017, Sec 74 (Illustrative 100% Penalty for Willful Misstatement)",
                    "CGST Act 2017, Sec 50 (Illustrative 18% p.a. Delayed Tax Interest)",
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
                f"(illustrative total exposure ₹{total_liability:,.2f} if contested under Sec 74)."
            )
        else:  # CRITICAL
            statutory_penalty = round(gst_amount * 1.0, 2)
            statutory_interest = round(gst_amount * 0.18, 2)
            total_liability = round(gst_amount + statutory_penalty + statutory_interest, 2)
            applicable_sections = [
                "CGST Act 2017, Sec 16(2)(c) (Immediate Reversal)",
                "CGST Act 2017, Sec 74 (Illustrative 100% Penalty for Willful Misstatement)",
                "CGST Act 2017, Sec 50 (Illustrative 18% p.a. Delayed Tax Interest)",
                "CGST Rules, Rule 86A (Electronic Credit Ledger Freeze)"
            ]
            cfo_advisory = (
                f"DO NOT RELEASE PAYMENT. Potential immediate clawback of ₹{gst_amount:,.2f} ITC plus "
                f"illustrative statutory penalties/interest totaling ₹{total_liability:,.2f}. Vendor exhibits "
                f"severe shell company contagion or inactive registration. Hold invoice and escalate to Tax Compliance."
            )

        return ITCExposureDetails(
            tax_amount_claimed=gst_amount,
            itc_clawback_probability=round(prob, 2),
            statutory_penalty_inr=statutory_penalty,
            estimated_interest_inr=statutory_interest,
            total_financial_liability_inr=total_liability,
            applicable_sections=applicable_sections,
            risk_tier=risk_tier,
            cfo_advisory=cfo_advisory
        )
