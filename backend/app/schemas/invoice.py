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
    source_text: Optional[str] = None
    notes: Optional[str] = None

class InvoiceClaim(BaseModel):
    invoice_number: str
    invoice_date: Optional[str] = None
    supplier_name: str  # Trade name as written on invoice
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_gstin: Optional[str] = None
    forensic_anomaly: Optional[str] = None
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
    bank_account_hash: Optional[str] = None    # SHA-256 for mutation comparison
    bank_beneficiary_name: Optional[str] = None
    bank_mutation_detected: bool = False
    beneficiary_name_match_score: Optional[float] = 1.0
    ifsc_code: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)

    # Physical Supply & e-Way Bill / IRN (CGST Sec 16(2)(b))
    irn_hash: Optional[str] = None
    eway_bill_no: Optional[str] = None
    vehicle_no: Optional[str] = None
    eway_bill_required: bool = False
    eway_bill_missing: bool = False

    # Procurement Price Benchmark
    market_benchmark_unit_price: Optional[float] = None
    price_inflation_pct: Optional[float] = None
    
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

class InvoiceCorrection(BaseModel):
    corrected_supplier_name: Optional[str] = None
    supplier_name: Optional[str] = None
    corrected_legal_name: Optional[str] = None
    legal_name: Optional[str] = None
    corrected_invoice_number: Optional[str] = None
    invoice_number: Optional[str] = None
    corrected_invoice_date: Optional[str] = None
    invoice_date: Optional[str] = None
    corrected_gstin: Optional[str] = None
    gstin: Optional[str] = None
    corrected_taxable_amount: Optional[float] = None
    taxable_amount: Optional[float] = None
    corrected_cgst: Optional[float] = None
    cgst: Optional[float] = None
    corrected_sgst: Optional[float] = None
    sgst: Optional[float] = None
    corrected_igst: Optional[float] = None
    igst: Optional[float] = None
    corrected_total_amount: Optional[float] = None
    total_amount: Optional[float] = None
    corrected_bank_account: Optional[str] = None
    bank_account: Optional[str] = None
    corrected_ifsc_code: Optional[str] = None
    ifsc_code: Optional[str] = None
    correction_notes: Optional[str] = None
    reviewer_id: Optional[str] = None


class DocumentParseResponse(BaseModel):
    supplier_name: str
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    gstin_format_valid: Optional[bool] = None
    gstin_checksum_message: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_gstin: Optional[str] = None
    forensic_anomaly: Optional[str] = None
    invoice_number: str
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    base_amount: Optional[float] = None
    gst_amount: Optional[float] = None
    detected_tax_rate: Optional[float] = None
    line_items: List[LineItem] = Field(default_factory=list)
    bank_account_masked: Optional[str] = None
    ifsc_code: Optional[str] = None
    eway_bill_no: Optional[str] = None
    irn_hash: Optional[str] = None
    raw_text_preview: str = ""
    line_item_arithmetic_valid: Optional[bool] = None
    extraction_method: str = "PYMUPDF_TEXT"  # "PYMUPDF_TEXT", "RAPIDOCR_ONNX_300DPI", "HEURISTIC_IMAGE_PARSE"
    extraction_confidence: float = 1.0
    is_scanned_image: bool = False
    missing_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

