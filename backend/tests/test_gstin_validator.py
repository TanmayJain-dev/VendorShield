import pytest
from app.services.validators.gstin_validator import (
    validate_gstin_format,
    calculate_gstin_checksum,
    verify_gstin_checksum
)

def test_gstin_checksum_calculation():
    # Calculate checksum for first 14 chars of standard format
    first_14 = "07AAAAA0000A1Z"
    expected = calculate_gstin_checksum(first_14)
    assert len(expected) == 1
    
    # Full valid GSTIN with verified checksum
    full_gstin = f"{first_14}{expected}"
    is_valid, reason = validate_gstin_format(full_gstin)
    assert is_valid is True
    assert reason == "FORMAT_VALID"

def test_gstin_invalid_checksum():
    first_14 = "07AAAAA0000A1Z"
    expected = calculate_gstin_checksum(first_14)
    # Intentionally alter 15th char
    tampered_char = "9" if expected != "9" else "8"
    bad_gstin = f"{first_14}{tampered_char}"
    
    is_valid, reason = validate_gstin_format(bad_gstin)
    assert is_valid is False
    assert "Checksum failure" in reason

def test_gstin_invalid_lengths_and_patterns():
    # Empty
    assert validate_gstin_format("")[0] is False
    # Too short
    assert validate_gstin_format("07AAAAA0000A1Z")[0] is False
    # Invalid state code (999)
    assert validate_gstin_format("999AAAA0000A1Z5")[0] is False
    # Invalid characters
    assert validate_gstin_format("07AAAAA0000A!Z5")[0] is False
