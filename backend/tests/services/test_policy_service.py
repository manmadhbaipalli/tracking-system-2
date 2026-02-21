"""
Tests for PolicyService functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import date

from app.services.policy_service import PolicyService
from app.schemas.policy import PolicySearchRequest, PolicyCreate, PolicyUpdate


class TestPolicyService:
    """Test suite for PolicyService."""

    @pytest.fixture
    def mock_policy_service(self, mock_db_session):
        """Create PolicyService instance with mocked database."""
        return PolicyService(mock_db_session)

    @pytest.fixture
    def search_request(self):
        """Sample search request for testing."""
        return PolicySearchRequest(
            policy_number="POL-2024",
            insured_first_name="John",
            insured_last_name="Doe",
            search_type="partial",
            page=1,
            page_size=10
        )

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_search_policies_success(
        self,
        mock_log_action,
        mock_policy_service,
        search_request,
        mock_policy,
        test_user
    ):
        """Test successful policy search."""
        # Setup mocks
        mock_log_action.return_value = None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_policy]

        mock_policy_service.db.query.return_value = mock_query

        # Execute test
        result = await mock_policy_service.search_policies(
            criteria=search_request,
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result["total"] == 1
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert len(result["policies"]) == 1
        assert result["policies"][0]["id"] == 1

        # Verify logging was called
        mock_log_action.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_search_policies_exact_match(
        self,
        mock_log_action,
        mock_policy_service,
        mock_policy,
        test_user
    ):
        """Test exact match policy search."""
        mock_log_action.return_value = None

        # Create exact search request
        exact_search = PolicySearchRequest(
            policy_number="POL-2024-001",
            search_type="exact",
            page=1,
            page_size=10
        )

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_policy]

        mock_policy_service.db.query.return_value = mock_query

        # Execute test
        result = await mock_policy_service.search_policies(
            criteria=exact_search,
            user_id=test_user["user_id"]
        )

        # Verify exact match was performed
        assert result["total"] == 1
        mock_policy_service.db.query.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    @patch('app.services.policy_service.encrypt_data')
    async def test_search_policies_ssn_tin(
        self,
        mock_encrypt_data,
        mock_log_action,
        mock_policy_service,
        mock_policy,
        test_user
    ):
        """Test policy search with SSN/TIN."""
        mock_log_action.return_value = None
        mock_encrypt_data.return_value = "encrypted_123456789"

        # Create search with SSN
        ssn_search = PolicySearchRequest(
            ssn_tin="123-45-6789",
            search_type="exact",
            page=1,
            page_size=10
        )

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_policy]

        mock_policy_service.db.query.return_value = mock_query

        # Execute test
        result = await mock_policy_service.search_policies(
            criteria=ssn_search,
            user_id=test_user["user_id"]
        )

        # Verify encryption was called
        mock_encrypt_data.assert_called_once_with("123-45-6789")
        assert result["total"] == 1

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_get_policy_details_success(
        self,
        mock_log_action,
        mock_policy_service,
        mock_policy,
        test_user
    ):
        """Test successful policy details retrieval."""
        mock_log_action.return_value = None

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_policy

        mock_policy_service.db.query.return_value = mock_query

        # Execute test
        result = await mock_policy_service.get_policy_details(
            policy_id=1,
            user_id=test_user["user_id"],
            mask_pii=True
        )

        # Verify results
        assert result is not None
        assert result["id"] == 1
        assert "is_active" in result
        assert "is_expired" in result
        assert "days_until_expiration" in result

        # Verify logging was called
        mock_log_action.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_get_policy_details_not_found(
        self,
        mock_log_action,
        mock_policy_service,
        test_user
    ):
        """Test policy details when policy not found."""
        mock_log_action.return_value = None

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        mock_policy_service.db.query.return_value = mock_query

        # Execute test
        result = await mock_policy_service.get_policy_details(
            policy_id=999,
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result is None

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    @patch('app.services.policy_service.validate_policy_number')
    @patch('app.services.policy_service.validate_ssn')
    async def test_create_policy_success(
        self,
        mock_validate_ssn,
        mock_validate_policy_number,
        mock_log_action,
        mock_policy_service,
        test_user
    ):
        """Test successful policy creation."""
        mock_log_action.return_value = None
        mock_validate_policy_number.return_value = None
        mock_validate_ssn.return_value = None

        # Create policy data
        policy_data = PolicyCreate(
            policy_number="POL-2024-001",
            policy_type="auto",
            insured_first_name="John",
            insured_last_name="Doe",
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31),
            address_line1="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            ssn="123-45-6789"
        )

        # Setup mocks for duplicate check
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No existing policy

        mock_policy_service.db.query.return_value = mock_query

        # Mock Policy creation
        mock_policy = Mock()
        mock_policy.id = 1
        mock_policy.policy_number = "POL-2024-001"
        mock_policy.to_dict.return_value = {"id": 1, "policy_number": "POL-2024-001"}
        mock_policy.generate_full_name = Mock()
        mock_policy.update_search_vector = Mock()

        # Mock database operations
        mock_policy_service.db.add = Mock()
        mock_policy_service.db.commit = Mock()
        mock_policy_service.db.refresh = Mock()

        with patch('app.services.policy_service.Policy', return_value=mock_policy):
            # Execute test
            result = await mock_policy_service.create_policy(
                policy_data=policy_data,
                user_id=test_user["user_id"]
            )

            # Verify results
            assert result["id"] == 1
            assert result["policy_number"] == "POL-2024-001"

            # Verify database operations
            mock_policy_service.db.add.assert_called_once()
            mock_policy_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    @patch('app.services.policy_service.validate_policy_number')
    async def test_create_policy_duplicate(
        self,
        mock_validate_policy_number,
        mock_log_action,
        mock_policy_service,
        mock_policy,
        test_user
    ):
        """Test policy creation with duplicate policy number."""
        mock_log_action.return_value = None
        mock_validate_policy_number.return_value = None

        # Create policy data
        policy_data = PolicyCreate(
            policy_number="POL-2024-001",
            policy_type="auto",
            insured_first_name="John",
            insured_last_name="Doe",
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31),
            address_line1="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345"
        )

        # Setup mocks for duplicate check
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_policy  # Existing policy found

        mock_policy_service.db.query.return_value = mock_query

        # Execute test and expect ValueError
        with pytest.raises(ValueError, match="Policy number POL-2024-001 already exists"):
            await mock_policy_service.create_policy(
                policy_data=policy_data,
                user_id=test_user["user_id"]
            )

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_update_policy_success(
        self,
        mock_log_action,
        mock_policy_service,
        mock_policy,
        test_user
    ):
        """Test successful policy update."""
        mock_log_action.return_value = None

        # Create update data
        update_data = PolicyUpdate(
            insured_first_name="Jane",
            city="New City"
        )

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_policy

        mock_policy_service.db.query.return_value = mock_query
        mock_policy_service.db.commit = Mock()

        # Execute test
        result = await mock_policy_service.update_policy(
            policy_id=1,
            policy_data=update_data,
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result["id"] == 1
        mock_policy_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_update_policy_not_found(
        self,
        mock_log_action,
        mock_policy_service,
        test_user
    ):
        """Test policy update when policy not found."""
        mock_log_action.return_value = None

        # Create update data
        update_data = PolicyUpdate(city="New City")

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        mock_policy_service.db.query.return_value = mock_query

        # Execute test and expect ValueError
        with pytest.raises(ValueError, match="Policy not found"):
            await mock_policy_service.update_policy(
                policy_id=999,
                policy_data=update_data,
                user_id=test_user["user_id"]
            )

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_get_policy_claims_history(
        self,
        mock_log_action,
        mock_policy_service,
        mock_policy,
        mock_claim,
        test_user
    ):
        """Test policy claims history retrieval."""
        mock_log_action.return_value = None

        # Setup policy mock
        mock_policy_query = Mock()
        mock_policy_query.filter.return_value = mock_policy_query
        mock_policy_query.first.return_value = mock_policy

        # Setup claims mock
        mock_claims_query = Mock()
        mock_claims_query.filter.return_value = mock_claims_query
        mock_claims_query.order_by.return_value = mock_claims_query
        mock_claims_query.all.return_value = [mock_claim]

        # Configure query side effect
        def query_side_effect(model_class):
            if 'Policy' in str(model_class):
                return mock_policy_query
            else:  # Claim query
                return mock_claims_query

        mock_policy_service.db.query.side_effect = query_side_effect

        # Execute test
        result = await mock_policy_service.get_policy_claims_history(
            policy_id=1,
            user_id=test_user["user_id"],
            status_filter=["open"]
        )

        # Verify results
        assert result["policy_id"] == 1
        assert len(result["claims"]) == 1
        assert result["total_claims"] == 1
        assert result["status_filter"] == ["open"]

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    @patch('app.services.policy_service.validate_policy_number')
    @patch('app.services.policy_service.validate_ssn')
    async def test_validate_policy_data(
        self,
        mock_validate_ssn,
        mock_validate_policy_number,
        mock_log_action,
        mock_policy_service,
        test_user
    ):
        """Test policy data validation."""
        mock_log_action.return_value = None
        mock_validate_policy_number.return_value = None
        mock_validate_ssn.return_value = None

        # Setup no existing policy
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        mock_policy_service.db.query.return_value = mock_query

        # Test valid policy data
        valid_data = {
            "policy_number": "POL-2024-001",
            "policy_type": "auto",
            "effective_date": "2024-01-01",
            "expiration_date": "2024-12-31",
            "insured_first_name": "John",
            "insured_last_name": "Doe",
            "address_line1": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "ssn": "123-45-6789"
        }

        # Execute test
        result = await mock_policy_service.validate_policy_data(
            policy_data=valid_data,
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_validate_policy_data_invalid(
        self,
        mock_log_action,
        mock_policy_service,
        test_user
    ):
        """Test policy data validation with invalid data."""
        mock_log_action.return_value = None

        # Test invalid policy data (missing required fields)
        invalid_data = {
            "policy_number": "",  # Empty required field
            "effective_date": "2024-12-31",  # After expiration
            "expiration_date": "2024-01-01"
        }

        # Execute test
        result = await mock_policy_service.validate_policy_data(
            policy_data=invalid_data,
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    @patch('app.services.policy_service.log_action')
    async def test_bulk_update_search_vectors(
        self,
        mock_log_action,
        mock_policy_service,
        test_user
    ):
        """Test bulk search vector update."""
        mock_log_action.return_value = None

        # Setup mock policies
        mock_policy1 = Mock()
        mock_policy1.update_search_vector = Mock()
        mock_policy2 = Mock()
        mock_policy2.update_search_vector = Mock()

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_policy1, mock_policy2]

        mock_policy_service.db.query.return_value = mock_query
        mock_policy_service.db.commit = Mock()

        # Execute test
        result = await mock_policy_service.bulk_update_search_vectors(
            user_id=test_user["user_id"]
        )

        # Verify results
        assert result["success"] is True
        assert result["updated_count"] == 2
        mock_policy1.update_search_vector.assert_called_once()
        mock_policy2.update_search_vector.assert_called_once()
        mock_policy_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_policies_database_error(
        self,
        mock_policy_service,
        search_request,
        test_user
    ):
        """Test policy search with database error."""
        # Setup mock to raise SQLAlchemy error
        mock_policy_service.db.query.side_effect = Exception("Database connection error")

        # Execute test and expect exception
        with pytest.raises(Exception, match="Policy search failed"):
            await mock_policy_service.search_policies(
                criteria=search_request,
                user_id=test_user["user_id"]
            )