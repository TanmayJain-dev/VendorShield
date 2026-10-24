"""
GSTIN generation and checksum helper tools.
Used for creating verified, checksum-valid synthetic GSTINs for testing and demo fixtures.
"""

from typing import Optional
from .gstin_validator import GSTIN_CHARS, calculate_gstin_checksum

def compute_check_char(first_14: str) -> str:
    """Computes the 15th Modulo-36 check character for a 14-character GSTIN prefix."""
    return calculate_gstin_checksum(first_14)

def make_gstin(state_code: str, pan: str, entity_number: str = "1") -> str:
    """
    Constructs a checksum-valid 15-character GSTIN given state code, PAN, and entity number.
    Formula: State (2) + PAN (10) + Entity (1) + 'Z' (1) + Checksum (1)
    """
    clean_state = state_code.strip()
    if len(clean_state) == 1:
        clean_state = f"0{clean_state}"
    clean_pan = pan.strip().upper()
    clean_entity = entity_number.strip().upper()[:1]
    
    first_14 = f"{clean_state}{clean_pan}{clean_entity}Z"
    check_char = compute_check_char(first_14)
    return f"{first_14}{check_char}"
