import hashlib
from typing import Optional, Tuple, Dict, Any

# Known Vendor Master Bank Registry (Seeded verified historical accounts for AP operations)
# Keyed by standardized GSTIN
KNOWN_VENDOR_BANK_MASTER: Dict[str, Dict[str, Any]] = {
    "07AAAAA0000A1Z5": {
        "legal_name": "Apex Global Logistics Pvt Ltd",
        "trade_name": "Apex Courier",
        "known_bank_account": "98765432109921",
        "known_ifsc": "HDFC0001234",
        "known_bank_name": "HDFC Bank, Okhla Branch",
        "is_msme": True,
        "msme_registration_no": "UDYAM-DL-01-0012345"
    },
    "07AAACH0828A1ZE": {
        "legal_name": "Havells India Limited",
        "trade_name": "Havells Industrial Electricals",
        "known_bank_account": "00030500123456",
        "known_ifsc": "HDFC0000003",
        "known_bank_name": "HDFC Bank, Corporate Branch",
        "is_msme": False,
        "msme_registration_no": None
    },
    "27AABCS1429B1Z1": {
        "legal_name": "Specter Cloud Solutions LLP",
        "trade_name": "Specter Cloud Technologies",
        "known_bank_account": "11223344556677",
        "known_ifsc": "SBIN0004567",
        "known_bank_name": "State Bank of India, Mumbai",
        "is_msme": False,
        "msme_registration_no": None
    },
    "06ABCDE1234F1Z5": {
        "legal_name": "Vertex Solutions Pvt Ltd",
        "trade_name": "Vertex Solutions",
        "known_bank_account": "55667788990011",
        "known_ifsc": "ICIC0000104",
        "known_bank_name": "ICICI Bank, Gurugram Branch",
        "is_msme": True,
        "msme_registration_no": "UDYAM-HR-02-0098765"
    }
}

def hash_bank_account(account_num: Optional[str]) -> Optional[str]:
    """Generates an SHA-256 fingerprint for a bank account number."""
    if not account_num:
        return None
    cleaned = "".join(filter(str.isdigit, str(account_num)))
    if not cleaned:
        return None
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

def check_bank_mutation(
    gstin: Optional[str],
    account_num: Optional[str],
    ifsc: Optional[str]
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Checks if the invoice bank details represent an unauthorized mutation (BEC / altered invoice fraud).
    Returns:
        (mutation_detected: bool, known_account_masked: Optional[str], alert_message: Optional[str])
    """
    if not gstin or not account_num:
        return False, None, None

    cleaned_gstin = gstin.strip().upper()
    cleaned_acc = "".join(filter(str.isdigit, str(account_num)))
    
    vendor = KNOWN_VENDOR_BANK_MASTER.get(cleaned_gstin)
    if not vendor:
        # First-time or unseeded vendor: no historical record to mutate against
        return False, None, None

    known_acc = vendor.get("known_bank_account", "")
    if known_acc and cleaned_acc != known_acc:
        known_masked = f"XXXX-XXXX-{known_acc[-4:]}" if len(known_acc) >= 4 else "****"
        msg = (
            f"CRITICAL BEC ALERT: Remittance account ({account_num[-4:] if len(account_num)>=4 else account_num}) "
            f"differs from verified historical vendor master account ({known_masked}). "
            f"Potential Business Email Compromise or invoice tampering detected."
        )
        return True, known_masked, msg

    return False, None, None

def calculate_beneficiary_match(
    beneficiary_name: Optional[str],
    legal_name: Optional[str],
    trade_name: Optional[str]
) -> float:
    """
    Computes name similarity score (0.0 to 1.0) between extracted bank beneficiary name
    and registered legal/trade names.
    """
    if not beneficiary_name:
        return 1.0  # Beneficiary name not separately stated; default to neutral
    
    b_norm = "".join(c for c in beneficiary_name.lower() if c.isalnum() or c == " ").strip()
    candidates = []
    if legal_name:
        candidates.append("".join(c for c in legal_name.lower() if c.isalnum() or c == " ").strip())
    if trade_name:
        candidates.append("".join(c for c in trade_name.lower() if c.isalnum() or c == " ").strip())
        
    for cand in candidates:
        if not cand:
            continue
        if b_norm in cand or cand in b_norm:
            return 1.0
        # Word overlap
        b_words = set(b_norm.split())
        c_words = set(cand.split())
        if b_words and c_words:
            overlap = len(b_words & c_words) / max(len(b_words), len(c_words))
            if overlap >= 0.5:
                return round(overlap, 2)

    return 0.2
