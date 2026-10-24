import pytest
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.database import Base
from backend.app.db.models import CaseModel
from backend.app.db.repository import CaseRepository
from backend.app.schemas.case import Case
from backend.app.schemas.invoice import InvoiceClaim
from backend.app.schemas.enums import CaseStatus, SourceMode

def test_case_persistence_across_sessions(tmp_path):
    """Verifies case data survives database connection restarts."""
    db_file = tmp_path / "test_persist.db"
    db_url = f"sqlite:///{db_file}"

    # Session 1: Create DB & persist case
    engine1 = create_engine(db_url)
    Base.metadata.create_all(bind=engine1)
    Session1 = sessionmaker(bind=engine1)
    db1 = Session1()

    case_id = f"case_persist_{uuid.uuid4().hex[:6]}"
    case = Case(
        case_id=case_id,
        case_reference="INV-PERSIST-101",
        status=CaseStatus.PARSED,
        source_mode=SourceMode.SIMULATED,
        invoice=InvoiceClaim(
            invoice_number="INV-PERSIST-101",
            supplier_name="Persistence Test Vendor",
            gstin="07AAAAA0000A1Z4",
            total_amount=150000.0,
            taxable_amount=127118.64,
            cgst=11440.68,
            sgst=11440.68,
            arithmetic_valid=True
        )
    )
    CaseRepository.save_case(db1, case)
    db1.close()
    engine1.dispose()

    # Session 2: Connect via entirely new engine and verify data is retained
    engine2 = create_engine(db_url)
    Session2 = sessionmaker(bind=engine2)
    db2 = Session2()

    retrieved = CaseRepository.get_case(db2, case_id)
    assert retrieved is not None
    assert retrieved.case_id == case_id
    assert retrieved.case_reference == "INV-PERSIST-101"
    assert retrieved.invoice is not None
    assert retrieved.invoice.supplier_name == "Persistence Test Vendor"
    assert retrieved.invoice.total_amount == 150000.0

    db2.close()
    engine2.dispose()
