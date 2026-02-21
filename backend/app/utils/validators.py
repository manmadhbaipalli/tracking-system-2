"""
Claims Service Platform - Input Validation Utilities

Validates SSN/TIN formats, payment amounts, policy numbers, and other business constraints.
"""

import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional, Union, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error exception"""
    pass


def validate_ssn(ssn: str) -> bool:
    """
    Validate Social Security Number format

    Args:
        ssn: SSN to validate (with or without dashes)

    Returns:
        bool: True if valid SSN format

    Raises:
        ValidationError: If SSN is invalid
    """
    if not ssn:
        raise ValidationError("SSN is required")

    # Remove dashes and spaces
    clean_ssn = ''.join(filter(str.isdigit, ssn))

    # Check length
    if len(clean_ssn) != 9:
        raise ValidationError("SSN must be 9 digits")

    # Check for invalid patterns
    invalid_patterns = [
        "000000000", "111111111", "222222222", "333333333",
        "444444444", "555555555", "666666666", "777777777",
        "888888888", "999999999", "123456789"
    ]

    if clean_ssn in invalid_patterns:
        raise ValidationError("Invalid SSN pattern")

    # Check area number (first 3 digits)
    area_number = clean_ssn[:3]
    if area_number in ["000", "666"] or area_number.startswith("9"):
        raise ValidationError("Invalid SSN area number")

    return True


def validate_tin(tin: str) -> bool:
    """
    Validate Tax Identification Number (EIN) format

    Args:
        tin: TIN/EIN to validate

    Returns:
        bool: True if valid TIN format

    Raises:
        ValidationError: If TIN is invalid
    """
    if not tin:
        raise ValidationError("TIN is required")

    # Remove dashes and spaces
    clean_tin = ''.join(filter(str.isdigit, tin))

    # Check length
    if len(clean_tin) != 9:
        raise ValidationError("TIN must be 9 digits")

    # Check for invalid patterns (all zeros, all same digit)
    if clean_tin == "000000000" or len(set(clean_tin)) == 1:
        raise ValidationError("Invalid TIN pattern")

    return True


def validate_policy_number(policy_number: str) -> bool:
    """
    Validate policy number format

    Args:
        policy_number: Policy number to validate

    Returns:
        bool: True if valid policy number

    Raises:
        ValidationError: If policy number is invalid
    """
    if not policy_number:
        raise ValidationError("Policy number is required")

    # Policy number should be alphanumeric, 8-20 characters
    if not re.match(r'^[A-Za-z0-9\-]+$', policy_number):
        raise ValidationError("Policy number can only contain letters, numbers, and hyphens")

    if len(policy_number) < 8 or len(policy_number) > 20:
        raise ValidationError("Policy number must be between 8 and 20 characters")

    return True


def validate_claim_number(claim_number: str) -> bool:
    """
    Validate claim number format

    Args:
        claim_number: Claim number to validate

    Returns:
        bool: True if valid claim number

    Raises:
        ValidationError: If claim number is invalid
    """
    if not claim_number:
        raise ValidationError("Claim number is required")

    # Claim number should be alphanumeric, 8-25 characters
    if not re.match(r'^[A-Za-z0-9\-]+$', claim_number):
        raise ValidationError("Claim number can only contain letters, numbers, and hyphens")

    if len(claim_number) < 8 or len(claim_number) > 25:
        raise ValidationError("Claim number must be between 8 and 25 characters")

    return True


def validate_payment_amount(amount: Union[str, float, Decimal]) -> bool:
    """
    Validate payment amount

    Args:
        amount: Payment amount to validate

    Returns:
        bool: True if valid amount

    Raises:
        ValidationError: If amount is invalid
    """
    if amount is None:
        raise ValidationError("Payment amount is required")

    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        raise ValidationError("Invalid payment amount format")

    # Allow negative amounts for reversals, but check reasonable limits
    if decimal_amount < Decimal('-999999999.99') or decimal_amount > Decimal('999999999.99'):
        raise ValidationError("Payment amount must be between -$999,999,999.99 and $999,999,999.99")

    # Check decimal places (max 2)
    if decimal_amount.as_tuple().exponent < -2:
        raise ValidationError("Payment amount cannot have more than 2 decimal places")

    return True


def validate_email(email: str) -> bool:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid email

    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email is required")

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")

    if len(email) > 254:
        raise ValidationError("Email address too long")

    return True


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format

    Args:
        phone: Phone number to validate

    Returns:
        bool: True if valid phone number

    Raises:
        ValidationError: If phone number is invalid
    """
    if not phone:
        raise ValidationError("Phone number is required")

    # Remove all non-digits
    clean_phone = ''.join(filter(str.isdigit, phone))

    # Check for US phone number (10 digits) or international (7-15 digits)
    if len(clean_phone) < 7 or len(clean_phone) > 15:
        raise ValidationError("Phone number must be between 7 and 15 digits")

    # For US numbers, validate area code and exchange
    if len(clean_phone) == 10:
        area_code = clean_phone[:3]
        exchange = clean_phone[3:6]

        if area_code[0] in ['0', '1']:
            raise ValidationError("Invalid area code")

        if exchange[0] in ['0', '1']:
            raise ValidationError("Invalid exchange code")

    return True


def validate_zip_code(zip_code: str) -> bool:
    """
    Validate ZIP code format

    Args:
        zip_code: ZIP code to validate

    Returns:
        bool: True if valid ZIP code

    Raises:
        ValidationError: If ZIP code is invalid
    """
    if not zip_code:
        raise ValidationError("ZIP code is required")

    # US ZIP code formats: 12345 or 12345-6789
    if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
        raise ValidationError("Invalid ZIP code format")

    return True


def validate_state_code(state_code: str) -> bool:
    """
    Validate US state code

    Args:
        state_code: 2-letter state code to validate

    Returns:
        bool: True if valid state code

    Raises:
        ValidationError: If state code is invalid
    """
    if not state_code:
        raise ValidationError("State code is required")

    valid_states = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        'DC', 'PR', 'VI', 'AS', 'GU', 'MP'
    }

    if state_code.upper() not in valid_states:
        raise ValidationError("Invalid state code")

    return True


def validate_vin(vin: str) -> bool:
    """
    Validate Vehicle Identification Number

    Args:
        vin: VIN to validate

    Returns:
        bool: True if valid VIN

    Raises:
        ValidationError: If VIN is invalid
    """
    if not vin:
        raise ValidationError("VIN is required")

    # VIN should be 17 characters, alphanumeric (excluding I, O, Q)
    if len(vin) != 17:
        raise ValidationError("VIN must be exactly 17 characters")

    if not re.match(r'^[ABCDEFGHJKLMNPRSTUVWXYZ0-9]+$', vin.upper()):
        raise ValidationError("VIN contains invalid characters (I, O, Q not allowed)")

    return True


def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Validate date range

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        bool: True if valid date range

    Raises:
        ValidationError: If date range is invalid
    """
    if not start_date or not end_date:
        raise ValidationError("Both start and end dates are required")

    if start_date > end_date:
        raise ValidationError("Start date cannot be after end date")

    # Check for reasonable date range (not more than 100 years)
    if (end_date - start_date).days > 36500:  # ~100 years
        raise ValidationError("Date range too large")

    return True


def validate_routing_number(routing_number: str) -> bool:
    """
    Validate bank routing number (ABA number)

    Args:
        routing_number: 9-digit routing number

    Returns:
        bool: True if valid routing number

    Raises:
        ValidationError: If routing number is invalid
    """
    if not routing_number:
        raise ValidationError("Routing number is required")

    # Remove any non-digits
    clean_routing = ''.join(filter(str.isdigit, routing_number))

    if len(clean_routing) != 9:
        raise ValidationError("Routing number must be 9 digits")

    # Check routing number checksum using ABA algorithm
    checksum = (
        3 * (int(clean_routing[0]) + int(clean_routing[3]) + int(clean_routing[6])) +
        7 * (int(clean_routing[1]) + int(clean_routing[4]) + int(clean_routing[7])) +
        1 * (int(clean_routing[2]) + int(clean_routing[5]) + int(clean_routing[8]))
    )

    if checksum % 10 != 0:
        raise ValidationError("Invalid routing number checksum")

    return True


def validate_account_number(account_number: str) -> bool:
    """
    Validate bank account number

    Args:
        account_number: Bank account number

    Returns:
        bool: True if valid account number

    Raises:
        ValidationError: If account number is invalid
    """
    if not account_number:
        raise ValidationError("Account number is required")

    # Account number should be numeric, 4-20 digits
    clean_account = ''.join(filter(str.isdigit, account_number))

    if len(clean_account) < 4 or len(clean_account) > 20:
        raise ValidationError("Account number must be between 4 and 20 digits")

    return True


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        bool: True if password meets requirements

    Raises:
        ValidationError: If password is weak
    """
    if not password:
        raise ValidationError("Password is required")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")

    if len(password) > 128:
        raise ValidationError("Password must be less than 128 characters")

    # Check for required character types
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    if not (has_lower and has_upper and has_digit and has_special):
        raise ValidationError(
            "Password must contain at least one lowercase letter, "
            "one uppercase letter, one digit, and one special character"
        )

    return True


def sanitize_input(input_str: str, max_length: int = None) -> str:
    """
    Sanitize input string by removing potentially dangerous characters

    Args:
        input_str: String to sanitize
        max_length: Maximum allowed length

    Returns:
        str: Sanitized string
    """
    if not input_str:
        return ""

    # Remove control characters and potentially dangerous chars
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)

    # Remove SQL injection patterns (basic)
    dangerous_patterns = [
        r'(\s*(union|select|insert|update|delete|drop|create|alter)\s+)',
        r'(\s*--)',
        r'(\s*/\*)',
        r'(\s*;\s*)',
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, ' ', sanitized, flags=re.IGNORECASE)

    # Trim whitespace
    sanitized = sanitized.strip()

    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_json_structure(data: Dict[Any, Any], required_fields: List[str]) -> bool:
    """
    Validate that JSON data contains required fields

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        bool: True if all required fields present

    Raises:
        ValidationError: If required fields are missing
    """
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    return True