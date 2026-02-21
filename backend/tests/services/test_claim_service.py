"""
Tests for ClaimService functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import date, datetime

from app.services.claim_service import ClaimService, ClaimPolicyOverride, SubrogationRecord
from app.schemas.claim import ClaimCreate


class TestClaimService:
    """Test suite for ClaimService."""

    @pytest.fixture
    def mock_claim_service(self, mock_db_session):
        """Create ClaimService instance with mocked database."""
        return ClaimService(mock_db_session)

    @pytest.mark.asyncio
    @patch('app.services.claim_service.log_action')
    async def test_get_claims_history_success(
        self,
        mock_log_action,
        mock_claim_service,
        mock_claim,
        test_user
    ):
        """Test successful claims history retrieval."""
        mock_log_action.return_value = None

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_claim]

        mock_claim_service.db.query.return_value = mock_query

        # Execute test
        result = await mock_claim_service.get_claims_history(
            policy_id=1,
            user_id=test_user["user_id"],
            status_filter=["open"]
        )

        # Verify results
        assert result["total_count"] == 1
        assert len(result["claims"]) == 1
        assert result["filters_applied"]["policy_id"] == 1

    @pytest.mark.asyncio
    @patch('app.services.claim_service.log_action')
    async def test_create_claim_policy_override(
        self,
        mock_log_action,
        mock_claim_service,
        mock_claim,
        mock_policy,
        test_user
    ):
        """Test claim policy override creation."""
        mock_log_action.return_value = None

        # Setup mocks
        mock_claim_query = Mock()
        mock_claim_query.filter.return_value = mock_claim_query
        mock_claim_query.first.return_value = mock_claim

        mock_policy_query = Mock()
        mock_policy_query.filter.return_value = mock_policy_query
        mock_policy_query.first.return_value = mock_policy

        # Configure query side effect
        def query_side_effect(model_class):
            if 'Claim' in str(model_class):
                return mock_claim_query
            else:  # Policy query
                return mock_policy_query

        mock_claim_service.db.query.side_effect = query_side_effect
        mock_claim_service.db.commit = Mock()

        # Test policy override data
        override_data = {
            "insured_first_name": "Jane",
            "address_line1": "456 New St"
        }

        # Execute test
        result = await mock_claim_service.create_claim_policy_override(
            claim_id=1,
            policy_data=override_data,
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result["success"] is True
        assert result["claim_id"] == 1
        assert "Jane" in result["override_fields"]

    @pytest.mark.asyncio
    @patch('app.services.claim_service.log_action')
    async def test_manage_subrogation(
        self,
        mock_log_action,
        mock_claim_service,
        mock_claim,
        test_user
    ):
        """Test subrogation management."""
        mock_log_action.return_value = None

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_claim

        mock_claim_service.db.query.return_value = mock_query
        mock_claim_service.db.commit = Mock()

        # Test subrogation data
        subrogation_data = {
            "status": "initiated",
            "responsible_party": "Third Party Insurance",
            "potential_recovery": 5000.00,
            "attorney_assigned": "John Legal",
            "case_number": "SUB-2024-001"
        }

        # Execute test
        result = await mock_claim_service.manage_subrogation(
            claim_id=1,
            subrogation_data=subrogation_data,
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result["success"] is True
        assert result["subrogation_status"] == "initiated"
        assert result["case_number"] == "SUB-2024-001"

    @pytest.mark.asyncio
    @patch('app.services.claim_service.log_action')
    async def test_calculate_settlement(
        self,
        mock_log_action,
        mock_claim_service,
        mock_claim,
        test_user
    ):
        """Test settlement calculation."""
        mock_log_action.return_value = None

        # Setup claim with reserves
        mock_claim.total_reserve = Decimal("10000.00")
        mock_claim.total_paid = Decimal("2000.00")
        mock_claim.total_incurred = Decimal("8000.00")

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_claim

        mock_claim_service.db.query.return_value = mock_query

        # Test settlement parameters
        settlement_params = {
            "settlement_percentage": 80,
            "discount_percentage": 10,
            "additional_costs": 500.00
        }

        # Execute test
        result = await mock_claim_service.calculate_settlement(
            claim_id=1,
            settlement_params=settlement_params,
            user_id=test_user["user_id"]
        )

        # Verify calculation
        expected_base = Decimal("8000.00")  # total_incurred
        expected_settlement = expected_base * Decimal("0.8")  # 80%
        expected_discount = expected_settlement * Decimal("0.1")  # 10% discount
        expected_final = expected_settlement - expected_discount + Decimal("500.00")

        assert result["claim_id"] == 1
        assert result["settlement_calculation"]["base_amount"] == float(expected_base)
        assert result["settlement_calculation"]["settlement_percentage"] == 80
        assert result["settlement_calculation"]["discount_percentage"] == 10

    @pytest.mark.asyncio
    @patch('app.services.claim_service.log_action')
    async def test_create_claim_success(
        self,
        mock_log_action,
        mock_claim_service,
        mock_policy,
        test_user
    ):
        """Test successful claim creation."""
        mock_log_action.return_value = None

        # Setup policy mock
        mock_policy_query = Mock()
        mock_policy_query.filter.return_value = mock_policy_query
        mock_policy_query.first.return_value = mock_policy

        mock_claim_service.db.query.return_value = mock_policy_query

        # Create claim data
        claim_data = ClaimCreate(
            policy_id=1,
            date_of_loss=date(2024, 6, 15),
            claim_type="collision",
            description="Rear-end collision"
        )

        # Mock Claim creation
        mock_claim = Mock()
        mock_claim.id = 1
        mock_claim.claim_number = "CLM-2024-001"
        mock_claim.policy_id = 1
        mock_claim.status = "open"
        mock_claim.created_at = datetime.now()

        # Mock database operations
        mock_claim_service.db.add = Mock()
        mock_claim_service.db.commit = Mock()
        mock_claim_service.db.refresh = Mock()

        with patch('app.services.claim_service.Claim', return_value=mock_claim), \
             patch.object(mock_claim_service, '_generate_claim_number', return_value="CLM-2024-001"):

            # Execute test
            result = await mock_claim_service.create_claim(
                claim_data=claim_data,
                user_id=test_user["user_id"]
            )

            # Verify results
            assert result["id"] == 1
            assert result["claim_number"] == "CLM-2024-001"
            assert result["policy_id"] == 1

    @pytest.mark.asyncio
    @patch('app.services.claim_service.log_action')
    async def test_create_claim_invalid_policy(
        self,
        mock_log_action,
        mock_claim_service,
        test_user
    ):
        """Test claim creation with invalid policy."""
        mock_log_action.return_value = None

        # Setup mocks - no policy found
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        mock_claim_service.db.query.return_value = mock_query
        mock_claim_service.db.rollback = Mock()

        # Create claim data
        claim_data = ClaimCreate(
            policy_id=999,
            date_of_loss=date(2024, 6, 15),
            claim_type="collision"
        )

        # Execute test and expect ValueError
        with pytest.raises(ValueError, match="Associated policy not found"):
            await mock_claim_service.create_claim(
                claim_data=claim_data,
                user_id=test_user["user_id"]
            )

    def test_calculate_days_open(self, mock_claim_service):
        """Test days open calculation."""
        mock_claim = Mock()
        mock_claim.created_at = datetime.now()

        result = mock_claim_service._calculate_days_open(mock_claim)
        assert isinstance(result, int)
        assert result >= 0

    def test_generate_claim_number(self, mock_claim_service):
        """Test claim number generation."""
        with patch('app.services.claim_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240615"

            with patch('app.services.claim_service.random.randint', return_value=1234):
                result = mock_claim_service._generate_claim_number()
                assert result.startswith("CLM-20240615-")
                assert result.endswith("1234")