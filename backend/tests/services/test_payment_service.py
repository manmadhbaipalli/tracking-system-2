"""
Tests for PaymentService functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from app.services.payment_service import PaymentService, PaymentRequest, PaymentMethodType, ReserveAllocation


class TestPaymentService:
    """Test suite for PaymentService."""

    @pytest.fixture
    def mock_payment_service(self, mock_db_session):
        return PaymentService(mock_db_session)

    @pytest.mark.asyncio
    @patch('app.services.payment_service.log_action')
    async def test_process_payment_success(
        self,
        mock_log_action,
        mock_payment_service,
        mock_claim,
        test_user
    ):
        """Test successful payment processing."""
        mock_log_action.return_value = None

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_claim

        mock_payment_service.db.query.return_value = mock_query
        mock_payment_service.db.add = Mock()
        mock_payment_service.db.commit = Mock()
        mock_payment_service.db.refresh = Mock()

        # Mock payment processing method
        mock_payment_service._process_payment_by_method = AsyncMock(
            return_value={"success": True, "transaction_id": "TXN-123", "status": "completed"}
        )
        mock_payment_service._validate_reserve_allocation = AsyncMock(
            return_value=Mock(success=True)
        )
        mock_payment_service._update_reserves_for_payment = AsyncMock()

        # Create payment request
        payment_request = PaymentRequest(
            claim_id=1,
            payment_method=PaymentMethodType.ACH,
            amount=Decimal("2500.00")
        )

        with patch('app.services.payment_service.Payment') as MockPayment:
            mock_payment = Mock()
            mock_payment.id = 1
            mock_payment.status = "completed"
            MockPayment.return_value = mock_payment

            # Execute test
            result = await mock_payment_service.process_payment(
                payment_request=payment_request,
                user_id=test_user["user_id"]
            )

            # Verify results
            assert result.success is True
            assert result.payment_id == 1

    @pytest.mark.asyncio
    @patch('app.services.payment_service.log_action')
    async def test_allocate_reserves_success(
        self,
        mock_log_action,
        mock_payment_service,
        mock_claim,
        test_user
    ):
        """Test successful reserve allocation."""
        mock_log_action.return_value = None

        # Setup claim with reserves
        mock_claim.metadata = {}

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_claim

        mock_payment_service.db.query.return_value = mock_query
        mock_payment_service._get_claim_reserves = Mock(return_value={
            "indemnity": Decimal("5000.00"),
            "expense": Decimal("1000.00")
        })
        mock_payment_service._update_claim_reserves = AsyncMock()

        # Create reserve allocations
        allocations = [
            ReserveAllocation("indemnity", Decimal("2500.00"), eroding=True),
            ReserveAllocation("expense", Decimal("500.00"), eroding=True)
        ]

        # Execute test
        result = await mock_payment_service.allocate_reserves(
            claim_id=1,
            allocations=allocations,
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result.success is True
        assert result.total_allocated == Decimal("3000.00")

    @pytest.mark.asyncio
    async def test_validate_payment_method_ach(
        self,
        mock_payment_service,
        test_user
    ):
        """Test ACH payment method validation."""
        with patch('app.services.payment_service.log_action') as mock_log:
            mock_log.return_value = None

            # Valid ACH details
            valid_details = {
                "routing_number": "123456789",
                "account_number": "987654321",
                "account_type": "checking"
            }

            result = await mock_payment_service.validate_payment_method(
                method=PaymentMethodType.ACH,
                details=valid_details,
                user_id=test_user["user_id"]
            )

            assert result["is_valid"] is True
            assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_payment_method_invalid_ach(
        self,
        mock_payment_service,
        test_user
    ):
        """Test invalid ACH payment method validation."""
        with patch('app.services.payment_service.log_action') as mock_log:
            mock_log.return_value = None

            # Invalid ACH details
            invalid_details = {
                "routing_number": "12345",  # Too short
                "account_number": "",  # Missing
            }

            result = await mock_payment_service.validate_payment_method(
                method=PaymentMethodType.ACH,
                details=invalid_details,
                user_id=test_user["user_id"]
            )

            assert result["is_valid"] is False
            assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_calculate_settlement_amount(
        self,
        mock_payment_service,
        mock_claim,
        test_user
    ):
        """Test settlement amount calculation."""
        with patch('app.services.payment_service.log_action') as mock_log:
            mock_log.return_value = None

            # Setup claim with reserves
            mock_claim.total_reserve = Decimal("10000.00")

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_claim

            mock_payment_service.db.query.return_value = mock_query

            # Execute test
            result = await mock_payment_service.calculate_settlement_amount(
                claim_id=1,
                percentage=75.0,
                user_id=test_user["user_id"]
            )

            # Verify calculation
            assert result == Decimal("7500.00")  # 75% of 10000