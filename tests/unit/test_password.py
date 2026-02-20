"""Unit tests for password hashing and verification."""

import pytest
from app.utils.password import hash_password, verify_password


class TestPasswordUtility:
    """Test password hashing and verification."""

    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a hash."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > len(password)

    def test_hash_password_different_each_time(self):
        """Test that hash_password creates different hashes (salting)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Different salts

    def test_verify_password_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword123"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that verify_password is case sensitive."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password("testpassword123", hashed) is False

    def test_hash_empty_password(self):
        """Test hashing empty password."""
        password = ""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_long_password(self):
        """Test hashing very long password."""
        password = "x" * 500
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
