"""
Test security utilities and authentication.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.security import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password,
    create_refresh_token
)
from app.core.config import settings
from app.utils.security import mask_ssn, mask_card_number, encrypt_sensitive_data, decrypt_sensitive_data


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)

    # Hash should be different from original password
    assert hashed != password
    assert len(hashed) > 50  # bcrypt hashes are long

    # Verification should work
    assert verify_password(password, hashed) is True

    # Wrong password should fail
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_creation():
    """Test JWT token creation."""
    user_id = "12345678-1234-1234-1234-123456789012"
    token = create_access_token(data={"sub": user_id})

    assert token is not None
    assert isinstance(token, str)

    # Decode token to verify contents
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == user_id
    assert "exp" in payload


def test_jwt_token_expiration():
    """Test JWT token expiration."""
    user_id = "12345678-1234-1234-1234-123456789012"

    # Create token with custom expiration
    token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=1)
    )

    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp)

    # Should expire in approximately 1 minute
    now = datetime.utcnow()
    time_diff = exp_datetime - now
    assert 50 <= time_diff.total_seconds() <= 70  # Allow some tolerance


def test_jwt_token_verification():
    """Test JWT token verification."""
    user_id = "12345678-1234-1234-1234-123456789012"
    token = create_access_token(data={"sub": user_id})

    # Valid token should verify successfully
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == user_id

    # Invalid token should fail
    invalid_payload = verify_token("invalid.token.here")
    assert invalid_payload is None

    # Tampered token should fail
    tampered_token = token[:-5] + "XXXXX"
    tampered_payload = verify_token(tampered_token)
    assert tampered_payload is None


def test_refresh_token_creation():
    """Test refresh token creation."""
    user_id = "12345678-1234-1234-1234-123456789012"
    token = create_refresh_token(data={"sub": user_id})

    assert token is not None
    assert isinstance(token, str)

    # Decode token to verify contents
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_ssn_masking():
    """Test SSN masking utility."""
    # Full SSN
    ssn = "123-45-6789"
    masked = mask_ssn(ssn)
    assert masked == "XXX-XX-6789"

    # SSN without dashes
    ssn = "123456789"
    masked = mask_ssn(ssn)
    assert masked == "XXXXX6789"

    # Invalid SSN should return as-is or empty
    invalid_ssn = "12345"
    masked = mask_ssn(invalid_ssn)
    assert len(masked) <= len(invalid_ssn)

    # None should return None
    assert mask_ssn(None) is None


def test_card_number_masking():
    """Test credit card number masking."""
    # Standard credit card
    card = "4111111111111111"
    masked = mask_card_number(card)
    assert masked == "XXXXXXXXXXXX1111"

    # Card with spaces
    card = "4111 1111 1111 1111"
    masked = mask_card_number(card)
    assert "1111" in masked
    assert "4111" not in masked

    # Invalid card should return safely
    invalid_card = "123"
    masked = mask_card_number(invalid_card)
    assert len(masked) <= len(invalid_card)

    # None should return None
    assert mask_card_number(None) is None


def test_encryption_utilities():
    """Test data encryption and decryption utilities."""
    # Test with simple string
    original_data = "sensitive information"
    encrypted = encrypt_sensitive_data(original_data)

    # Encrypted should be different from original
    assert encrypted != original_data
    assert len(encrypted) > len(original_data)

    # Decryption should restore original
    decrypted = decrypt_sensitive_data(encrypted)
    assert decrypted == original_data

    # Test with None
    assert encrypt_sensitive_data(None) is None
    assert decrypt_sensitive_data(None) is None

    # Test with empty string
    encrypted_empty = encrypt_sensitive_data("")
    decrypted_empty = decrypt_sensitive_data(encrypted_empty)
    assert decrypted_empty == ""