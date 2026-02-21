"""
Test configuration and shared fixtures for claims system tests.
"""

import pytest
import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base
from app.models.policy import Policy, PolicyStatus
from app.models.claim import Claim, ClaimStatus
from app.models.payment import Payment, PaymentStatus


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.refresh = Mock()
    return session


@pytest.fixture
def sample_policy_data():
    """Sample policy data for testing."""
    return {
        "id": 1,
        "policy_number": "POL-2024-001",
        "policy_type": "auto",
        "insured_first_name": "John",
        "insured_last_name": "Doe",
        "organization_name": None,
        "effective_date": date(2024, 1, 1),
        "expiration_date": date(2024, 12, 31),
        "address_line1": "123 Main St",
        "address_line2": None,
        "city": "Anytown",
        "state": "CA",
        "zip_code": "12345",
        "premium_amount": Decimal("1200.00"),
        "status": PolicyStatus.ACTIVE.value,
        "vehicle_vin": "1HGBH41JXMN109186",
        "vehicle_year": 2023,
        "vehicle_make": "Honda",
        "vehicle_model": "Civic",
        "coverage_details": {
            "liability": {"limit": 100000},
            "comprehensive": {"deductible": 500},
            "collision": {"deductible": 500}
        },
        "is_deleted": False
    }


@pytest.fixture
def sample_claim_data():
    """Sample claim data for testing."""
    return {
        "id": 1,
        "claim_number": "CLM-2024-001",
        "policy_id": 1,
        "date_of_loss": date(2024, 6, 15),
        "status": ClaimStatus.OPEN.value,
        "claim_type": "collision",
        "total_incurred": Decimal("5000.00"),
        "total_paid": Decimal("2500.00"),
        "total_reserve": Decimal("2500.00"),
        "adjuster_name": "Jane Smith",
        "description": "Rear-end collision",
        "is_deleted": False
    }


@pytest.fixture
def sample_payment_data():
    """Sample payment data for testing."""
    return {
        "id": 1,
        "claim_id": 1,
        "amount": Decimal("2500.00"),
        "payment_method": "ach",
        "status": PaymentStatus.COMPLETED.value,
        "transaction_id": "TXN-12345",
        "payee_name": "John Doe",
        "tax_reportable": False,
        "is_deleted": False
    }


@pytest.fixture
def mock_policy():
    """Mock policy object for testing."""
    policy = Mock(spec=Policy)
    policy.id = 1
    policy.policy_number = "POL-2024-001"
    policy.insured_first_name = "John"
    policy.insured_last_name = "Doe"
    policy.is_deleted = False
    policy.to_dict = Mock(return_value={"id": 1, "policy_number": "POL-2024-001"})
    policy.is_active = Mock(return_value=True)
    policy.is_expired = Mock(return_value=False)
    policy.days_until_expiration = Mock(return_value=30)
    policy.generate_full_name = Mock()
    policy.update_search_vector = Mock()
    return policy


@pytest.fixture
def mock_claim():
    """Mock claim object for testing."""
    claim = Mock(spec=Claim)
    claim.id = 1
    claim.claim_number = "CLM-2024-001"
    claim.policy_id = 1
    claim.status = "open"
    claim.is_deleted = False
    claim.created_at = Mock()
    claim.created_at.days = 30
    return claim


@pytest.fixture
def mock_payment():
    """Mock payment object for testing."""
    payment = Mock(spec=Payment)
    payment.id = 1
    payment.claim_id = 1
    payment.amount = Decimal("2500.00")
    payment.status = "completed"
    payment.is_deleted = False
    return payment


@pytest.fixture
def mock_audit_service():
    """Mock audit service for testing."""
    audit_mock = AsyncMock()
    audit_mock.log_action = AsyncMock(return_value=None)
    return audit_mock


@pytest.fixture
def test_user():
    """Test user data."""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "permissions": ["policy_read", "policy_write", "claim_read", "payment_read"]
    }


@pytest.fixture
def mock_encryption():
    """Mock encryption/decryption functions."""
    def mock_encrypt(data):
        return f"encrypted_{data}"

    def mock_decrypt(encrypted_data):
        if encrypted_data.startswith("encrypted_"):
            return encrypted_data[10:]
        return encrypted_data

    return {"encrypt": mock_encrypt, "decrypt": mock_decrypt}


# Async test helpers
def async_mock_return(return_value):
    """Create an async mock that returns a specific value."""
    async def _async_return():
        return return_value
    return AsyncMock(return_value=return_value)