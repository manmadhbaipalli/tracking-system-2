"""
Claims Service Platform - Field-level Encryption Utilities

Provides encrypt/decrypt functions for PII and payment data with key management.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key from configuration

    Returns:
        bytes: Encryption key for Fernet
    """
    # Use configured key if available
    if settings.ENCRYPTION_KEY and len(settings.ENCRYPTION_KEY) == 32:
        # Derive key using PBKDF2 for additional security
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=settings.FIELD_ENCRYPTION_SALT.encode(),
            iterations=100000,  # Recommended minimum
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
        return key
    else:
        # Generate new key for development (not recommended for production)
        logger.warning("Using generated encryption key - not suitable for production!")
        return Fernet.generate_key()


# Global encryption instance
_fernet_instance = None


def _get_fernet() -> Fernet:
    """
    Get Fernet encryption instance (singleton)

    Returns:
        Fernet: Encryption instance
    """
    global _fernet_instance
    if _fernet_instance is None:
        key = _get_encryption_key()
        _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_field(value: str) -> Optional[str]:
    """
    Encrypt a field value for database storage

    Args:
        value: Plain text value to encrypt

    Returns:
        str: Encrypted value as base64 string, or None if input is None/empty

    Raises:
        Exception: If encryption fails
    """
    if not value:
        return None

    try:
        fernet = _get_fernet()
        encrypted_bytes = fernet.encrypt(value.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        raise Exception("Field encryption failed") from e


def decrypt_field(encrypted_value: str) -> Optional[str]:
    """
    Decrypt a field value from database storage

    Args:
        encrypted_value: Encrypted value as base64 string

    Returns:
        str: Decrypted plain text value, or None if input is None/empty

    Raises:
        Exception: If decryption fails
    """
    if not encrypted_value:
        return None

    try:
        fernet = _get_fernet()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise Exception("Field decryption failed") from e


def encrypt_ssn(ssn: str) -> Optional[str]:
    """
    Encrypt Social Security Number with additional validation

    Args:
        ssn: SSN to encrypt (can include dashes)

    Returns:
        str: Encrypted SSN, or None if invalid

    Raises:
        ValueError: If SSN format is invalid
        Exception: If encryption fails
    """
    if not ssn:
        return None

    # Clean SSN (remove dashes, spaces)
    clean_ssn = ''.join(filter(str.isdigit, ssn))

    # Validate SSN format
    if len(clean_ssn) != 9:
        raise ValueError("SSN must be 9 digits")

    # Check for invalid SSN patterns
    invalid_patterns = [
        "000000000", "111111111", "222222222", "333333333",
        "444444444", "555555555", "666666666", "777777777",
        "888888888", "999999999", "123456789"
    ]

    if clean_ssn in invalid_patterns:
        raise ValueError("Invalid SSN pattern")

    return encrypt_field(clean_ssn)


def encrypt_tin(tin: str) -> Optional[str]:
    """
    Encrypt Tax Identification Number (EIN) with validation

    Args:
        tin: TIN/EIN to encrypt (can include dashes)

    Returns:
        str: Encrypted TIN, or None if invalid

    Raises:
        ValueError: If TIN format is invalid
        Exception: If encryption fails
    """
    if not tin:
        return None

    # Clean TIN (remove dashes, spaces)
    clean_tin = ''.join(filter(str.isdigit, tin))

    # Validate TIN format (9 digits)
    if len(clean_tin) != 9:
        raise ValueError("TIN must be 9 digits")

    return encrypt_field(clean_tin)


def encrypt_payment_info(payment_data: dict) -> dict:
    """
    Encrypt sensitive payment information

    Args:
        payment_data: Dictionary containing payment information

    Returns:
        dict: Dictionary with encrypted sensitive fields

    Raises:
        Exception: If encryption fails
    """
    if not payment_data:
        return payment_data

    encrypted_data = payment_data.copy()
    sensitive_fields = [
        'account_number', 'routing_number', 'card_number',
        'card_cvv', 'bank_account', 'swift_code', 'iban'
    ]

    for field in sensitive_fields:
        if field in encrypted_data and encrypted_data[field]:
            encrypted_data[field] = encrypt_field(str(encrypted_data[field]))

    return encrypted_data


def decrypt_payment_info(encrypted_payment_data: dict) -> dict:
    """
    Decrypt sensitive payment information

    Args:
        encrypted_payment_data: Dictionary containing encrypted payment information

    Returns:
        dict: Dictionary with decrypted sensitive fields

    Raises:
        Exception: If decryption fails
    """
    if not encrypted_payment_data:
        return encrypted_payment_data

    decrypted_data = encrypted_payment_data.copy()
    sensitive_fields = [
        'account_number', 'routing_number', 'card_number',
        'card_cvv', 'bank_account', 'swift_code', 'iban'
    ]

    for field in sensitive_fields:
        if field in decrypted_data and decrypted_data[field]:
            decrypted_data[field] = decrypt_field(decrypted_data[field])

    return decrypted_data


def generate_encryption_key() -> str:
    """
    Generate a new encryption key for configuration

    Returns:
        str: Base64 encoded encryption key
    """
    key = Fernet.generate_key()
    return base64.urlsafe_b64decode(key).decode('utf-8')[:32]


def rotate_encryption_key(old_key: str, new_key: str, encrypted_value: str) -> str:
    """
    Rotate encryption key by decrypting with old key and re-encrypting with new key

    Args:
        old_key: Previous encryption key
        new_key: New encryption key
        encrypted_value: Value encrypted with old key

    Returns:
        str: Value re-encrypted with new key

    Raises:
        Exception: If key rotation fails
    """
    # Create Fernet instances for old and new keys
    old_kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.FIELD_ENCRYPTION_SALT.encode(),
        iterations=100000,
    )
    old_fernet_key = base64.urlsafe_b64encode(old_kdf.derive(old_key.encode()))
    old_fernet = Fernet(old_fernet_key)

    new_kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.FIELD_ENCRYPTION_SALT.encode(),
        iterations=100000,
    )
    new_fernet_key = base64.urlsafe_b64encode(new_kdf.derive(new_key.encode()))
    new_fernet = Fernet(new_fernet_key)

    try:
        # Decrypt with old key
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
        decrypted_bytes = old_fernet.decrypt(encrypted_bytes)

        # Re-encrypt with new key
        new_encrypted_bytes = new_fernet.encrypt(decrypted_bytes)
        return base64.urlsafe_b64encode(new_encrypted_bytes).decode('utf-8')

    except Exception as e:
        logger.error(f"Key rotation failed: {str(e)}")
        raise Exception("Encryption key rotation failed") from e


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be encrypted

    Args:
        value: Value to check

    Returns:
        bool: True if value appears to be encrypted
    """
    if not value:
        return False

    try:
        # Try to base64 decode - encrypted values should be base64 encoded
        decoded = base64.urlsafe_b64decode(value.encode('utf-8'))
        # Fernet tokens have a specific structure and minimum length
        return len(decoded) >= 73  # Minimum Fernet token length
    except Exception:
        return False