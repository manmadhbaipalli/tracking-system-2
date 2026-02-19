"""Unit tests for JWT token generation and validation."""

import pytest
from datetime import timedelta
from jose import jwt
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    extract_user_id_from_token,
)
from app.utils.exceptions import TokenExpiredException
from app.config import settings


class TestJWTUtils:
    """Test JWT token utilities."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = 123
        token = create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = 123
        token = create_refresh_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_has_correct_payload(self):
        """Test that access token contains correct user ID."""
        user_id = 456
        token = create_access_token(user_id)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_refresh_token_has_correct_payload(self):
        """Test that refresh token contains correct user ID."""
        user_id = 789
        token = create_refresh_token(user_id)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_verify_valid_token(self):
        """Test verify_token with valid token."""
        user_id = 123
        token = create_access_token(user_id)
        payload = verify_token(token)
        assert payload["sub"] == str(user_id)

    def test_verify_invalid_token(self):
        """Test verify_token with invalid token."""
        with pytest.raises(TokenExpiredException):
            verify_token("invalid.token.here")

    def test_verify_expired_token(self):
        """Test verify_token with expired token."""
        user_id = 123
        # Create an expired token
        expired_token = create_access_token(
            user_id,
            expires_delta=timedelta(minutes=-1)
        )
        with pytest.raises(TokenExpiredException):
            verify_token(expired_token)

    def test_extract_user_id_from_token(self):
        """Test extracting user ID from token."""
        user_id = 999
        token = create_access_token(user_id)
        extracted_id = extract_user_id_from_token(token)
        assert extracted_id == user_id

    def test_extract_user_id_from_expired_token(self):
        """Test that extracting from expired token raises exception."""
        user_id = 123
        expired_token = create_access_token(
            user_id,
            expires_delta=timedelta(minutes=-1)
        )
        with pytest.raises(TokenExpiredException):
            extract_user_id_from_token(expired_token)

    def test_token_includes_expiration(self):
        """Test that token includes expiration claim."""
        user_id = 123
        token = create_access_token(user_id)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert "exp" in payload
        assert payload["exp"] > 0

    def test_custom_expiration_delta(self):
        """Test creating token with custom expiration."""
        user_id = 123
        custom_delta = timedelta(hours=2)
        token = create_access_token(user_id, expires_delta=custom_delta)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert "exp" in payload
