import pytest
from app.services.validators.gstin_validator import (
    validate_gstin_format,
    calculate_gstin_checksum,
    verify_gstin_checksum,
    extract_state_from_gstin,
    extract_pan_from_gstin,
    get_pan_entity_type,
    diagnose_gstin
)


def test_gstin_checksum_calculation():
    # 1. Apex Courier synthetic sample
    first_14 = "07AAAAA0000A1Z"
    expected = calculate_gstin_checksum(first_14)
    assert expected == "4"
    full_gstin = f"{first_14}{expected}"
    is_valid, reason = validate_gstin_format(full_gstin)
    assert is_valid is True
    assert reason == "FORMAT_VALID"

    # 2. Real-world sample GSTIN (Uttar Pradesh)
    up_gstin = "09AAAUP8175A1ZG"
    assert calculate_gstin_checksum(up_gstin[:14]) == "G"
    is_valid_up, _ = validate_gstin_format(up_gstin)
    assert is_valid_up is True

    # 3. Real-world sample GSTIN (Maharashtra TCS)
    mh_gstin = "27AAACT2727Q1ZW"
    assert calculate_gstin_checksum(mh_gstin[:14]) == "W"
    is_valid_mh, _ = validate_gstin_format(mh_gstin)
    assert is_valid_mh is True


def test_gstin_invalid_checksum():
    first_14 = "07AAAAA0000A1Z"
    expected = calculate_gstin_checksum(first_14)
    tampered_char = "9" if expected != "9" else "8"
    bad_gstin = f"{first_14}{tampered_char}"
    
    is_valid, reason = validate_gstin_format(bad_gstin)
    assert is_valid is False
    assert "Checksum failure" in reason

    is_checksum_ok, exp = verify_gstin_checksum(bad_gstin)
    assert is_checksum_ok is False
    assert exp == expected


def test_gstin_state_code_extraction():
    code, name = extract_state_from_gstin("07AAAAA0000A1Z4")
    assert code == "07"
    assert name == "Delhi"

    code_mh, name_mh = extract_state_from_gstin("27AAACT2727Q1ZW")
    assert code_mh == "27"
    assert name_mh == "Maharashtra"

    # Special jurisdictions
    code_cnt, name_cnt = extract_state_from_gstin("99AAAAA0000A1Z9")
    assert code_cnt == "99"
    assert "Centre Jurisdiction" in name_cnt


def test_gstin_pan_extraction_and_classification():
    gstin = "07AAACA1234F1Z3"
    pan = extract_pan_from_gstin(gstin)
    assert pan == "AAACA1234F"
    
    # 4th letter 'C' indicates Company
    entity_type = get_pan_entity_type(pan)
    assert "Company" in entity_type

    # 4th letter 'P' indicates Individual / Proprietorship
    assert "Individual" in get_pan_entity_type("ABCPE1234P")
    # 4th letter 'F' indicates Firm / LLP
    assert "Partnership" in get_pan_entity_type("ABCFE1234F")


def test_gstin_diagnose_breakdown():
    diag = diagnose_gstin("09AAAUP8175A1ZG")
    assert diag["is_valid"] is True
    assert diag["status"] == "FORMAT_VALID"
    assert diag["state_code"] == "09"
    assert diag["state_name"] == "Uttar Pradesh"
    assert diag["pan"] == "AAAUP8175A"
    assert diag["has_default_z"] is True
    assert diag["checksum_valid"] is True
    assert len(diag["failure_reasons"]) == 0

    # Tampered GSTIN diagnosis
    bad_diag = diagnose_gstin("09AAAUP8175A1Z0")
    assert bad_diag["is_valid"] is False
    assert bad_diag["checksum_valid"] is False
    assert len(bad_diag["failure_reasons"]) > 0


def test_gstin_invalid_lengths_and_patterns():
    # Empty string
    assert validate_gstin_format("")[0] is False
    # Short length
    assert validate_gstin_format("07AAAAA0000A1Z")[0] is False
    # Invalid 14th character (must be 'Z')
    assert validate_gstin_format("07AAAAA0000A1A4")[0] is False
    # Invalid state code 00 or 95
    assert validate_gstin_format("00AAAAA0000A1Z4")[0] is False
    assert validate_gstin_format("95AAAAA0000A1Z4")[0] is False
    # Special characters
    assert validate_gstin_format("07AAAAA0000A!Z4")[0] is False


def test_gstin_truth_invariant():
    """
    INVARIANT: Passing format and checksum validation DOES NOT prove active status.
    Reason string must be explicitly FORMAT_VALID.
    """
    valid_gstin = "07AAAAA0000A1Z4"
    is_valid, reason = validate_gstin_format(valid_gstin)
    assert is_valid is True
    assert reason == "FORMAT_VALID"
    assert "ACTIVE" not in reason
