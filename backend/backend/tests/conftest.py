"""
Claims Service Platform - Test Configuration and Fixtures
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

from app.core.database import Base, get_db
from app.core.config import Settings
from app.services.auth_service import auth_service
from backend.main import app


# Test database configuration using in-memory SQLite
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings fixture"""
    return Settings(
        ENVIRONMENT="testing",
        DATABASE_URL=TEST_SQLALCHEMY_DATABASE_URL,
        SECRET_KEY="test-secret-key-32-chars-long!!",
        ENCRYPTION_KEY="test-encryption-key-32-chars!!",
        FIELD_ENCRYPTION_SALT="test-salt-for-field-encryption"
    )


@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client(db_session):
    """Create test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    from app.models.user import User
    from app.core.security import get_password_hash, UserRole

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        role=UserRole.ADJUSTER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create admin test user"""
    from app.models.user import User
    from app.core.security import get_password_hash, UserRole

    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_client, test_user):
    """Create authentication headers for test user"""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    response = test_client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
def admin_headers(test_client, admin_user):
    """Create authentication headers for admin user"""
    login_data = {
        "username": "admin",
        "password": "adminpassword123"
    }
    response = test_client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
def test_policy(db_session):
    """Create test policy"""
    from app.models.policy import Policy, PolicyType, PolicyStatus
    from datetime import date, datetime

    policy = Policy(
        policy_number="TEST-POL-001",
        policy_type=PolicyType.AUTO,
        status=PolicyStatus.ACTIVE,
        effective_date=date(2024, 1, 1),
        expiration_date=date(2024, 12, 31),
        insured_first_name="John",
        insured_last_name="Doe",
        insured_ssn_tin="123456789",  # Will be encrypted
        policy_city="Test City",
        policy_state="CA",
        policy_zip="12345",
        organizational_name=None,
        vehicle_year=2020,
        vehicle_make="Toyota",
        vehicle_model="Camry",
        vehicle_vin="1HGBH41JXMN109186",
        policy_limits_liability=100000,
        deductible_collision=500,
        deductible_comprehensive=250
    )
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)
    return policy


@pytest.fixture
def test_claim(db_session, test_policy):
    """Create test claim"""
    from app.models.claim import Claim, ClaimStatus
    from datetime import date

    claim = Claim(
        claim_number="CLM-001",
        policy_id=test_policy.id,
        date_of_loss=date(2024, 6, 15),
        claim_status=ClaimStatus.OPEN,
        loss_description="Vehicle collision",
        reported_date=date(2024, 6, 16),
        claim_amount=5000.00
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)
    return claim


@pytest.fixture
def test_payment(db_session, test_claim):
    """Create test payment"""
    from app.models.payment import Payment, PaymentStatus, PaymentMethod
    from decimal import Decimal

    payment = Payment(
        claim_id=test_claim.id,
        payment_number="PAY-001",
        amount=Decimal("1500.00"),
        payment_method=PaymentMethod.ACH,
        status=PaymentStatus.PENDING,
        payee_name="John Doe",
        payee_address="123 Test St, Test City, CA 12345"
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment