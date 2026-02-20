"""Unit tests for circuit breaker implementation."""

import pytest
import time
from app.utils.circuit_breaker import CircuitBreaker, CircuitState
from app.utils.exceptions import CircuitBreakerOpenException


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_successful_call(self):
        """Test successful call in closed state."""
        breaker = CircuitBreaker()

        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_failure_threshold(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3)

        def fail_func():
            raise Exception("Failed")

        # First failure
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.CLOSED

        # Second failure
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.CLOSED

        # Third failure - circuit opens
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.OPEN

    def test_circuit_breaker_open_raises_exception(self):
        """Test that calls fail fast when circuit is open."""
        breaker = CircuitBreaker(failure_threshold=1)

        def fail_func():
            raise Exception("Failed")

        # Trigger opening
        with pytest.raises(Exception):
            breaker.call(fail_func)

        # Now circuit is open
        assert breaker.state == CircuitState.OPEN

        # Subsequent calls fail with CircuitBreakerOpenException
        with pytest.raises(CircuitBreakerOpenException):
            breaker.call(fail_func)

    def test_circuit_breaker_half_open_state(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        def fail_func():
            raise Exception("Failed")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN
        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_half_open_fails(self):
        """Test circuit goes back to OPEN if HALF_OPEN call fails."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        def fail_func():
            raise Exception("Failed")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call in HALF_OPEN fails, should go back to OPEN
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.OPEN

    def test_circuit_breaker_reset(self):
        """Test manual circuit breaker reset."""
        breaker = CircuitBreaker(failure_threshold=1)

        def fail_func():
            raise Exception("Failed")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.OPEN

        # Reset
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_circuit_breaker_failure_count_reset_on_success(self):
        """Test failure count resets on success."""
        breaker = CircuitBreaker(failure_threshold=5)

        def fail_func():
            raise Exception("Failed")

        def success_func():
            return "success"

        # Two failures
        with pytest.raises(Exception):
            breaker.call(fail_func)
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.failure_count == 2

        # Success resets counter
        breaker.call(success_func)
        assert breaker.failure_count == 0

    def test_circuit_breaker_with_custom_exception(self):
        """Test circuit breaker with specific expected exception."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            expected_exception=ValueError
        )

        def raises_value_error():
            raise ValueError("Bad value")

        # First failure
        with pytest.raises(ValueError):
            breaker.call(raises_value_error)

        # Second failure - opens circuit
        with pytest.raises(ValueError):
            breaker.call(raises_value_error)
        assert breaker.state == CircuitState.OPEN

    def test_circuit_breaker_unexpected_exception_not_counted(self):
        """Test that unexpected exceptions don't count as failures."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            expected_exception=ValueError
        )

        def raises_type_error():
            raise TypeError("Wrong type")

        # This exception is not counted
        with pytest.raises(TypeError):
            breaker.call(raises_type_error)

        # Failure count should still be 0
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_concurrent_calls(self):
        """Test circuit breaker is thread-safe."""
        breaker = CircuitBreaker(failure_threshold=3)

        def fail_func():
            raise Exception("Failed")

        import threading

        exceptions_raised = []

        def call_breaker():
            try:
                breaker.call(fail_func)
            except Exception as e:
                exceptions_raised.append(e)

        # Multiple threads calling
        threads = [threading.Thread(target=call_breaker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have exceptions
        assert len(exceptions_raised) >= 3
