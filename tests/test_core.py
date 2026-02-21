"""Tests for core utilities."""
import pytest
from datetime import datetime, timedelta

from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestSecurity:
    """Test cases for security utilities."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password
        # Hash should be a bcrypt hash
        assert hashed.startswith("$2b$")
        # Should be able to verify the password
        assert verify_password(password, hashed) is True
        # Wrong password should not verify
        assert verify_password("wrongpassword", hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # Both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_jwt_token_creation_and_decoding(self):
        """Test JWT token creation and decoding."""
        subject = "test@example.com"
        token = create_access_token(subject=subject)

        # Token should be a string
        assert isinstance(token, str)
        # Should contain JWT structure (header.payload.signature)
        assert token.count(".") == 2

        # Decode token
        payload = decode_token(token)
        assert payload["sub"] == subject
        assert "exp" in payload
        # Expiration should be in the future
        exp_timestamp = payload["exp"]
        assert exp_timestamp > datetime.utcnow().timestamp()

    def test_jwt_token_with_custom_expiry(self):
        """Test JWT token creation with custom expiry."""
        subject = "test@example.com"
        expires_delta = timedelta(minutes=60)
        token = create_access_token(subject=subject, expires_delta=expires_delta)

        payload = decode_token(token)
        assert payload["sub"] == subject

        # Check that expiry is approximately 60 minutes from now
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + expires_delta
        # Allow 5 second tolerance
        assert abs(exp_timestamp - expected_exp.timestamp()) < 5

    def test_invalid_jwt_token_decoding(self):
        """Test decoding invalid JWT tokens."""
        # Completely invalid token
        invalid_payload = decode_token("invalid.token.here")
        assert invalid_payload == {}

        # Malformed token
        malformed_payload = decode_token("malformed-token")
        assert malformed_payload == {}

        # Empty token
        empty_payload = decode_token("")
        assert empty_payload == {}

    def test_expired_jwt_token(self):
        """Test handling of expired JWT tokens."""
        subject = "test@example.com"
        # Create token that expired 1 minute ago
        expired_delta = timedelta(minutes=-1)
        expired_token = create_access_token(subject=subject, expires_delta=expired_delta)

        # Decoding expired token should return empty dict
        payload = decode_token(expired_token)
        assert payload == {}

    def test_jwt_token_subject_types(self):
        """Test JWT token creation with different subject types."""
        # String subject
        string_subject = "test@example.com"
        token1 = create_access_token(subject=string_subject)
        payload1 = decode_token(token1)
        assert payload1["sub"] == string_subject

        # Integer subject (converted to string)
        int_subject = 12345
        token2 = create_access_token(subject=int_subject)
        payload2 = decode_token(token2)
        assert payload2["sub"] == "12345"

        # UUID subject (converted to string)
        import uuid
        uuid_subject = uuid.uuid4()
        token3 = create_access_token(subject=uuid_subject)
        payload3 = decode_token(token3)
        assert payload3["sub"] == str(uuid_subject)