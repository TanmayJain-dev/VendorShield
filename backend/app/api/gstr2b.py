from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from sqlalchemy.orm import Session

from ..schemas.gstr2b import Gstr2bEntrySchema, Gstr2bImportResponse, Gstr2bMatchResult
from ..services.reconciler.gstr2b_parser import parse_gstr2b_json
from ..db.database import get_db
from ..db.repository import CaseRepository

router = APIRouter(prefix="/gstr2b", tags=["gstr2b"])

@router.post("/import", response_model=Gstr2bImportResponse, status_code=status.HTTP_201_CREATED)
async def import_gstr2b_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Imports and reconciles official Indian GSTR-2B returns JSON file.
    Parses B2B sections tolerantly, records supplier invoices, and stores entries in persistent DB.
    """
    filename = file.filename or "gstr2b.json"
    if not filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currently GSTR-2B import accepts JSON files downloaded from the GST portal."
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    try:
        entries, summary = parse_gstr2b_json(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse GSTR-2B file: {str(e)}"
        )

    if not entries:
        return Gstr2bImportResponse(
            message="GSTR-2B file parsed successfully, but no B2B invoice rows were found.",
            total_records=0,
            imported_records=0,
            buyer_gstin=summary.get("buyer_gstin"),
            return_period=summary.get("return_period")
        )

    saved_count = CaseRepository.save_gstr2b_entries(db, entries)

    return Gstr2bImportResponse(
        message=f"Successfully imported {saved_count} GSTR-2B B2B invoice entries.",
        total_records=len(entries),
        imported_records=saved_count,
        buyer_gstin=summary.get("buyer_gstin"),
        return_period=summary.get("return_period")
    )

@router.get("/entries", response_model=List[Gstr2bEntrySchema])
async def list_gstr2b_entries(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lists recent imported GSTR-2B entries."""
    models = CaseRepository.list_gstr2b_entries(db, limit=limit)
    return [
        Gstr2bEntrySchema(
            id=m.id,
            period=m.period,
            buyer_gstin=m.buyer_gstin,
            supplier_gstin=m.supplier_gstin,
            supplier_name=m.supplier_name,
            invoice_number=m.invoice_number,
            invoice_date=m.invoice_date,
            invoice_value=m.invoice_value,
            taxable_value=m.taxable_value,
            igst=m.igst,
            cgst=m.cgst,
            sgst=m.sgst,
            cess=m.cess,
            itc_available=m.itc_available,
            imported_at=m.imported_at
        )
        for m in models
    ]

@router.get("/unmatched", response_model=List[Gstr2bEntrySchema])
async def list_unmatched_gstr2b_entries(db: Session = Depends(get_db)):
    """Returns GSTR-2B rows that have not yet been claimed by any case in the accounts payable queue."""
    unmatched_models = CaseRepository.find_unmatched_gstr2b_entries(db)
    return [
        Gstr2bEntrySchema(
            id=m.id,
            period=m.period,
            buyer_gstin=m.buyer_gstin,
            supplier_gstin=m.supplier_gstin,
            supplier_name=m.supplier_name,
            invoice_number=m.invoice_number,
            invoice_date=m.invoice_date,
            invoice_value=m.invoice_value,
            taxable_value=m.taxable_value,
            igst=m.igst,
            cgst=m.cgst,
            sgst=m.sgst,
            cess=m.cess,
            itc_available=m.itc_available,
            imported_at=m.imported_at
        )
        for m in unmatched_models
    ]

@router.get("/match/{case_id}", response_model=Gstr2bMatchResult)
async def check_case_gstr2b_match(
    case_id: str,
    db: Session = Depends(get_db)
):
    """Reconciles a case invoice against persistent GSTR-2B records."""
    case = CaseRepository.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    if not case.invoice:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Case has no extracted invoice claims")

    entry = CaseRepository.find_gstr2b_entry(db, case.invoice.gstin, case.invoice.invoice_number)
    if not entry:
        has_buyer = CaseRepository.has_gstr2b_entries_for_buyer(db, case.invoice.buyer_gstin)
        msg = "Invoice not found in imported GSTR-2B." if has_buyer else "No GSTR-2B data imported for this recipient GSTIN."
        return Gstr2bMatchResult(
            matched=False,
            status="NOT_FOUND",
            value_difference=0.0,
            itc_available=True,
            message=msg
        )

    val_diff = round(abs(case.invoice.total_amount - entry.invoice_value), 2)
    entry_schema = Gstr2bEntrySchema(
        id=entry.id,
        period=entry.period,
        buyer_gstin=entry.buyer_gstin,
        supplier_gstin=entry.supplier_gstin,
        supplier_name=entry.supplier_name,
        invoice_number=entry.invoice_number,
        invoice_date=entry.invoice_date,
        invoice_value=entry.invoice_value,
        taxable_value=entry.taxable_value,
        igst=entry.igst,
        cgst=entry.cgst,
        sgst=entry.sgst,
        cess=entry.cess,
        itc_available=entry.itc_available,
        imported_at=entry.imported_at
    )

    if val_diff > 2.0:
        return Gstr2bMatchResult(
            matched=True,
            status="VALUE_MISMATCH",
            gstr2b_entry=entry_schema,
            value_difference=val_diff,
            itc_available=entry.itc_available,
            message=f"Invoice matched in GSTR-2B but total amount differs by INR {val_diff:.2f} (Filed: INR {entry.invoice_value:.2f})."
        )
    elif not entry.itc_available:
        return Gstr2bMatchResult(
            matched=True,
            status="ITC_NOT_AVAILABLE",
            gstr2b_entry=entry_schema,
            value_difference=val_diff,
            itc_available=False,
            message="Invoice matched in GSTR-2B, but supplier flagged ITC Available = 'No'."
        )
    else:
        return Gstr2bMatchResult(
            matched=True,
            status="MATCHED",
            gstr2b_entry=entry_schema,
            value_difference=val_diff,
            itc_available=True,
            message="Invoice successfully matched in GSTR-2B filing. ITC is claimable."
        )
