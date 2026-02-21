"""Circuit breaker wrapper around pybreaker."""

import functools
from pybreaker import CircuitBreaker
from app.utils.exceptions import ExternalServiceError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AsyncCircuitBreaker:
    """Wrapper around pybreaker to support async operations."""

    def __init__(
        self,
        name: str,
        fail_max: int = 5,
        reset_timeout: int = 60,
    ):
        """Initialize async circuit breaker.

        Args:
            name: Breaker name for logging
            fail_max: Number of failures before opening circuit
            reset_timeout: Seconds before attempting half-open
        """
        self._breaker = CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            name=name,
        )

    def __getattr__(self, name):
        """Delegate attribute access to wrapped breaker."""
        return getattr(self._breaker, name)

    async def call(self, func, *args, **kwargs):
        """Call async function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            ExternalServiceError: If circuit is open
        """
        # Use pybreaker's call_async which properly tracks failures
        return await self._breaker.call_async(func, *args, **kwargs)


def create_breaker(
    name: str,
    fail_max: int = 5,
    reset_timeout: int = 60,
    **kwargs
) -> AsyncCircuitBreaker:
    """Create a circuit breaker instance.

    Args:
        name: Breaker name for logging
        fail_max: Number of failures before opening circuit
        reset_timeout: Seconds before attempting half-open
        **kwargs: Additional arguments (ignored for compatibility)

    Returns:
        AsyncCircuitBreaker instance
    """
    return AsyncCircuitBreaker(name, fail_max, reset_timeout)


def breaker_decorator(breaker):
    """Decorator to apply circuit breaker to async functions.

    Args:
        breaker: AsyncCircuitBreaker instance

    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        return async_wrapper
    return decorator
