import uuid
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from ..schemas.case import Case, CaseSummary
from ..schemas.invoice import InvoiceClaim, InvoiceCorrection
from ..schemas.enums import CaseStatus, SourceMode
from ..services.parser.invoice_parser import extract_text_from_pdf_bytes, parse_invoice_text
from ..services.validators.gstin_validator import validate_gstin_format
from ..config import settings

router = APIRouter(prefix="/cases", tags=["cases"])

# In-memory case storage for API runtime
case_store: Dict[str, Case] = {}

def seed_benchmark_case():
    """Seeds the benchmark case from the submitted HackIIITD deck (Apex Courier)."""
    case_id = "case_inv_2026_8841"
    if case_id not in case_store:
        case = Case(
            case_id=case_id,
            case_reference="INV-2026-8841",
            status=CaseStatus.PARSED,
            source_mode=SourceMode.SIMULATED,
            invoice=InvoiceClaim(
                invoice_number="INV-2026-8841",
                invoice_date="2026-10-15",
                supplier_name="Apex Courier",
                gstin="07AAAAA0000A1Z5",
                billing_address="Okhla Industrial Area, Phase-II, New Delhi - 110020",
                taxable_amount=408898.31,
                cgst=36800.85,
                sgst=36800.85,
                igst=0.0,
                total_amount=482500.0,
                bank_account_masked="XXXX-XXXX-9921",
                ifsc_code="HDFC0000123",
                gstin_format_valid=True,
                arithmetic_valid=True
            )
        )
        case_store[case_id] = case

seed_benchmark_case()

@router.get("", response_model=List[CaseSummary])
async def list_cases():
    """List all vendor verification cases."""
    summaries = []
    for c in case_store.values():
        summaries.append(CaseSummary(
            case_id=c.case_id,
            case_reference=c.case_reference,
            status=c.status,
            supplier_name=c.invoice.supplier_name if c.invoice else "Unknown",
            invoice_number=c.invoice.invoice_number if c.invoice else "N/A",
            total_amount=c.invoice.total_amount if c.invoice else 0.0,
            recommendation=c.assessment.recommendation if c.assessment else None,
            created_at=c.created_at
        ))
    return sorted(summaries, key=lambda x: x.created_at, reverse=True)

@router.post("", response_model=Case, status_code=status.HTTP_201_CREATED)
async def create_case(
    file: Optional[UploadFile] = File(None),
    supplier_name: Optional[str] = Form(None),
    gstin: Optional[str] = Form(None),
    invoice_number: Optional[str] = Form(None),
    total_amount: Optional[float] = Form(None)
):
    """
    Creates a new due-diligence case from an uploaded invoice or manual payload.
    """
    case_id = f"case_{uuid.uuid4().hex[:8]}"
    ref = invoice_number or f"CASE-{uuid.uuid4().hex[:6].upper()}"
    
    # If a file is uploaded, parse it
    if file:
        content = await file.read()
        raw_text = extract_text_from_pdf_bytes(content)
        invoice_claim = parse_invoice_text(raw_text, default_supplier=supplier_name or "Unknown Supplier")
        
        # Override with manual fields if provided
        if gstin:
            invoice_claim.gstin = gstin
            invoice_claim.gstin_format_valid, _ = validate_gstin_format(gstin)
        if total_amount:
            invoice_claim.total_amount = total_amount
    else:
        gstin_valid, _ = validate_gstin_format(gstin) if gstin else (False, "Missing")
        invoice_claim = InvoiceClaim(
            invoice_number=ref,
            supplier_name=supplier_name or "Unknown Supplier",
            gstin=gstin,
            total_amount=total_amount or 0.0,
            gstin_format_valid=gstin_valid,
            arithmetic_valid=True
        )

    case = Case(
        case_id=case_id,
        case_reference=ref,
        status=CaseStatus.PARSED,
        source_mode=SourceMode.LIVE if settings.TINYFISH_API_KEY else SourceMode.SIMULATED,
        invoice=invoice_claim
    )
    case_store[case_id] = case
    return case

@router.get("/{case_id}", response_model=Case)
async def get_case(case_id: str):
    """Retrieves full details of a single case."""
    if case_id not in case_store:
        raise HTTPException(status_code=404, detail="Case not found")
    return case_store[case_id]

@router.patch("/{case_id}/invoice", response_model=Case)
async def correct_invoice_claims(case_id: str, correction: InvoiceCorrection):
    """Allows human reviewer to correct OCR extracted claims."""
    if case_id not in case_store:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = case_store[case_id]
    if not case.invoice:
        raise HTTPException(status_code=400, detail="No invoice associated with case")

    if correction.corrected_supplier_name:
        case.invoice.supplier_name = correction.corrected_supplier_name
    if correction.corrected_gstin:
        case.invoice.gstin = correction.corrected_gstin
        case.invoice.gstin_format_valid, _ = validate_gstin_format(correction.corrected_gstin)
    if correction.corrected_total_amount is not None:
        case.invoice.total_amount = correction.corrected_total_amount
        
    return case
