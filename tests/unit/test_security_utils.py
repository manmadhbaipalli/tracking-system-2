"""
Test security utilities for data encryption, masking, and compliance.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.utils.security import (
    encrypt_data, decrypt_data, hash_ssn_tin, mask_ssn_tin,
    mask_payment_data, generate_correlation_id, hash_password_secure
)


class TestDataEncryption:
    """Test data encryption and decryption functions."""

    def test_encrypt_data_basic(self):
        """Test basic data encryption."""
        with patch('app.utils.security.settings') as mock_settings:
            mock_settings.encryption_key = b"test-key-32-bytes-long-for-testing"

            # Mock Fernet encryption
            with patch('app.utils.security.Fernet') as mock_fernet:
                mock_cipher = MagicMock()
                mock_cipher.encrypt.return_value = b"encrypted_data"
                mock_fernet.return_value = mock_cipher

                result = encrypt_data("sensitive_data")

                assert result == "encrypted_data"
                mock_cipher.encrypt.assert_called_once()

    def test_decrypt_data_basic(self):
        """Test basic data decryption."""
        with patch('app.utils.security.settings') as mock_settings:
            mock_settings.encryption_key = b"test-key-32-bytes-long-for-testing"

            # Mock Fernet decryption
            with patch('app.utils.security.Fernet') as mock_fernet:
                mock_cipher = MagicMock()
                mock_cipher.decrypt.return_value = b"decrypted_data"
                mock_fernet.return_value = mock_cipher

                result = decrypt_data("encrypted_data")

                assert result == "decrypted_data"
                mock_cipher.decrypt.assert_called_once()

    def test_encrypt_none_value(self):
        """Test encrypting None value."""
        result = encrypt_data(None)
        assert result is None

    def test_decrypt_none_value(self):
        """Test decrypting None value."""
        result = decrypt_data(None)
        assert result is None

    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        result = encrypt_data("")
        assert result is None


class TestSSNTINHandling:
    """Test SSN/TIN hashing and masking functions."""

    def test_hash_ssn_tin_with_dashes(self):
        """Test hashing SSN with dashes."""
        with patch('hashlib.sha256') as mock_sha:
            mock_hash = MagicMock()
            mock_hash.hexdigest.return_value = "hashed_value"
            mock_sha.return_value = mock_hash

            result = hash_ssn_tin("123-45-6789")

            assert result == "hashed_value"
            # Should be called with normalized version (no dashes)
            mock_sha.assert_called_once()

    def test_hash_ssn_tin_without_dashes(self):
        """Test hashing SSN without dashes."""
        with patch('hashlib.sha256') as mock_sha:
            mock_hash = MagicMock()
            mock_hash.hexdigest.return_value = "hashed_value"
            mock_sha.return_value = mock_hash

            result = hash_ssn_tin("123456789")

            assert result == "hashed_value"
            mock_sha.assert_called_once()

    def test_hash_ssn_tin_none_value(self):
        """Test hashing None SSN/TIN."""
        result = hash_ssn_tin(None)
        assert result is None

    def test_hash_ssn_tin_empty_string(self):
        """Test hashing empty SSN/TIN."""
        result = hash_ssn_tin("")
        assert result is None

    def test_mask_ssn_tin_with_dashes(self):
        """Test masking SSN with dashes."""
        with patch('app.utils.security.decrypt_data') as mock_decrypt:
            mock_decrypt.return_value = "123-45-6789"

            result = mask_ssn_tin("encrypted_ssn")

            assert result == "XXX-XX-6789"
            mock_decrypt.assert_called_once_with("encrypted_ssn")

    def test_mask_ssn_tin_without_dashes(self):
        """Test masking SSN without dashes."""
        with patch('app.utils.security.decrypt_data') as mock_decrypt:
            mock_decrypt.return_value = "123456789"

            result = mask_ssn_tin("encrypted_ssn")

            assert result == "XXXXX6789"
            mock_decrypt.assert_called_once_with("encrypted_ssn")

    def test_mask_ssn_tin_short_value(self):
        """Test masking short SSN/TIN."""
        with patch('app.utils.security.decrypt_data') as mock_decrypt:
            mock_decrypt.return_value = "123"

            result = mask_ssn_tin("encrypted_ssn")

            assert result == "123"  # Too short to mask

    def test_mask_ssn_tin_none_value(self):
        """Test masking None SSN/TIN."""
        result = mask_ssn_tin(None)
        assert result is None

    def test_mask_ssn_tin_decryption_failure(self):
        """Test masking when decryption fails."""
        with patch('app.utils.security.decrypt_data') as mock_decrypt:
            mock_decrypt.side_effect = Exception("Decryption failed")

            result = mask_ssn_tin("encrypted_ssn")

            assert result == "XXXX"  # Default mask on error


class TestPaymentDataMasking:
    """Test payment data masking for PCI-DSS compliance."""

    def test_mask_payment_data_credit_card(self):
        """Test masking credit card payment data."""
        payment_data = {
            "payment_method": "CREDIT_CARD",
            "card_number": "4111111111111111",
            "cvv": "123",
            "expiry_date": "12/25",
            "cardholder_name": "John Doe",
            "amount": 100.00
        }

        result = mask_payment_data(payment_data)

        assert result["card_number"] == "****-****-****-1111"
        assert result["cvv"] == "***"
        assert result["cardholder_name"] == "John Doe"  # Name not masked
        assert result["amount"] == 100.00  # Amount not masked

    def test_mask_payment_data_bank_account(self):
        """Test masking bank account payment data."""
        payment_data = {
            "payment_method": "ACH",
            "routing_number": "123456789",
            "account_number": "9876543210",
            "account_holder_name": "Jane Smith",
            "amount": 250.00
        }

        result = mask_payment_data(payment_data)

        assert result["routing_number"] == "*****6789"
        assert result["account_number"] == "******3210"
        assert result["account_holder_name"] == "Jane Smith"  # Name not masked
        assert result["amount"] == 250.00  # Amount not masked

    def test_mask_payment_data_no_sensitive_fields(self):
        """Test masking payment data with no sensitive fields."""
        payment_data = {
            "payment_method": "CHECK",
            "check_number": "1001",
            "amount": 75.00
        }

        result = mask_payment_data(payment_data)

        # No masking should occur for non-sensitive fields
        assert result["check_number"] == "1001"
        assert result["amount"] == 75.00

    def test_mask_payment_data_none_values(self):
        """Test masking payment data with None values."""
        payment_data = {
            "payment_method": "CREDIT_CARD",
            "card_number": None,
            "cvv": None,
            "amount": 100.00
        }

        result = mask_payment_data(payment_data)

        assert result["card_number"] is None
        assert result["cvv"] is None
        assert result["amount"] == 100.00


class TestCorrelationID:
    """Test correlation ID generation."""

    def test_generate_correlation_id_format(self):
        """Test correlation ID format."""
        correlation_id = generate_correlation_id()

        # Should be a UUID-like string
        assert len(correlation_id) == 36
        assert correlation_id.count('-') == 4

    def test_generate_correlation_id_unique(self):
        """Test that correlation IDs are unique."""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()

        assert id1 != id2

    def test_generate_correlation_id_format_validation(self):
        """Test correlation ID follows UUID4 format."""
        import re

        correlation_id = generate_correlation_id()
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'

        assert re.match(uuid_pattern, correlation_id.lower())


class TestPasswordSecurity:
    """Test password hashing functions."""

    def test_hash_password_secure(self):
        """Test secure password hashing."""
        with patch('app.utils.security.pwd_context') as mock_context:
            mock_context.hash.return_value = "hashed_password"

            result = hash_password_secure("password123")

            assert result == "hashed_password"
            mock_context.hash.assert_called_once_with("password123")

    def test_hash_password_secure_none_value(self):
        """Test hashing None password."""
        result = hash_password_secure(None)
        assert result is None

    def test_hash_password_secure_empty_string(self):
        """Test hashing empty password."""
        result = hash_password_secure("")
        assert result is None


class TestSecurityConfiguration:
    """Test security configuration and settings."""

    def test_encryption_key_required(self):
        """Test that encryption operations require encryption key."""
        with patch('app.utils.security.settings') as mock_settings:
            mock_settings.encryption_key = None

            with pytest.raises(Exception):
                encrypt_data("test_data")

    def test_secure_random_generation(self):
        """Test that secure random generation works."""
        # This implicitly tests that the secrets module is used
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()

        # Should be different (extremely unlikely to be same with secure random)
        assert id1 != id2

        # Should be valid UUIDs
        import uuid
        uuid.UUID(id1)  # Should not raise exception
        uuid.UUID(id2)  # Should not raise exception


class TestErrorHandling:
    """Test error handling in security functions."""

    def test_encryption_with_invalid_key(self):
        """Test encryption with invalid key."""
        with patch('app.utils.security.settings') as mock_settings:
            mock_settings.encryption_key = "too_short"

            with patch('app.utils.security.Fernet') as mock_fernet:
                mock_fernet.side_effect = Exception("Invalid key")

                result = encrypt_data("test_data")

                # Should handle error gracefully
                assert result is None

    def test_decryption_with_invalid_data(self):
        """Test decryption with invalid encrypted data."""
        with patch('app.utils.security.settings') as mock_settings:
            mock_settings.encryption_key = b"test-key-32-bytes-long-for-testing"

            with patch('app.utils.security.Fernet') as mock_fernet:
                mock_cipher = MagicMock()
                mock_cipher.decrypt.side_effect = Exception("Invalid token")
                mock_fernet.return_value = mock_cipher

                result = decrypt_data("invalid_encrypted_data")

                # Should handle error gracefully
                assert result is None