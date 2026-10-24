from typing import Tuple, List, Optional, Dict, Any
from ...schemas.invoice import LineItem

STANDARD_GST_RATES = {0.0, 5.0, 12.0, 18.0, 28.0}


def reconcile_invoice_components(
    taxable_amount: float,
    cgst: float,
    sgst: float,
    igst: float,
    total_amount: float,
    line_items: Optional[List[LineItem]] = None,
    tolerance: float = 1.0
) -> Dict[str, Any]:
    """
    Performs comprehensive deterministic reconciliation of invoice financial components.
    
    Verifications:
    1. Line items sum vs taxable amount / total amount
    2. Individual line item math: quantity * unit_price == total
    3. Tax component reconciliation: taxable_amount + cgst + sgst + igst == total_amount
    4. Intra-state vs Inter-state consistency (CGST == SGST if intra-state; IGST only if inter-state)
    5. Effective GST rate alignment with statutory Indian tax slabs (0%, 5%, 12%, 18%, 28%)
    """
    discrepancies: List[str] = []
    line_math_errors: List[str] = []
    
    # 1. Line item checks
    line_items_sum = 0.0
    line_items_checked = False
    if line_items and len(line_items) > 0:
        line_items_checked = True
        for idx, item in enumerate(line_items, start=1):
            line_items_sum += item.total
            expected_item_total = round(item.quantity * item.unit_price, 2)
            # Check unit math if quantity and unit_price provided
            if item.quantity > 0 and item.unit_price > 0:
                if abs(expected_item_total - item.total) > tolerance:
                    line_math_errors.append(
                        f"Line {idx} ('{item.description}'): {item.quantity} x {item.unit_price:.2f} = "
                        f"{expected_item_total:.2f}, but declared total is {item.total:.2f}"
                    )
        
        # Line items sum should match taxable amount (or gross total if tax inclusive)
        matches_taxable = abs(line_items_sum - taxable_amount) <= tolerance
        matches_total = abs(line_items_sum - total_amount) <= tolerance
        if not (matches_taxable or matches_total):
            discrepancies.append(
                f"Line items sum ({line_items_sum:.2f}) does not match "
                f"taxable amount ({taxable_amount:.2f}) or total amount ({total_amount:.2f})"
            )
            
        discrepancies.extend(line_math_errors)

    # 2. Tax breakdown reconciliation
    total_tax = round(cgst + sgst + igst, 2)
    calculated_total = round(taxable_amount + total_tax, 2)
    total_diff = abs(calculated_total - total_amount)
    
    if total_diff > tolerance:
        discrepancies.append(
            f"Tax breakdown sum ({taxable_amount:.2f} + {cgst:.2f} + {sgst:.2f} + {igst:.2f} = "
            f"{calculated_total:.2f}) does not match declared total amount ({total_amount:.2f}) "
            f"(diff: {total_diff:.2f})"
        )

    # 3. Tax type classification & symmetry
    is_intra_state = (cgst > 0 or sgst > 0)
    is_inter_state = (igst > 0)
    cgst_sgst_symmetric = True
    tax_type = "ZERO_TAX"

    if is_intra_state and is_inter_state:
        tax_type = "CONFLICTING_TAX"
        discrepancies.append(
            f"Both intra-state (CGST: {cgst:.2f}, SGST: {sgst:.2f}) and "
            f"inter-state (IGST: {igst:.2f}) taxes are charged simultaneously"
        )
    elif is_intra_state:
        tax_type = "INTRA_STATE"
        if abs(cgst - sgst) > tolerance:
            cgst_sgst_symmetric = False
            discrepancies.append(
                f"Intra-state tax asymmetry: CGST ({cgst:.2f}) does not equal SGST ({sgst:.2f})"
            )
    elif is_inter_state:
        tax_type = "INTER_STATE"

    # 4. Effective tax rate calculation
    effective_rate: Optional[float] = None
    rate_matched = False
    if taxable_amount > 0 and total_tax > 0:
        raw_rate = (total_tax / taxable_amount) * 100
        effective_rate = round(raw_rate, 2)
        # Check proximity to standard GST slabs within 0.5%
        for slab in STANDARD_GST_RATES:
            if abs(effective_rate - slab) <= 0.5:
                rate_matched = True
                break

    is_valid = (len(discrepancies) == 0)
    reason = "ARITHMETIC_RECONCILED" if is_valid else "; ".join(discrepancies)

    return {
        "is_valid": is_valid,
        "reason": reason,
        "taxable_amount": taxable_amount,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "total_tax": total_tax,
        "calculated_total": calculated_total,
        "declared_total": total_amount,
        "total_diff": round(total_diff, 2),
        "tax_type": tax_type,
        "cgst_sgst_symmetric": cgst_sgst_symmetric,
        "effective_tax_rate": effective_rate,
        "standard_tax_rate_matched": rate_matched,
        "line_items_count": len(line_items) if line_items else 0,
        "line_items_sum": round(line_items_sum, 2) if line_items_checked else None,
        "discrepancies": discrepancies
    }


def validate_invoice_arithmetic(
    taxable_amount: float,
    cgst: float,
    sgst: float,
    igst: float,
    total_amount: float,
    line_items: Optional[List[LineItem]] = None,
    tolerance: float = 1.0
) -> Tuple[bool, str]:
    """
    Validates arithmetic consistency of an invoice.
    Maintains drop-in compatibility with legacy tuple (is_valid, reason).
    """
    reconciliation = reconcile_invoice_components(
        taxable_amount=taxable_amount,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_amount=total_amount,
        line_items=line_items,
        tolerance=tolerance
    )
    return reconciliation["is_valid"], reconciliation["reason"]
