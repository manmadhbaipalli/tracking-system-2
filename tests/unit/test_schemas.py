"""
Test Pydantic schemas for request/response validation.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.auth import UserCreate, UserResponse, Token
from app.schemas.policy import PolicyCreate, PolicyResponse, PolicySearchRequest
from app.schemas.claim import ClaimCreate, ClaimResponse
from app.schemas.payment import PaymentCreate, PaymentResponse


def test_user_create_schema():
    """Test user creation schema validation."""
    # Valid user data
    valid_data = {
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "Test",
        "last_name": "User",
        "role": "agent"
    }

    user = UserCreate(**valid_data)
    assert user.email == "test@example.com"
    assert user.password == "securepassword123"
    assert user.first_name == "Test"
    assert user.role == "agent"

    # Invalid email should fail
    invalid_data = valid_data.copy()
    invalid_data["email"] = "not-an-email"
    with pytest.raises(ValidationError):
        UserCreate(**invalid_data)

    # Missing required field should fail
    incomplete_data = valid_data.copy()
    del incomplete_data["email"]
    with pytest.raises(ValidationError):
        UserCreate(**incomplete_data)


def test_user_response_schema():
    """Test user response schema validation."""
    valid_data = {
        "id": "12345678-1234-1234-1234-123456789012",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "agent",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    user_response = UserResponse(**valid_data)
    assert user_response.email == "test@example.com"
    assert user_response.is_active is True


def test_token_schema():
    """Test token schema validation."""
    valid_data = {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }

    token = Token(**valid_data)
    assert token.access_token.startswith("eyJ")
    assert token.token_type == "bearer"
    assert token.expires_in == 3600


def test_policy_create_schema():
    """Test policy creation schema validation."""
    valid_data = {
        "policy_number": "POL-001",
        "policy_type": "AUTO",
        "effective_date": date(2024, 1, 1),
        "expiration_date": date(2024, 12, 31),
        "insured_first_name": "John",
        "insured_last_name": "Doe",
        "policy_city": "New York",
        "policy_state": "NY",
        "policy_zip": "10001",
        "premium_amount": Decimal("1200.00")
    }

    policy = PolicyCreate(**valid_data)
    assert policy.policy_number == "POL-001"
    assert policy.policy_type == "AUTO"
    assert policy.premium_amount == Decimal("1200.00")

    # Invalid state (too long) should fail
    invalid_data = valid_data.copy()
    invalid_data["policy_state"] = "NEW YORK"  # Should be 2 chars
    with pytest.raises(ValidationError):
        PolicyCreate(**invalid_data)


def test_policy_search_schema():
    """Test policy search schema validation."""
    # Empty search should be valid
    empty_search = PolicySearchRequest()
    assert empty_search.policy_number is None
    assert empty_search.insured_first_name is None

    # Search with criteria should be valid
    search_data = {
        "policy_number": "POL-001",
        "insured_first_name": "John",
        "insured_last_name": "Doe",
        "policy_type": "AUTO",
        "policy_state": "NY",
        "policy_city": "New York"
    }

    search = PolicySearchRequest(**search_data)
    assert search.policy_number == "POL-001"
    assert search.insured_first_name == "John"
    assert search.policy_state == "NY"


def test_claim_create_schema():
    """Test claim creation schema validation."""
    valid_data = {
        "policy_id": "12345678-1234-1234-1234-123456789012",
        "claim_number": "CLM-001",
        "claim_type": "COLLISION",
        "date_of_loss": date(2024, 6, 15),
        "loss_description": "Rear-end collision at intersection",
        "reported_date": datetime(2024, 6, 16, 10, 30)
    }

    claim = ClaimCreate(**valid_data)
    assert claim.claim_number == "CLM-001"
    assert claim.claim_type == "COLLISION"
    assert claim.loss_description == "Rear-end collision at intersection"

    # Invalid UUID should fail
    invalid_data = valid_data.copy()
    invalid_data["policy_id"] = "not-a-uuid"
    with pytest.raises(ValidationError):
        ClaimCreate(**invalid_data)


def test_payment_create_schema():
    """Test payment creation schema validation."""
    valid_data = {
        "claim_id": "12345678-1234-1234-1234-123456789012",
        "payment_number": "PAY-001",
        "payment_type": "CLAIM_SETTLEMENT",
        "payment_method": "ACH",
        "total_amount": Decimal("5000.00"),
        "currency": "USD"
    }

    payment = PaymentCreate(**valid_data)
    assert payment.payment_number == "PAY-001"
    assert payment.payment_type == "CLAIM_SETTLEMENT"
    assert payment.total_amount == Decimal("5000.00")

    # Negative amount should be allowed (reversals)
    negative_data = valid_data.copy()
    negative_data["total_amount"] = Decimal("-1000.00")
    negative_payment = PaymentCreate(**negative_data)
    assert negative_payment.total_amount == Decimal("-1000.00")


def test_schema_field_validation():
    """Test specific field validation rules."""
    # Test email validation
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            email="invalid-email",
            password="pass123",
            first_name="Test",
            last_name="User"
        )
    assert "email" in str(exc_info.value).lower()

    # Test state code validation (should be 2 characters)
    with pytest.raises(ValidationError) as exc_info:
        PolicyCreate(
            policy_number="POL-001",
            policy_type="AUTO",
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31),
            insured_first_name="John",
            insured_last_name="Doe",
            policy_city="Boston",
            policy_state="MASSACHUSETTS",  # Too long
            policy_zip="02101"
        )
    assert "policy_state" in str(exc_info.value).lower()