"""Tests for circuit breaker module."""

import pytest
import asyncio
from app.circuit_breaker.breaker import create_breaker, breaker_decorator
from app.utils.exceptions import ExternalServiceError


class TestCircuitBreakerCreation:
    """Tests for circuit breaker creation."""

    def test_create_breaker_returns_breaker(self):
        """Test that create_breaker returns a CircuitBreaker instance."""
        breaker = create_breaker("test_breaker")
        assert breaker is not None
        assert breaker.name == "test_breaker"

    def test_create_breaker_with_custom_params(self):
        """Test creating breaker with custom parameters."""
        breaker = create_breaker(
            "test_breaker",
            fail_max=10,
            reset_timeout=120,
        )
        assert breaker.fail_max == 10
        assert breaker.reset_timeout == 120

    def test_create_breaker_default_params(self):
        """Test breaker with default parameters."""
        breaker = create_breaker("test_breaker")
        assert breaker.fail_max == 5
        assert breaker.reset_timeout == 60


class TestCircuitBreakerStates:
    """Tests for circuit breaker state management."""

    @pytest.mark.asyncio
    async def test_breaker_closed_on_success(self):
        """Test breaker stays closed on successful call."""
        breaker = create_breaker("test_breaker")

        @breaker_decorator(breaker)
        async def successful_call():
            return "success"

        result = await successful_call()
        assert result == "success"
        assert breaker.current_state == "closed"

    @pytest.mark.asyncio
    async def test_breaker_opens_after_threshold(self):
        """Test breaker opens after exceeding fail_max."""
        breaker = create_breaker("test_breaker", fail_max=3)

        @breaker_decorator(breaker)
        async def failing_call():
            raise Exception("Service unavailable")

        for _ in range(3):
            with pytest.raises(Exception):
                await failing_call()

        assert breaker.current_state == "open"

    @pytest.mark.asyncio
    async def test_breaker_fail_fast_when_open(self):
        """Test breaker fails fast when open."""
        breaker = create_breaker("test_breaker", fail_max=1)

        @breaker_decorator(breaker)
        async def failing_call():
            raise Exception("Service error")

        with pytest.raises(Exception):
            await failing_call()

        assert breaker.current_state == "open"

        with pytest.raises(ExternalServiceError):
            await failing_call()

    @pytest.mark.asyncio
    async def test_breaker_half_open_state(self):
        """Test breaker enters half-open state after timeout."""
        breaker = create_breaker(
            "test_breaker",
            fail_max=1,
            reset_timeout=1,
        )

        @breaker_decorator(breaker)
        async def failing_call():
            raise Exception("Service error")

        with pytest.raises(Exception):
            await failing_call()

        assert breaker.current_state == "open"

        await asyncio.sleep(1.1)

        @breaker_decorator(breaker)
        async def successful_call():
            return "recovered"

        result = await successful_call()
        assert result == "recovered"
        assert breaker.current_state == "closed"


class TestBreakerDecorator:
    """Tests for breaker decorator."""

    @pytest.mark.asyncio
    async def test_decorator_applies_to_async_function(self):
        """Test breaker decorator on async functions."""
        breaker = create_breaker("test_breaker")

        @breaker_decorator(breaker)
        async def async_function(x):
            return x * 2

        result = await async_function(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_decorator_raises_external_service_error_when_open(self):
        """Test decorator raises ExternalServiceError when breaker open."""
        breaker = create_breaker("test_breaker", fail_max=1)

        @breaker_decorator(breaker)
        async def failing_function():
            raise Exception("Service error")

        with pytest.raises(Exception):
            await failing_function()

        assert breaker.current_state == "open"

        with pytest.raises(ExternalServiceError):
            await failing_function()

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves function metadata."""
        breaker = create_breaker("test_breaker")

        @breaker_decorator(breaker)
        async def documented_function():
            """This is a documented function."""
            pass

        assert documented_function.__doc__ == "This is a documented function."
        assert documented_function.__name__ == "documented_function"
