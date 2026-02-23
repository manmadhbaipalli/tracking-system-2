"""Data masking and encryption utilities for SSN/TIN, payment information, and PCI-DSS compliance."""

import re


def mask_ssn_tin(value: str) -> str:
    """Mask SSN/TIN to show only last 4 digits."""
    if not value:
        return ""

    # Remove non-digits
    digits = re.sub(r'\D', '', value)

    if len(digits) == 9:  # SSN
        return f"XXX-XX-{digits[-4:]}"
    elif len(digits) >= 4:  # Other TIN
        return f"{'X' * (len(digits) - 4)}{digits[-4:]}"

    return "XXX-XX-XXXX"


def mask_card_number(value: str) -> str:
    """Mask credit card number to show only last 4 digits."""
    if not value:
        return ""

    digits = re.sub(r'\D', '', value)
    if len(digits) >= 4:
        return f"XXXX-XXXX-XXXX-{digits[-4:]}"

    return "XXXX-XXXX-XXXX-XXXX"