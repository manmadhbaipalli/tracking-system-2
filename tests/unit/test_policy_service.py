"""
Test policy service business logic.
"""

import pytest
import pytest_asyncio
from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.services.policy_service import PolicyService
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicySearchRequest
from app.models.policy import Policy
from app.utils.exceptions import NotFoundError, ValidationError


class TestPolicyService:
    """Test policy service methods."""

    @pytest_asyncio.fixture
    async def policy_service(self, test_db):
        """Create policy service instance."""
        return PolicyService(test_db)

    @pytest_asyncio.fixture
    async def sample_policy_data(self):
        """Create sample policy data."""
        return PolicyCreate(
            policy_number="TEST-001",
            policy_type="AUTO",
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31),
            insured_first_name="John",
            insured_last_name="Doe",
            policy_address="123 Main St",
            policy_city="Boston",
            policy_state="MA",
            policy_zip="02101",
            premium_amount=Decimal("1200.00"),
            deductible_amount=Decimal("500.00")
        )

    @pytest_asyncio.async_test
    async def test_create_policy_success(self, policy_service, sample_policy_data, test_db):
        """Test successful policy creation."""
        user_id = uuid4()

        policy = await policy_service.create_policy(sample_policy_data, user_id)

        assert policy.policy_number == "TEST-001"
        assert policy.policy_type == "AUTO"
        assert policy.insured_first_name == "John"
        assert policy.insured_last_name == "Doe"
        assert policy.policy_city == "Boston"
        assert policy.policy_state == "MA"
        assert policy.created_by == user_id
        assert policy.updated_by == user_id

    @pytest_asyncio.async_test
    async def test_create_policy_duplicate_number(self, policy_service, sample_policy_data, test_db):
        """Test policy creation with duplicate policy number."""
        user_id = uuid4()

        # Create first policy
        await policy_service.create_policy(sample_policy_data, user_id)

        # Try to create duplicate
        with pytest.raises(ValidationError) as exc_info:
            await policy_service.create_policy(sample_policy_data, user_id)

        assert "already exists" in str(exc_info.value)

    @pytest_asyncio.async_test
    async def test_create_policy_with_ssn(self, policy_service, sample_policy_data):
        """Test policy creation with SSN encryption."""
        user_id = uuid4()
        sample_policy_data.ssn_tin = "123-45-6789"

        with patch('app.utils.security.encrypt_data') as mock_encrypt, \
             patch('app.utils.security.hash_ssn_tin') as mock_hash:

            mock_encrypt.return_value = "encrypted_ssn"
            mock_hash.return_value = "hashed_ssn"

            policy = await policy_service.create_policy(sample_policy_data, user_id)

            mock_encrypt.assert_called_once_with("123-45-6789")
            mock_hash.assert_called_once_with("123-45-6789")

    @pytest_asyncio.async_test
    async def test_get_policy_exists(self, policy_service, sample_policy_data):
        """Test retrieving an existing policy."""
        user_id = uuid4()
        created_policy = await policy_service.create_policy(sample_policy_data, user_id)

        policy = await policy_service.get_policy(created_policy.id)

        assert policy is not None
        assert policy.id == created_policy.id
        assert policy.policy_number == "TEST-001"

    @pytest_asyncio.async_test
    async def test_get_policy_not_exists(self, policy_service):
        """Test retrieving a non-existent policy."""
        non_existent_id = uuid4()

        policy = await policy_service.get_policy(non_existent_id)

        assert policy is None

    @pytest_asyncio.async_test
    async def test_get_policy_by_number(self, policy_service, sample_policy_data):
        """Test retrieving policy by number."""
        user_id = uuid4()
        await policy_service.create_policy(sample_policy_data, user_id)

        policy = await policy_service.get_policy_by_number("TEST-001")

        assert policy is not None
        assert policy.policy_number == "TEST-001"

    @pytest_asyncio.async_test
    async def test_update_policy_success(self, policy_service, sample_policy_data):
        """Test successful policy update."""
        user_id = uuid4()
        created_policy = await policy_service.create_policy(sample_policy_data, user_id)

        update_data = PolicyUpdate(
            policy_city="Cambridge",
            policy_state="MA",
            premium_amount=Decimal("1300.00")
        )

        updated_policy = await policy_service.update_policy(created_policy.id, update_data, user_id)

        assert updated_policy.policy_city == "Cambridge"
        assert updated_policy.premium_amount == Decimal("1300.00")
        assert updated_policy.updated_by == user_id

    @pytest_asyncio.async_test
    async def test_update_policy_not_found(self, policy_service):
        """Test updating non-existent policy."""
        non_existent_id = uuid4()
        user_id = uuid4()

        update_data = PolicyUpdate(policy_city="Cambridge")

        with pytest.raises(NotFoundError):
            await policy_service.update_policy(non_existent_id, update_data, user_id)

    @pytest_asyncio.async_test
    async def test_delete_policy_success(self, policy_service, sample_policy_data):
        """Test successful policy deletion."""
        user_id = uuid4()
        created_policy = await policy_service.create_policy(sample_policy_data, user_id)

        result = await policy_service.delete_policy(created_policy.id, user_id)

        assert result is True

        # Verify policy is marked as deleted
        deleted_policy = await policy_service.get_policy(created_policy.id)
        assert deleted_policy.policy_status == "DELETED"

    @pytest_asyncio.async_test
    async def test_delete_policy_with_active_claims(self, policy_service, sample_policy_data):
        """Test policy deletion with active claims."""
        user_id = uuid4()
        created_policy = await policy_service.create_policy(sample_policy_data, user_id)

        # Mock the count query to return active claims
        with patch.object(policy_service.db, 'execute') as mock_execute:
            # Mock the count result
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 1  # Has active claims
            mock_execute.return_value = mock_result

            with pytest.raises(ValidationError) as exc_info:
                await policy_service.delete_policy(created_policy.id, user_id)

            assert "active claims" in str(exc_info.value)

    @pytest_asyncio.async_test
    async def test_search_policies_by_policy_number(self, policy_service, sample_policy_data):
        """Test policy search by policy number."""
        user_id = uuid4()
        await policy_service.create_policy(sample_policy_data, user_id)

        search_request = PolicySearchRequest(
            policy_number="TEST-001",
            page=1,
            limit=10
        )

        result = await policy_service.search_policies(search_request, user_id)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].policy_number == "TEST-001"
        assert result.search_time_ms > 0

    @pytest_asyncio.async_test
    async def test_search_policies_by_name(self, policy_service, sample_policy_data):
        """Test policy search by insured name."""
        user_id = uuid4()
        await policy_service.create_policy(sample_policy_data, user_id)

        search_request = PolicySearchRequest(
            insured_first_name="John",
            insured_last_name="Doe",
            page=1,
            limit=10
        )

        result = await policy_service.search_policies(search_request, user_id)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].insured_name == "John Doe"

    @pytest_asyncio.async_test
    async def test_search_policies_by_location(self, policy_service, sample_policy_data):
        """Test policy search by location criteria."""
        user_id = uuid4()
        await policy_service.create_policy(sample_policy_data, user_id)

        search_request = PolicySearchRequest(
            policy_city="Boston",
            policy_state="MA",
            policy_zip="02101",
            page=1,
            limit=10
        )

        result = await policy_service.search_policies(search_request, user_id)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].policy_city == "Boston"
        assert result.items[0].policy_state == "MA"

    @pytest_asyncio.async_test
    async def test_search_policies_with_sorting(self, policy_service):
        """Test policy search with sorting options."""
        user_id = uuid4()

        # Create multiple policies
        for i in range(3):
            policy_data = PolicyCreate(
                policy_number=f"TEST-00{i+1}",
                policy_type="AUTO",
                effective_date=date(2024, 1, 1),
                expiration_date=date(2024, 12, 31),
                insured_first_name="John",
                insured_last_name=f"Doe{i+1}",
                policy_city="Boston",
                policy_state="MA",
                policy_zip="02101",
                premium_amount=Decimal("1200.00")
            )
            await policy_service.create_policy(policy_data, user_id)

        # Test ascending sort
        search_request = PolicySearchRequest(
            sort_by="policy_number",
            sort_order="asc",
            page=1,
            limit=10
        )

        result = await policy_service.search_policies(search_request, user_id)

        assert result.total_count == 3
        assert result.items[0].policy_number == "TEST-001"
        assert result.items[1].policy_number == "TEST-002"

    @pytest_asyncio.async_test
    async def test_search_policies_pagination(self, policy_service):
        """Test policy search pagination."""
        user_id = uuid4()

        # Create multiple policies
        for i in range(5):
            policy_data = PolicyCreate(
                policy_number=f"PAGE-00{i+1}",
                policy_type="AUTO",
                effective_date=date(2024, 1, 1),
                expiration_date=date(2024, 12, 31),
                insured_first_name="Jane",
                insured_last_name=f"Smith{i+1}",
                policy_city="Boston",
                policy_state="MA",
                policy_zip="02101",
                premium_amount=Decimal("1200.00")
            )
            await policy_service.create_policy(policy_data, user_id)

        # Test first page
        search_request = PolicySearchRequest(
            insured_first_name="Jane",
            page=1,
            limit=2
        )

        result = await policy_service.search_policies(search_request, user_id)

        assert result.total_count == 5
        assert len(result.items) == 2
        assert result.has_next is True
        assert result.has_previous is False

        # Test second page
        search_request.page = 2
        result = await policy_service.search_policies(search_request, user_id)

        assert len(result.items) == 2
        assert result.has_previous is True

    @pytest_asyncio.async_test
    async def test_list_policies(self, policy_service, sample_policy_data):
        """Test policy listing with pagination."""
        user_id = uuid4()
        await policy_service.create_policy(sample_policy_data, user_id)

        policies, total_count = await policy_service.list_policies(skip=0, limit=10)

        assert total_count == 1
        assert len(policies) == 1
        assert policies[0].policy_number == "TEST-001"

    @pytest_asyncio.async_test
    async def test_search_performance_tracking(self, policy_service, sample_policy_data):
        """Test that search performance is tracked."""
        user_id = uuid4()
        await policy_service.create_policy(sample_policy_data, user_id)

        search_request = PolicySearchRequest(
            policy_number="TEST-001",
            page=1,
            limit=10
        )

        with patch('app.utils.audit.audit_log') as mock_audit:
            result = await policy_service.search_policies(search_request, user_id)

            # Verify audit was called for search tracking
            mock_audit.assert_called()
            call_args = mock_audit.call_args[1]
            assert call_args['action'] == "POLICY_SEARCH"
            assert call_args['entity_type'] == "Policy"
            assert 'search_time_ms' in call_args['new_values']