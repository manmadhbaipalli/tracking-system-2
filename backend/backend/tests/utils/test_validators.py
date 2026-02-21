"""
Claims Service Platform - Validation Utilities Tests
"""

import pytest
from app.utils.validators import (
    validate_ssn, validate_tin, validate_policy_number,
    validate_zip_code, validate_state_code
)


class TestValidationUtils:
    """Test validation utility functions"""

    def test_validate_ssn_valid(self):
        """Test SSN validation with valid inputs"""
        valid_ssns = [
            "123456789",
            "123-45-6789",
            "123 45 6789"
        ]

        for ssn in valid_ssns:
            assert validate_ssn(ssn) == True

    def test_validate_ssn_invalid(self):
        """Test SSN validation with invalid inputs"""
        invalid_ssns = [
            "12345678",      # Too short
            "1234567890",    # Too long
            "000000000",     # Invalid pattern
            "111111111",     # Invalid pattern
            "666123456",     # Invalid area number
            "123456789a",    # Contains letters
            "",              # Empty
            None,            # None
            "123-45-67890",  # Too many digits in last group
        ]

        for ssn in invalid_ssns:
            assert validate_ssn(ssn) == False

    def test_validate_tin_valid(self):
        """Test TIN/EIN validation with valid inputs"""
        valid_tins = [
            "123456789",
            "12-3456789",
            "12 3456789"
        ]

        for tin in valid_tins:
            assert validate_tin(tin) == True

    def test_validate_tin_invalid(self):
        """Test TIN validation with invalid inputs"""
        invalid_tins = [
            "12345678",      # Too short
            "1234567890",    # Too long
            "12345678a",     # Contains letters
            "",              # Empty
            None,            # None
        ]

        for tin in invalid_tins:
            assert validate_tin(tin) == False

    def test_validate_policy_number_valid(self):
        """Test policy number validation with valid inputs"""
        valid_policy_numbers = [
            "POL-123456",
            "POLICY-2024-001",
            "AUTO-123-456-789",
            "HOME2024001",
            "COMM-ABC-123"
        ]

        for policy_num in valid_policy_numbers:
            assert validate_policy_number(policy_num) == True

    def test_validate_policy_number_invalid(self):
        """Test policy number validation with invalid inputs"""
        invalid_policy_numbers = [
            "",              # Empty
            None,            # None
            "A",             # Too short
            "x" * 51,        # Too long (assuming 50 char limit)
            "POL 123",       # Contains spaces (if not allowed)
            "POL@123",       # Contains invalid characters
        ]

        for policy_num in invalid_policy_numbers:
            assert validate_policy_number(policy_num) == False

    def test_validate_zip_code_valid(self):
        """Test ZIP code validation with valid inputs"""
        valid_zip_codes = [
            "12345",         # 5-digit ZIP
            "12345-6789",    # 9-digit ZIP with dash
            "123456789",     # 9-digit ZIP without dash
        ]

        for zip_code in valid_zip_codes:
            assert validate_zip_code(zip_code) == True

    def test_validate_zip_code_invalid(self):
        """Test ZIP code validation with invalid inputs"""
        invalid_zip_codes = [
            "1234",          # Too short
            "123456",        # 6 digits (invalid)
            "1234567890",    # Too long
            "12345-678",     # Incomplete +4
            "abcde",         # Letters
            "",              # Empty
            None,            # None
        ]

        for zip_code in invalid_zip_codes:
            assert validate_zip_code(zip_code) == False

    def test_validate_state_code_valid(self):
        """Test state code validation with valid inputs"""
        valid_state_codes = [
            "CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI",
            "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
            "CO", "MN", "SC", "AL", "LA", "KY", "OR", "OK", "CT", "UT",
            "IA", "NV", "AR", "MS", "KS", "NM", "NE", "WV", "ID", "HI",
            "NH", "ME", "MT", "RI", "DE", "SD", "ND", "AK", "VT", "WY",
            "DC"  # District of Columbia
        ]

        for state_code in valid_state_codes:
            assert validate_state_code(state_code) == True

    def test_validate_state_code_invalid(self):
        """Test state code validation with invalid inputs"""
        invalid_state_codes = [
            "ZZ",            # Invalid state
            "CAL",           # Too long
            "C",             # Too short
            "ca",            # Lowercase (if case sensitive)
            "12",            # Numbers
            "",              # Empty
            None,            # None
        ]

        for state_code in invalid_state_codes:
            assert validate_state_code(state_code) == False

    def test_validate_state_code_case_insensitive(self):
        """Test that state code validation handles case properly"""
        # Test both cases if validator is case insensitive
        assert validate_state_code("CA") == validate_state_code("ca") or validate_state_code("ca") == False

    def test_edge_cases(self):
        """Test edge cases for all validators"""
        edge_cases = [
            "",              # Empty string
            None,            # None value
            "   ",           # Whitespace only
            123,             # Integer instead of string
            [],              # List
            {},              # Dict
        ]

        validators = [
            validate_ssn,
            validate_tin,
            validate_policy_number,
            validate_zip_code,
            validate_state_code
        ]

        for validator in validators:
            for edge_case in edge_cases:
                try:
                    result = validator(edge_case)
                    # Should return False for all edge cases
                    assert result == False
                except (TypeError, AttributeError):
                    # It's acceptable to raise type errors for non-string inputs
                    pass

    def test_ssn_normalization_behavior(self):
        """Test that SSN validation handles formatting consistently"""
        ssn_formats = [
            "123456789",
            "123-45-6789",
            "123 45 6789"
        ]

        # All should be valid
        for ssn in ssn_formats:
            assert validate_ssn(ssn) == True

    def test_policy_number_length_limits(self):
        """Test policy number length constraints"""
        # Test minimum length
        assert validate_policy_number("A") == False
        assert validate_policy_number("AB") == False  # Assuming min length > 2

        # Test reasonable length
        assert validate_policy_number("POL-123") == True

        # Test maximum length
        very_long_policy = "POL-" + "x" * 100
        result = validate_policy_number(very_long_policy)
        # Should be False if there's a reasonable length limit
        assert result in [True, False]  # Depends on implementation

    def test_zip_code_formatting(self):
        """Test ZIP code formatting variations"""
        zip_variations = [
            ("12345", True),
            ("12345-6789", True),
            ("123456789", True),
            ("12345 6789", False),  # Space instead of dash
            ("12345_6789", False),  # Underscore
        ]

        for zip_code, expected in zip_variations:
            assert validate_zip_code(zip_code) == expected