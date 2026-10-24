from pydantic import BaseModel, Field
from typing import Optional, List

class LineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0

class InvoiceClaim(BaseModel):
    invoice_number: str
    invoice_date: Optional[str] = None
    supplier_name: str  # Trade name as written on invoice
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    billing_address: Optional[str] = None
    taxable_amount: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    total_amount: float = 0.0
    bank_account_masked: Optional[str] = None  # Always masked (e.g. XXXX-XXXX-1234)
    ifsc_code: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    
    # Validation state
    gstin_format_valid: Optional[bool] = None
    arithmetic_valid: Optional[bool] = None
    raw_text: Optional[str] = None

class InvoiceCorrection(BaseModel):
    corrected_supplier_name: Optional[str] = None
    corrected_gstin: Optional[str] = None
    corrected_total_amount: Optional[float] = None
    correction_notes: Optional[str] = None
