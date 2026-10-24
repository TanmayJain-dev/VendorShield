import re
from typing import Tuple

GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

def validate_gstin_format(gstin: str) -> Tuple[bool, str]:
    """
    Validates Indian 15-character Goods and Services Tax Identification Number (GSTIN).
    
    Returns:
        (is_valid: bool, reason: str)
    
    IMPORTANT: Format and checksum validity proves structural correctness only.
    It DOES NOT prove that the business is active, registered, or legitimate.
    """
    if not gstin:
        return False, "GSTIN is missing or empty"
    
    cleaned = gstin.strip().upper()
    if len(cleaned) != 15:
        return False, f"Invalid length: expected 15 characters, got {len(cleaned)}"
    
    if not GSTIN_REGEX.match(cleaned):
        return False, "GSTIN does not match official format regex (e.g. 07AAAAA0000A1Z5)"
    
    # State code validation: 01 to 38 plus 97, 99
    state_code = int(cleaned[:2])
    valid_state_codes = set(list(range(1, 39)) + [97, 99])
    if state_code not in valid_state_codes:
        return False, f"Invalid state code '{cleaned[:2]}'"
    
    # Checksum verification (Modulo 36 algorithm)
    try:
        is_checksum_valid, expected_char = verify_gstin_checksum(cleaned)
        if not is_checksum_valid:
            return False, f"Checksum failure: 15th character '{cleaned[14]}' does not match expected '{expected_char}'"
    except Exception as e:
        return False, f"Checksum calculation error: {str(e)}"
    
    return True, "FORMAT_VALID"

def calculate_gstin_checksum(first_14_chars: str) -> str:
    """Calculates the 15th character checksum for first 14 chars using GSTN Modulo 36."""
    chars = GSTIN_CHARS
    total = 0
    for i, c in enumerate(first_14_chars[:14]):
        code_point = chars.index(c)
        factor = 1 if (i % 2 == 0) else 2
        product = code_point * factor
        total += (product // 36) + (product % 36)
    
    remainder = total % 36
    check_code = (36 - remainder) % 36
    return chars[check_code]

def verify_gstin_checksum(gstin: str) -> Tuple[bool, str]:
    """Verifies the 15th character checksum."""
    if len(gstin) != 15:
        return False, ""
    expected = calculate_gstin_checksum(gstin[:14])
    return gstin[14] == expected, expected
