from typing import Optional, List
from pydantic import BaseModel, Field

class Gstr2bEntrySchema(BaseModel):
    id: Optional[int] = None
    period: str = Field(..., description="Tax return period (e.g. 102026)")
    buyer_gstin: str = Field(..., description="Recipient / Buyer GSTIN")
    supplier_gstin: str = Field(..., description="Supplier / Vendor GSTIN")
    supplier_name: Optional[str] = None
    invoice_number: str = Field(..., description="Invoice number")
    invoice_date: Optional[str] = None
    invoice_value: float = 0.0
    taxable_value: float = 0.0
    igst: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    cess: float = 0.0
    itc_available: bool = True
    imported_at: Optional[str] = None

class Gstr2bImportResponse(BaseModel):
    message: str
    total_records: int
    imported_records: int
    buyer_gstin: Optional[str] = None
    return_period: Optional[str] = None

class Gstr2bMatchResult(BaseModel):
    matched: bool
    status: str
    gstr2b_entry: Optional[Gstr2bEntrySchema] = None
    value_difference: float = 0.0
    itc_available: bool = True
    message: str
