from typing import Tuple, List, Optional
from ...schemas.invoice import LineItem

def validate_invoice_arithmetic(
    taxable_amount: float,
    cgst: float,
    sgst: float,
    igst: float,
    total_amount: float,
    line_items: Optional[List[LineItem]] = None,
    round_off: float = 0.0,
    discount_amount: float = 0.0,
    tolerance: float = 1.0
) -> Tuple[bool, str]:
    """
    Validates arithmetic consistency of an invoice:
    1. Sum of line items ~= taxable_amount (if line items provided)
    2. taxable_amount + cgst + sgst + igst + round_off - discount_amount ~= total_amount
    """
    # 1. Verify line items sum if present
    if line_items and len(line_items) > 0:
        line_items_sum = sum(item.total for item in line_items)
        if abs(line_items_sum - taxable_amount) > tolerance and abs(line_items_sum - total_amount) > tolerance:
            return False, (
                f"Line items sum ({line_items_sum:.2f}) does not match "
                f"taxable amount ({taxable_amount:.2f}) or total ({total_amount:.2f})"
            )

    # 2. Verify total reconciliation
    calculated_total = taxable_amount + cgst + sgst + igst + round_off - discount_amount
    if abs(calculated_total - total_amount) > tolerance:
        return False, (
            f"Tax breakdown sum ({taxable_amount:.2f} + {cgst:.2f} + {sgst:.2f} + {igst:.2f} + round_off {round_off:.2f} - discount {discount_amount:.2f} = {calculated_total:.2f}) "
            f"does not match declared total amount ({total_amount:.2f})"
        )

    return True, "ARITHMETIC_RECONCILED"
