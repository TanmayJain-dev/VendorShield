from typing import List, Dict, Any, Optional
from ...schemas.invoice import InvoiceClaim
from ...schemas.forensic_graph import ITCExposureDetails

class ITCExposureCalculator:
    """
    Computes direct financial liability and tax clawback vulnerability under:
    - CGST Act Section 16(2)(c): Condition of actual tax deposit by supplier
    - CGST Act Section 74: Recovery of wrongly availed ITC with 100% mandatory penalty
    - CGST Act Section 50: Statutory interest at 18% to 24% per annum
    - Rule 86A: Blocking of Electronic Credit Ledger
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
        gst_amount = (invoice.cgst + invoice.sgst + invoice.igst)
        if gst_amount <= 0.0 and invoice.total_amount > 0:
            # If line-item tax not explicit, compute implied 18% GST component
            taxable = invoice.taxable_amount if invoice.taxable_amount > 0 else (invoice.total_amount / 1.18)
            gst_amount = invoice.total_amount - taxable

        # 2. Probability of ITC Disallowance / Clawback
        # Base probability from promoter shell contagion & address anomalies
        prob = 0.05  # baseline audit friction
        if gst_inactive:
            prob = 1.0  # confirmed inactive = 100% immediate ITC clawback
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

        # 3. Statutory Penalty & Interest Calculation (Under Section 74 & 50)
        # 100% penalty is standard under Section 74 for fraudulent / bogus supplier transactions
        statutory_penalty = round(gst_amount * 1.0, 2) if prob >= 0.5 else 0.0
        
        # Statutory interest estimated at 18% per annum for 1-year audit realization cycle
        statutory_interest = round(gst_amount * 0.18, 2) if prob >= 0.5 else 0.0

        # Total Potential Financial Liability
        total_liability = round(gst_amount + statutory_penalty + statutory_interest, 2)

        # 4. Applicable Statutory Provisions
        applicable_sections = ["CGST Act 2017, Sec 16(2)(c)"]
        if prob >= 0.5:
            applicable_sections.append("CGST Act 2017, Sec 74 (100% Penalty for Willful Misstatement)")
            applicable_sections.append("CGST Act 2017, Sec 50 (18% p.a. Delayed Tax Interest)")
            applicable_sections.append("CGST Rules, Rule 86A (Electronic Credit Ledger Freeze)")

        # 5. Risk Tier & Direct CFO Advisory
        if prob >= 0.75:
            risk_tier = "CRITICAL"
            cfo_advisory = (
                f"DO NOT RELEASE PAYMENT. Potential immediate clawback of ₹{gst_amount:,.2f} ITC plus "
                f"statutory penalties totaling ₹{total_liability:,.2f}. Vendor exhibits severe shell company "
                f"contagion or inactive registration. Hold invoice and report to Tax Compliance."
            )
        elif prob >= 0.4:
            risk_tier = "HIGH"
            cfo_advisory = (
                f"WITHHOLD GST COMPONENT. Pay only taxable base after obtaining proof of GSTR-3B tax payment "
                f"and GSTR-2B reflection. Potential Section 16(2)(c) reversal exposure of ₹{gst_amount:,.2f}."
            )
        elif prob >= 0.2:
            risk_tier = "MODERATE"
            cfo_advisory = (
                f"VERIFY GSTR-1 REFLECTION. Confirm invoice appears in buyer's GSTR-2B before claiming ITC "
                f"on monthly return. Monitor supplier return filing cadence."
            )
        else:
            risk_tier = "LOW"
            cfo_advisory = (
                f"PROCEED WITH NORMAL CYCLE. Supplier displays consistent tax compliance and clean promoter graph. "
                f"Estimated clawback exposure is nominal (₹0.00)."
            )

        return ITCExposureDetails(
            tax_amount_claimed=round(gst_amount, 2),
            itc_clawback_probability=round(prob, 2),
            statutory_penalty_inr=statutory_penalty,
            estimated_interest_inr=statutory_interest,
            total_financial_liability_inr=total_liability,
            applicable_sections=applicable_sections,
            risk_tier=risk_tier,
            cfo_advisory=cfo_advisory
        )
