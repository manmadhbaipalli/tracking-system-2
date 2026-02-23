"""
Test database models.
"""

import pytest
import uuid
from datetime import date, datetime
from decimal import Decimal

from app.models.user import User, Role
from app.models.policy import Policy
from app.models.claim import Claim
from app.models.payment import Payment
from app.models.audit import AuditLog


def test_user_model():
    """Test User model creation."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_here",
        first_name="Test",
        last_name="User",
        role=Role.AGENT,
        is_active=True
    )

    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.role == Role.AGENT
    assert user.is_active is True
    assert user.full_name == "Test User"


def test_policy_model():
    """Test Policy model creation."""
    policy = Policy(
        policy_number="POL-001",
        policy_type="AUTO",
        policy_status="ACTIVE",
        effective_date=date(2024, 1, 1),
        expiration_date=date(2024, 12, 31),
        insured_first_name="John",
        insured_last_name="Doe",
        policy_city="New York",
        policy_state="NY",
        policy_zip="10001",
        premium_amount=Decimal("1200.00")
    )

    assert policy.policy_number == "POL-001"
    assert policy.policy_type == "AUTO"
    assert policy.insured_name == "John Doe"
    assert policy.policy_city == "New York"
    assert policy.premium_amount == Decimal("1200.00")


def test_policy_properties():
    """Test Policy model properties."""
    policy = Policy(
        policy_number="POL-002",
        policy_type="AUTO",
        policy_status="ACTIVE",
        effective_date=date(2024, 1, 1),
        expiration_date=date(2024, 12, 31),
        insured_first_name="Jane",
        insured_last_name="Smith",
        organizational_name="ABC Corp",
        policy_address="123 Main St",
        policy_city="Boston",
        policy_state="MA",
        policy_zip="02101",
        vehicle_details={"year": 2023, "make": "Toyota", "model": "Camry"},
        coverage_details={"liability": {"limit": 100000, "deductible": 500}}
    )

    # Test organizational name takes precedence
    assert policy.insured_name == "ABC Corp"

    # Test full address formatting
    assert "123 Main St" in policy.full_address
    assert "Boston" in policy.full_address
    assert "MA" in policy.full_address

    # Test vehicle and coverage info
    vehicle_info = policy.get_vehicle_info()
    assert vehicle_info["year"] == 2023
    assert vehicle_info["make"] == "Toyota"

    coverage_info = policy.get_coverage_info()
    assert coverage_info["liability"]["limit"] == 100000

    # Test coverage limit retrieval
    liability_limit = policy.get_coverage_limit("liability")
    assert liability_limit == Decimal("100000")


def test_claim_model():
    """Test Claim model creation."""
    policy_id = uuid.uuid4()

    claim = Claim(
        policy_id=policy_id,
        claim_number="CLM-001",
        claim_type="COLLISION",
        claim_status="OPEN",
        date_of_loss=date(2024, 6, 15),
        reported_date=datetime(2024, 6, 16, 10, 30),
        loss_description="Rear-end collision at intersection"
    )

    assert claim.policy_id == policy_id
    assert claim.claim_number == "CLM-001"
    assert claim.claim_type == "COLLISION"
    assert claim.claim_status == "OPEN"
    assert claim.loss_description == "Rear-end collision at intersection"


def test_payment_model():
    """Test Payment model creation."""
    claim_id = uuid.uuid4()

    payment = Payment(
        claim_id=claim_id,
        payment_number="PAY-001",
        payment_type="CLAIM_SETTLEMENT",
        payment_method="ACH",
        payment_status="PENDING",
        total_amount=Decimal("5000.00"),
        currency="USD"
    )

    assert payment.claim_id == claim_id
    assert payment.payment_number == "PAY-001"
    assert payment.payment_type == "CLAIM_SETTLEMENT"
    assert payment.payment_method == "ACH"
    assert payment.total_amount == Decimal("5000.00")
    assert payment.currency == "USD"


def test_audit_log_model():
    """Test AuditLog model creation."""
    user_id = uuid.uuid4()
    entity_id = uuid.uuid4()

    audit = AuditLog(
        entity_type="Policy",
        entity_id=entity_id,
        action="CREATE",
        user_id=user_id,
        changes={"policy_number": "POL-001", "status": "ACTIVE"},
        ip_address="192.168.1.1"
    )

    assert audit.entity_type == "Policy"
    assert audit.entity_id == entity_id
    assert audit.action == "CREATE"
    assert audit.user_id == user_id
    assert audit.changes["policy_number"] == "POL-001"
    assert audit.ip_address == "192.168.1.1"


def test_model_relationships():
    """Test model relationships are properly defined."""
    # Test that relationships exist (even if we can't test them fully without DB)
    assert hasattr(Policy, 'claims')
    assert hasattr(Claim, 'policy')
    assert hasattr(Claim, 'payments')
    assert hasattr(Payment, 'claim')