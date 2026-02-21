"""
Claims Service Platform - Encryption Utilities Tests
"""

import pytest
from app.utils.encryption import (
    encrypt_field, decrypt_field, encrypt_ssn, encrypt_tin,
    encrypt_payment_info, decrypt_payment_info, is_encrypted
)


class TestEncryptionUtils:
    """Test encryption utility functions"""

    def test_encrypt_decrypt_field(self):
        """Test basic field encryption and decryption"""
        original_value = "sensitive data"
        encrypted = encrypt_field(original_value)
        decrypted = decrypt_field(encrypted)

        assert encrypted != original_value
        assert decrypted == original_value
        assert is_encrypted(encrypted)

    def test_encrypt_decrypt_empty_values(self):
        """Test encryption with empty/None values"""
        assert encrypt_field(None) is None
        assert encrypt_field("") is None
        assert decrypt_field(None) is None
        assert decrypt_field("") is None

    def test_encrypt_ssn_valid(self):
        """Test SSN encryption with valid inputs"""
        valid_ssns = [
            "123456789",
            "123-45-6789",
            "123 45 6789"
        ]

        for ssn in valid_ssns:
            encrypted = encrypt_ssn(ssn)
            assert encrypted is not None
            assert is_encrypted(encrypted)
            decrypted = decrypt_field(encrypted)
            assert decrypted == "123456789"  # Should be normalized

    def test_encrypt_ssn_invalid(self):
        """Test SSN encryption with invalid inputs"""
        invalid_ssns = [
            "12345678",      # Too short
            "1234567890",    # Too long
            "000000000",     # Invalid pattern
            "111111111",     # Invalid pattern
            "123456789a",    # Contains letters
            ""
        ]

        for ssn in invalid_ssns:
            if ssn == "":
                assert encrypt_ssn(ssn) is None
            else:
                with pytest.raises(ValueError):
                    encrypt_ssn(ssn)

    def test_encrypt_tin_valid(self):
        """Test TIN/EIN encryption with valid inputs"""
        valid_tins = [
            "987654321",
            "98-7654321",
            "98 7654321"
        ]

        for tin in valid_tins:
            encrypted = encrypt_tin(tin)
            assert encrypted is not None
            assert is_encrypted(encrypted)
            decrypted = decrypt_field(encrypted)
            assert decrypted == "987654321"  # Should be normalized

    def test_encrypt_tin_invalid(self):
        """Test TIN encryption with invalid inputs"""
        invalid_tins = [
            "12345678",      # Too short
            "1234567890",    # Too long
            "12345678a",     # Contains letters
            ""
        ]

        for tin in invalid_tins:
            if tin == "":
                assert encrypt_tin(tin) is None
            else:
                with pytest.raises(ValueError):
                    encrypt_tin(tin)

    def test_encrypt_payment_info(self):
        """Test payment information encryption"""
        payment_data = {
            "account_number": "1234567890",
            "routing_number": "987654321",
            "card_number": "4111111111111111",
            "card_cvv": "123",
            "non_sensitive_field": "public data"
        }

        encrypted_data = encrypt_payment_info(payment_data)

        # Sensitive fields should be encrypted
        assert encrypted_data["account_number"] != payment_data["account_number"]
        assert encrypted_data["routing_number"] != payment_data["routing_number"]
        assert encrypted_data["card_number"] != payment_data["card_number"]
        assert encrypted_data["card_cvv"] != payment_data["card_cvv"]

        # Non-sensitive fields should remain unchanged
        assert encrypted_data["non_sensitive_field"] == payment_data["non_sensitive_field"]

        # Verify all sensitive fields are encrypted
        assert is_encrypted(encrypted_data["account_number"])
        assert is_encrypted(encrypted_data["routing_number"])
        assert is_encrypted(encrypted_data["card_number"])
        assert is_encrypted(encrypted_data["card_cvv"])

    def test_decrypt_payment_info(self):
        """Test payment information decryption"""
        original_data = {
            "account_number": "1234567890",
            "routing_number": "987654321",
            "card_number": "4111111111111111",
            "non_sensitive_field": "public data"
        }

        encrypted_data = encrypt_payment_info(original_data)
        decrypted_data = decrypt_payment_info(encrypted_data)

        # All fields should match original
        assert decrypted_data["account_number"] == original_data["account_number"]
        assert decrypted_data["routing_number"] == original_data["routing_number"]
        assert decrypted_data["card_number"] == original_data["card_number"]
        assert decrypted_data["non_sensitive_field"] == original_data["non_sensitive_field"]

    def test_payment_info_with_missing_fields(self):
        """Test payment info encryption with missing fields"""
        partial_data = {
            "account_number": "1234567890",
            "other_field": "value"
        }

        encrypted_data = encrypt_payment_info(partial_data)
        assert encrypted_data["account_number"] != partial_data["account_number"]
        assert encrypted_data["other_field"] == partial_data["other_field"]

        decrypted_data = decrypt_payment_info(encrypted_data)
        assert decrypted_data["account_number"] == partial_data["account_number"]

    def test_payment_info_with_none_values(self):
        """Test payment info encryption with None values"""
        data_with_nones = {
            "account_number": None,
            "routing_number": "987654321",
            "empty_field": ""
        }

        encrypted_data = encrypt_payment_info(data_with_nones)
        assert encrypted_data["account_number"] is None
        assert encrypted_data["routing_number"] != data_with_nones["routing_number"]
        assert encrypted_data["empty_field"] == ""

    def test_is_encrypted_function(self):
        """Test the is_encrypted utility function"""
        # Test with encrypted data
        encrypted = encrypt_field("test data")
        assert is_encrypted(encrypted)

        # Test with plain text
        assert not is_encrypted("plain text")
        assert not is_encrypted("123456789")
        assert not is_encrypted("")
        assert not is_encrypted(None)

        # Test with invalid base64
        assert not is_encrypted("invalid@base64!")

    def test_encryption_consistency(self):
        """Test that encryption produces consistent but different results"""
        original = "consistent test"
        encrypted1 = encrypt_field(original)
        encrypted2 = encrypt_field(original)

        # Should produce different encrypted values (due to randomization)
        assert encrypted1 != encrypted2

        # But both should decrypt to the same original value
        assert decrypt_field(encrypted1) == original
        assert decrypt_field(encrypted2) == original

    def test_decryption_with_invalid_data(self):
        """Test decryption with invalid encrypted data"""
        with pytest.raises(Exception):
            decrypt_field("invalid-encrypted-data")

        with pytest.raises(Exception):
            decrypt_field("not-base64-encoded!")

    def test_large_data_encryption(self):
        """Test encryption with large amounts of data"""
        large_data = "x" * 10000  # 10KB of data
        encrypted = encrypt_field(large_data)
        decrypted = decrypt_field(encrypted)

        assert decrypted == large_data
        assert is_encrypted(encrypted)

    def test_unicode_data_encryption(self):
        """Test encryption with unicode characters"""
        unicode_data = "Test with émojis 🔒 and spëcial cháracters"
        encrypted = encrypt_field(unicode_data)
        decrypted = decrypt_field(encrypted)

        assert decrypted == unicode_data
        assert is_encrypted(encrypted)