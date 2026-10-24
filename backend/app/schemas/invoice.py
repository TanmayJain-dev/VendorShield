from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .enums import ExtractionStatus

class LineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0
    tax_rate: Optional[float] = None

class TaxBreakdownItem(BaseModel):
    tax_type: str  # e.g., "CGST", "SGST", "IGST"
    rate_pct: float  # e.g., 9.0, 18.0
    taxable_amount: float = 0.0
    tax_amount: float = 0.0
    status: ExtractionStatus = ExtractionStatus.EXTRACTED

class FieldExtractionMeta(BaseModel):
    status: ExtractionStatus = ExtractionStatus.EXTRACTED
    confidence: float = 1.0
    source: Optional[str] = None  # QR, LLM, REGEX, MANUAL
    extracted_value: Optional[Any] = None
    source_text: Optional[str] = None
    notes: Optional[str] = None

class InvoiceClaim(BaseModel):
    invoice_number: str
    invoice_date: Optional[str] = None
    supplier_name: str  # Trade name as written on invoice
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    billing_address: Optional[str] = None
    place_of_supply: Optional[str] = None
    discount_amount: float = 0.0
    round_off: float = 0.0
    taxable_amount: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    total_amount: float = 0.0
    tax_breakdown: List[TaxBreakdownItem] = Field(default_factory=list)
    bank_account_masked: Optional[str] = None  # Always masked (e.g. XXXX-XXXX-1234)
    ifsc_code: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    
    # Validation state
    gstin_format_valid: Optional[bool] = None
    arithmetic_valid: Optional[bool] = None
    arithmetic_notes: Optional[str] = None
    raw_text: Optional[str] = None

    # Extraction provenance & uncertainty
    tax_inferred: bool = False
    tax_inference_reason: Optional[str] = None
    extraction_metadata: Dict[str, FieldExtractionMeta] = Field(default_factory=dict)
    parsing_errors: List[str] = Field(default_factory=list)
    parsing_warnings: List[str] = Field(default_factory=list)
    is_scanned_image: bool = False
    ocr_applied: bool = False
    ocr_status_message: Optional[str] = None

    # Duplicate tracking
    file_sha256: Optional[str] = None
    duplicate_status: Optional[str] = None
    duplicate_case_id: Optional[str] = None
    buyer_gstin: Optional[str] = None
    buyer_name: Optional[str] = None
    irn: Optional[str] = None
    qr_data: Optional[Dict[str, Any]] = None
    qr_signature_status: Optional[str] = None
    extraction_conflicts: List[Dict[str, Any]] = Field(default_factory=list)

class InvoiceCorrection(BaseModel):
    corrected_supplier_name: Optional[str] = None
    corrected_legal_name: Optional[str] = None
    corrected_invoice_number: Optional[str] = None
    corrected_invoice_date: Optional[str] = None
    corrected_gstin: Optional[str] = None
    corrected_taxable_amount: Optional[float] = None
    corrected_cgst: Optional[float] = None
    corrected_sgst: Optional[float] = None
    corrected_igst: Optional[float] = None
    corrected_total_amount: Optional[float] = None
    corrected_bank_account: Optional[str] = None
    corrected_ifsc_code: Optional[str] = None
    correction_notes: Optional[str] = None
    reviewer_id: Optional[str] = None
