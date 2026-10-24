import uuid
import os
import hashlib
import re
from typing import List, Optional, Tuple
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..schemas.case import Case, CaseSummary
from ..schemas.invoice import InvoiceClaim, InvoiceCorrection, FieldExtractionMeta
from ..schemas.enums import CaseStatus, SourceMode, ExtractionStatus
from ..services.parser.invoice_parser import extract_text_from_pdf_bytes, parse_invoice_text
from ..services.extraction.pipeline import extract_invoice
from ..services.validators.gstin_validator import validate_gstin_format
from ..services.validators.arithmetic_validator import validate_invoice_arithmetic
from ..services.rules.assessment_service import assessment_service
from ..services.reconciler.evidence_reconciler import EvidenceReconciler, normalize_business_name
from ..services.audit.trail import AuditTrailService
from ..db.database import get_db, init_db
from ..db.repository import CaseRepository
from ..config import settings

router = APIRouter(prefix="/cases", tags=["cases"])

reconciler = EvidenceReconciler()
audit_service = AuditTrailService()

# Initialize DB tables on startup
init_db()

def _sanitize_filename(filename: str) -> str:
    """Removes path traversal and special characters from filename."""
    base = os.path.basename(filename)
    cleaned = re.sub(r"[^\w\.-]", "_", base)
    return cleaned[:100]

def _validate_file_upload(filename: str, content: bytes) -> Tuple[bool, str]:
    """Backend validation for file uploads (size, magic bytes, safe filename)."""
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        return False, f"File exceeds maximum size limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB."
    if len(content) == 0:
        return False, "Uploaded file is empty (0 bytes)."

    # Magic byte checks
    is_pdf = content.startswith(b"%PDF-")
    is_png = content.startswith(b"\x89PNG\r\n\x1a\n")
    is_jpeg = content.startswith(b"\xff\xd8")

    if not (is_pdf or is_png or is_jpeg):
        return False, "Invalid file format. Uploaded file does not match PDF, PNG, or JPEG header specifications."

    return True, "VALID"

def _compute_normalized_invoice_key(supplier_name: Optional[str], invoice_number: Optional[str]) -> Optional[str]:
    if not supplier_name or not invoice_number:
        return None
    norm_supp = normalize_business_name(supplier_name)
    norm_inv = re.sub(r"[^\w]", "", invoice_number).lower()
    return f"{norm_supp}_{norm_inv}"

@router.get("", response_model=List[CaseSummary])
async def list_cases(include_demo: bool = False, db: Session = Depends(get_db)):
    """List all vendor verification cases from persistent database storage."""
    return CaseRepository.list_cases(db, include_demo=include_demo)

@router.post("", response_model=Case, status_code=status.HTTP_201_CREATED)
async def create_case(
    file: Optional[UploadFile] = File(None),
    supplier_name: Optional[str] = Form(None),
    gstin: Optional[str] = Form(None),
    invoice_number: Optional[str] = Form(None),
    total_amount: Optional[float] = Form(None),
    is_demo: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Creates a new due-diligence case from an uploaded invoice or manual payload.
    Enforces upload security, duplicate detection, and persistent storage.
    """

    case_id = f"case_{uuid.uuid4().hex[:8]}"
    ref = invoice_number or f"CASE-{uuid.uuid4().hex[:6].upper()}"
    file_sha256 = None
    duplicate_type = None
    duplicate_case_id = None

    # Handle file upload with security validation
    if file:
        raw_filename = file.filename or "invoice.pdf"
        safe_filename = _sanitize_filename(raw_filename)
        content = await file.read()

        is_valid, err_msg = _validate_file_upload(safe_filename, content)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

        # 1. Compute file SHA-256 for duplicate detection
        file_sha256 = hashlib.sha256(content).hexdigest()

        # Persist uploaded file under UPLOAD_DIR/<case_id>/<sha256>.<ext>
        ext = os.path.splitext(safe_filename)[1].lower()
        if not ext:
            if content.startswith(b"%PDF-"):
                ext = ".pdf"
            elif content.startswith(b"\x89PNG"):
                ext = ".png"
            else:
                ext = ".jpg"
        case_upload_dir = os.path.join(settings.UPLOAD_DIR, case_id)
        os.makedirs(case_upload_dir, exist_ok=True)
        saved_file_path = os.path.join(case_upload_dir, f"{file_sha256}{ext}")
        with open(saved_file_path, "wb") as f_out:
            f_out.write(content)

        # Check exact file duplicate in database
        existing_file_case = CaseRepository.find_case_by_file_hash(db, file_sha256)
        if existing_file_case:
            duplicate_type = "EXACT_FILE_DUPLICATE"
            duplicate_case_id = existing_file_case.case_id

        # 2. Extract using layered extraction pipeline (QR + Text + LLM)
        mime_type = file.content_type or ("application/pdf" if ext == ".pdf" else "image/jpeg")
        invoice_claim = await extract_invoice(content, filename=safe_filename, mime_type=mime_type)
        invoice_claim.file_sha256 = file_sha256

        # Override manual fields if explicitly provided in form
        if supplier_name and supplier_name.strip():
            invoice_claim.supplier_name = supplier_name.strip()
            invoice_claim.extraction_metadata["supplier_name"] = FieldExtractionMeta(
                status=ExtractionStatus.MANUALLY_CORRECTED,
                confidence=1.0,
                source="MANUAL",
                extracted_value=supplier_name.strip()
            )
        if gstin and gstin.strip():
            invoice_claim.gstin = gstin.strip().upper()
            invoice_claim.gstin_format_valid, _ = validate_gstin_format(invoice_claim.gstin)
            invoice_claim.extraction_metadata["supplier_gstin"] = FieldExtractionMeta(
                status=ExtractionStatus.MANUALLY_CORRECTED,
                confidence=1.0,
                source="MANUAL",
                extracted_value=invoice_claim.gstin
            )
        if invoice_number and invoice_number.strip():
            invoice_claim.invoice_number = invoice_number.strip()
            ref = invoice_number.strip()
            invoice_claim.extraction_metadata["invoice_number"] = FieldExtractionMeta(
                status=ExtractionStatus.MANUALLY_CORRECTED,
                confidence=1.0,
                source="MANUAL",
                extracted_value=invoice_claim.invoice_number
            )
        if total_amount is not None:
            invoice_claim.total_amount = total_amount
            invoice_claim.extraction_metadata["total_amount"] = FieldExtractionMeta(
                status=ExtractionStatus.MANUALLY_CORRECTED,
                confidence=1.0,
                source="MANUAL",
                extracted_value=total_amount
            )
            # Re-verify arithmetic
            arith_valid, arith_notes = validate_invoice_arithmetic(
                taxable_amount=invoice_claim.taxable_amount,
                cgst=invoice_claim.cgst,
                sgst=invoice_claim.sgst,
                igst=invoice_claim.igst,
                total_amount=total_amount,
                round_off=invoice_claim.round_off,
                discount_amount=invoice_claim.discount_amount
            )
            invoice_claim.arithmetic_valid = arith_valid
            invoice_claim.arithmetic_notes = arith_notes
    else:
        # Manual payload intake - do not fabricate 18% tax or mark arithmetic valid
        gstin_valid, _ = validate_gstin_format(gstin) if gstin else (False, "Missing")
        invoice_claim = InvoiceClaim(
            invoice_number=ref,
            supplier_name=supplier_name or "Unknown Supplier",
            gstin=gstin.upper() if gstin else None,
            total_amount=total_amount or 0.0,
            taxable_amount=0.0,
            cgst=0.0,
            sgst=0.0,
            igst=0.0,
            gstin_format_valid=gstin_valid,
            arithmetic_valid=None,
            arithmetic_notes="ARITHMETIC_UNVERIFIED: Manual entry does not specify tax components or taxable base."
        )

    # 3. Duplicate check on normalized invoice identifier
    norm_key = _compute_normalized_invoice_key(invoice_claim.supplier_name, invoice_claim.invoice_number)
    if norm_key and not duplicate_type:
        existing_key_case = CaseRepository.find_case_by_normalized_key(db, norm_key)
        if existing_key_case and existing_key_case.case_id != case_id:
            # Check amounts
            existing_total = existing_key_case.invoice.total_amount if existing_key_case.invoice else 0.0
            if abs(existing_total - invoice_claim.total_amount) < 1.0:
                duplicate_type = "EXACT_INVOICE_DUPLICATE"
            else:
                duplicate_type = "SUSPECT_INVOICE_REUSE"
            duplicate_case_id = existing_key_case.case_id

    invoice_claim.duplicate_status = duplicate_type
    invoice_claim.duplicate_case_id = duplicate_case_id

    # Create Case
    case = Case(
        case_id=case_id,
        case_reference=ref,
        status=CaseStatus.PARSED,
        source_mode=SourceMode.LIVE if settings.TINYFISH_API_KEY else SourceMode.SIMULATED,
        file_sha256=file_sha256,
        duplicate_of_case_id=duplicate_case_id,
        duplicate_type=duplicate_type,
        is_demo=is_demo,
        invoice=invoice_claim
    )

    # Initial snapshot hash
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)

    # Persist to SQLite
    saved_case = CaseRepository.save_case(db, case, normalized_key=norm_key)

    # Record append-only audit event
    CaseRepository.add_audit_event(
        db=db,
        case_id=case_id,
        event_type="CASE_CREATED",
        actor="ap_analyst",
        actor_role="ap_analyst",
        event_data={
            "case_reference": ref,
            "has_file": file is not None,
            "file_sha256": file_sha256,
            "duplicate_type": duplicate_type,
            "duplicate_case_id": duplicate_case_id
        }
    )

    return saved_case

@router.get("/{case_id}", response_model=Case)
async def get_case(case_id: str, db: Session = Depends(get_db)):
    """Retrieves full details of a single case from persistent database."""
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.patch("/{case_id}/invoice", response_model=Case)
async def correct_invoice_claims(
    case_id: str,
    correction: InvoiceCorrection,
    db: Session = Depends(get_db)
):
    """
    Allows human reviewer to correct extracted invoice fields.
    Automatically recalculates arithmetic/checksums, records an immutable audit event,
    and triggers a fresh evidence reconciliation and assessment when applicable.
    """
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not case.invoice:
        raise HTTPException(status_code=400, detail="No invoice associated with case")

    inv = case.invoice
    corrections_applied = {}

    if correction.corrected_supplier_name:
        corrections_applied["supplier_name"] = {"old": inv.supplier_name, "new": correction.corrected_supplier_name}
        inv.supplier_name = correction.corrected_supplier_name
        inv.extraction_metadata["supplier_name"] = FieldExtractionMeta(status=ExtractionStatus.MANUALLY_CORRECTED, confidence=1.0)

    if correction.corrected_legal_name:
        corrections_applied["legal_name"] = {"old": inv.legal_name, "new": correction.corrected_legal_name}
        inv.legal_name = correction.corrected_legal_name

    if correction.corrected_invoice_number:
        corrections_applied["invoice_number"] = {"old": inv.invoice_number, "new": correction.corrected_invoice_number}
        inv.invoice_number = correction.corrected_invoice_number
        case.case_reference = correction.corrected_invoice_number

    if correction.corrected_invoice_date:
        corrections_applied["invoice_date"] = {"old": inv.invoice_date, "new": correction.corrected_invoice_date}
        inv.invoice_date = correction.corrected_invoice_date

    if correction.corrected_gstin:
        corrections_applied["gstin"] = {"old": inv.gstin, "new": correction.corrected_gstin}
        inv.gstin = correction.corrected_gstin.upper()
        inv.gstin_format_valid, _ = validate_gstin_format(inv.gstin)
        inv.extraction_metadata["gstin"] = FieldExtractionMeta(status=ExtractionStatus.MANUALLY_CORRECTED, confidence=1.0)

    if correction.corrected_taxable_amount is not None:
        corrections_applied["taxable_amount"] = {"old": inv.taxable_amount, "new": correction.corrected_taxable_amount}
        inv.taxable_amount = correction.corrected_taxable_amount
        inv.extraction_metadata["taxable_amount"] = FieldExtractionMeta(status=ExtractionStatus.MANUALLY_CORRECTED, confidence=1.0)

    if correction.corrected_cgst is not None:
        corrections_applied["cgst"] = {"old": inv.cgst, "new": correction.corrected_cgst}
        inv.cgst = correction.corrected_cgst

    if correction.corrected_sgst is not None:
        corrections_applied["sgst"] = {"old": inv.sgst, "new": correction.corrected_sgst}
        inv.sgst = correction.corrected_sgst

    if correction.corrected_igst is not None:
        corrections_applied["igst"] = {"old": inv.igst, "new": correction.corrected_igst}
        inv.igst = correction.corrected_igst

    if correction.corrected_total_amount is not None:
        corrections_applied["total_amount"] = {"old": inv.total_amount, "new": correction.corrected_total_amount}
        inv.total_amount = correction.corrected_total_amount
        inv.extraction_metadata["total_amount"] = FieldExtractionMeta(status=ExtractionStatus.MANUALLY_CORRECTED, confidence=1.0)

    if correction.corrected_bank_account:
        corrections_applied["bank_account"] = {"old": inv.bank_account_masked, "new": correction.corrected_bank_account}
        # Re-mask
        cleaned_ac = re.sub(r"\D", "", correction.corrected_bank_account)
        inv.bank_account_masked = f"XXXX-XXXX-{cleaned_ac[-4:]}" if len(cleaned_ac) > 4 else "****"

    if correction.corrected_ifsc_code:
        corrections_applied["ifsc_code"] = {"old": inv.ifsc_code, "new": correction.corrected_ifsc_code}
        inv.ifsc_code = correction.corrected_ifsc_code.upper()

    # Re-validate arithmetic after corrections
    arith_valid, arith_notes = validate_invoice_arithmetic(
        taxable_amount=inv.taxable_amount,
        cgst=inv.cgst,
        sgst=inv.sgst,
        igst=inv.igst,
        total_amount=inv.total_amount,
        round_off=inv.round_off,
        discount_amount=inv.discount_amount
    )
    inv.arithmetic_valid = arith_valid
    inv.arithmetic_notes = arith_notes

    # If case already had evidence or assessment, rerun unified assessment service
    if case.evidence_items or case.assessment:
        fresh_assessment = assessment_service.assess(case)
        case.assessment = fresh_assessment
        case.status = CaseStatus.READY_FOR_REVIEW

    # Re-compute case snapshot hash
    case.audit_hash_sha256 = audit_service.compute_case_hash(case)

    # Save to DB
    norm_key = _compute_normalized_invoice_key(inv.supplier_name, inv.invoice_number)
    saved_case = CaseRepository.save_case(db, case, normalized_key=norm_key)

    # Add audit event for corrections
    CaseRepository.add_audit_event(
        db=db,
        case_id=case_id,
        event_type="INVOICE_FIELDS_CORRECTED",
        actor=correction.reviewer_id or "reviewer",
        actor_role="ap_analyst",
        event_data={
            "corrections": corrections_applied,
            "notes": correction.correction_notes,
            "reassessment_triggered": case.assessment is not None
        }
    )

    return saved_case


@router.get("/{case_id}/file")
async def get_case_file(case_id: str, db: Session = Depends(get_db)):
    """Returns the raw uploaded PDF or image file for side-by-side verification."""
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    
    case_upload_dir = os.path.join(settings.UPLOAD_DIR, case_id)
    if not os.path.isdir(case_upload_dir):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No uploaded file found for this case")
    
    files = [f for f in os.listdir(case_upload_dir) if os.path.isfile(os.path.join(case_upload_dir, f))]
    if not files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No uploaded file found for this case")
    
    file_path = os.path.join(case_upload_dir, files[0])
    ext = os.path.splitext(file_path)[1].lower()
    media_type = "application/pdf" if ext == ".pdf" else ("image/png" if ext == ".png" else "image/jpeg")
    return FileResponse(file_path, media_type=media_type, filename=files[0])
