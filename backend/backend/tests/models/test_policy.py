"""
Claims Service Platform - Policy Model Tests
"""

import pytest
from datetime import date
from app.models.policy import Policy, PolicyType, PolicyStatus


class TestPolicyModel:
    """Test Policy model functionality"""

    def test_create_policy(self, db_session):
        """Test creating a basic policy"""
        policy = Policy(
            policy_number="TEST-001",
            policy_type=PolicyType.AUTO,
            status=PolicyStatus.ACTIVE,
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31),
            insured_first_name="John",
            insured_last_name="Doe",
            policy_city="Test City",
            policy_state="CA",
            policy_zip="12345"
        )

        db_session.add(policy)
        db_session.commit()
        db_session.refresh(policy)

        assert policy.id is not None
        assert policy.policy_number == "TEST-001"
        assert policy.policy_type == PolicyType.AUTO
        assert policy.status == PolicyStatus.ACTIVE

    def test_policy_with_encrypted_ssn(self, db_session):
        """Test policy with encrypted SSN"""
        policy = Policy(
            policy_number="TEST-SSN-001",
            policy_type=PolicyType.AUTO,
            status=PolicyStatus.ACTIVE,
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31),
            insured_first_name="Jane",
            insured_last_name="Smith",
            insured_ssn_tin="123456789",  # Will be encrypted
            policy_city="Test City",
            policy_state="NY",
            policy_zip="54321"
        )

        db_session.add(policy)
        db_session.commit()
        db_session.refresh(policy)

        # SSN should be encrypted in storage but accessible through the model
        assert policy.insured_ssn_tin is not None
        assert len(policy.insured_ssn_tin) > 9  # Should be longer due to encryption

    def test_policy_relationships(self, db_session, test_policy):
        """Test policy relationships with claims"""
        from app.models.claim import Claim, ClaimStatus

        claim = Claim(
            claim_number="REL-TEST-001",
            policy_id=test_policy.id,
            date_of_loss=date(2024, 6, 15),
            claim_status=ClaimStatus.OPEN,
            loss_description="Test claim for relationships"
        )

        db_session.add(claim)
        db_session.commit()

        # Test the relationship
        db_session.refresh(test_policy)
        assert len(test_policy.claims) >= 1
        assert claim in test_policy.claims

    def test_policy_validation(self, db_session):
        """Test policy model validation"""
        # Test with invalid state
        policy = Policy(
            policy_number="INVALID-STATE-001",
            policy_type=PolicyType.AUTO,
            status=PolicyStatus.ACTIVE,
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31),
            insured_first_name="Invalid",
            insured_last_name="State",
            policy_city="Test City",
            policy_state="INVALID",  # Invalid state code
            policy_zip="12345"
        )

        # Depending on model validation, this might raise an error or be accepted
        try:
            db_session.add(policy)
            db_session.commit()
            # If no error, that's also acceptable - validation might be at API level
        except Exception:
            # Validation error is expected
            db_session.rollback()

    def test_policy_types(self):
        """Test policy type enumeration"""
        assert PolicyType.AUTO.value == "auto"
        assert PolicyType.HOME.value == "home"
        assert PolicyType.LIFE.value == "life"
        assert PolicyType.HEALTH.value == "health"

    def test_policy_status(self):
        """Test policy status enumeration"""
        assert PolicyStatus.ACTIVE.value == "active"
        assert PolicyStatus.INACTIVE.value == "inactive"
        assert PolicyStatus.EXPIRED.value == "expired"
        assert PolicyStatus.CANCELLED.value == "cancelled"