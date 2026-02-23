"""Circuit breaker implementation for external service calls."""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

from app.config import settings
from app.core.exceptions import CircuitBreakerError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CircuitBreakerState:
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.

    Tracks failures and opens the circuit when failure threshold is reached.
    After recovery timeout, allows one request to test if service is back.
    """

    def __init__(
        self,
        failure_threshold: int,
        recovery_timeout: int,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures to trigger open state
            recovery_timeout: Time to wait before trying half-open state
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Any: Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to half-open")
                else:
                    raise CircuitBreakerError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except self.expected_exception as e:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
                logger.info("Circuit breaker reset to closed state")

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(
                    "Circuit breaker opened",
                    failure_count=self.failure_count,
                    threshold=self.failure_threshold,
                )

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time is not None
            and time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout,
        }


# Global circuit breakers for different operations
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: Optional[int] = None,
    recovery_timeout: Optional[int] = None,
    expected_exception: type = Exception,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker instance.

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures to trigger open state
        recovery_timeout: Time to wait before trying half-open state
        expected_exception: Exception type that counts as failure

    Returns:
        CircuitBreaker: Circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold or settings.circuit_breaker_failure_threshold,
            recovery_timeout=recovery_timeout or settings.circuit_breaker_recovery_timeout,
            expected_exception=expected_exception,
        )
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: Optional[int] = None,
    recovery_timeout: Optional[int] = None,
    expected_exception: type = Exception,
):
    """
    Decorator for applying circuit breaker pattern to functions.

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures to trigger open state
        recovery_timeout: Time to wait before trying half-open state
        expected_exception: Exception type that counts as failure
    """
    def decorator(func: Callable) -> Callable:
        cb = get_circuit_breaker(
            name, failure_threshold, recovery_timeout, expected_exception
        )

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await cb.call(func, *args, **kwargs)

        return wrapper
    return decorator


async def get_all_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """Get states of all circuit breakers."""
    return {name: cb.get_state() for name, cb in _circuit_breakers.items()}


async def reset_circuit_breaker(name: str) -> bool:
    """
    Manually reset a circuit breaker.

    Args:
        name: Circuit breaker name

    Returns:
        bool: True if reset successful, False if breaker doesn't exist
    """
    if name in _circuit_breakers:
        cb = _circuit_breakers[name]
        async with cb._lock:
            cb.failure_count = 0
            cb.last_failure_time = None
            cb.state = CircuitBreakerState.CLOSED
            logger.info(f"Circuit breaker {name} manually reset")
        return True
    return False