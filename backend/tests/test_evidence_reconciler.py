import pytest
from backend.app.services.reconciler.evidence_reconciler import EvidenceReconciler, normalize_business_name
from backend.app.schemas.invoice import InvoiceClaim
from backend.app.schemas.evidence import EvidenceItem
from backend.app.schemas.enums import CheckStatus, SourceMode

@pytest.fixture
def reconciler():
    return EvidenceReconciler()

def test_normalize_business_name():
    # Suffix removal and lowercase
    assert normalize_business_name("Acme Logistics Pvt. Ltd.") == "acme logistics"
    assert normalize_business_name("Acme & Co. Limited") == "acme and"
    assert normalize_business_name("Globex Technologies India Private Limited") == "globex"
    assert normalize_business_name("Apex Courier") == "apex courier"

def test_reconcile_exact_name_match(reconciler):
    invoice = InvoiceClaim(
        invoice_number="INV-001",
        supplier_name="Apex Global Logistics",
        gstin="07AAAAA0000A1Z5",
        total_amount=1000.0
    )
    evidence = [
        EvidenceItem(
            evidence_id="ev_01",
            source_url="https://gst.gov.in",
            source_name="GST Portal",
            claim_supported="Legal Identity",
            raw_excerpt="Registration Active",
            facts={"legal_name": "Apex Global Logistics Private Limited", "status": "Active"},
            is_authoritative=True
        )
    ]
    checks = reconciler.reconcile(invoice, evidence)
    name_chk = next(c for c in checks if c.check_id == "chk_name_match")
    assert name_chk.status == CheckStatus.MATCH

def test_reconcile_trade_alias_possible_match(reconciler):
    # Invoice uses trade name; registry confirms legal name with registered trade alias
    invoice = InvoiceClaim(
        invoice_number="INV-002",
        supplier_name="Apex Courier",
        gstin="07AAAAA0000A1Z5",
        total_amount=1000.0
    )
    evidence = [
        EvidenceItem(
            evidence_id="ev_01",
            source_url="https://gst.gov.in",
            source_name="GST Portal",
            claim_supported="Legal Identity",
            raw_excerpt="Registration Active",
            facts={
                "legal_name": "Apex Global Logistics Private Limited",
                "trade_name": "Apex Courier",
                "status": "Active"
            },
            is_authoritative=True
        )
    ]
    checks = reconciler.reconcile(invoice, evidence)
    name_chk = next(c for c in checks if c.check_id == "chk_legal_name_discrepancy")
    assert name_chk.status == CheckStatus.POSSIBLE_MATCH
    assert name_chk.reason_code == "LEGAL_NAME_MISMATCH"

def test_never_match_merely_because_trade_name_field_exists(reconciler):
    # Registry has a trade_name field, but it has a completely conflicting name!
    invoice = InvoiceClaim(
        invoice_number="INV-003",
        supplier_name="Specter Cloud Technologies",
        gstin="07AAAAA0000A1Z5",
        total_amount=1000.0
    )
    evidence = [
        EvidenceItem(
            evidence_id="ev_01",
            source_url="https://gst.gov.in",
            source_name="GST Portal",
            claim_supported="Legal Identity",
            raw_excerpt="Registration Active",
            facts={
                "legal_name": "Apex Global Logistics Private Limited",
                "trade_name": "Apex Courier",
                "status": "Active"
            },
            is_authoritative=True
        )
    ]
    checks = reconciler.reconcile(invoice, evidence)
    name_chk = next(c for c in checks if c.check_id == "chk_name_mismatch")
    assert name_chk.status == CheckStatus.MISMATCH
    assert name_chk.reason_code == "CRITICAL_NAME_MISMATCH"

def test_reconcile_missing_evidence(reconciler):
    # When registry evidence is unavailable, flag as UNAVAILABLE, not as fraud
    invoice = InvoiceClaim(
        invoice_number="INV-004",
        supplier_name="Unknown Unregistered Vendor",
        gstin=None,
        total_amount=500.0
    )
    evidence = []
    checks = reconciler.reconcile(invoice, evidence)
    name_chk = next(c for c in checks if c.check_id == "chk_name_unknown")
    assert name_chk.status == CheckStatus.UNAVAILABLE
    assert name_chk.reason_code == "EVIDENCE_INSUFFICIENT"
