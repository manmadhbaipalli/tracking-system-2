"""Circuit breaker utilities for fault tolerance."""

import asyncio
from functools import wraps
from typing import Callable, Any, Optional, Type, Union
from circuitbreaker import CircuitBreaker
from app.config import settings
from app.core.logging import get_logger

logger = get_logger("app.circuit_breaker")


class AsyncCircuitBreaker:
    """Async-compatible circuit breaker wrapper."""

    def __init__(
        self,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        expected_exception: Optional[Union[Type[Exception], tuple]] = None,
        name: str = "default"
    ):
        """
        Initialize async circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying to close circuit
            expected_exception: Expected exception types that trigger circuit opening
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.recovery_timeout = recovery_timeout or settings.circuit_breaker_recovery_timeout
        self.expected_exception = expected_exception or Exception
        self.name = name

        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self.failure_threshold,
            recovery_timeout=self.recovery_timeout,
            expected_exception=self.expected_exception,
            name=self.name
        )

        # Add state change listeners
        self._circuit_breaker.add_listener(self._on_circuit_open)
        self._circuit_breaker.add_listener(self._on_circuit_close)
        self._circuit_breaker.add_listener(self._on_circuit_half_open)

    def _on_circuit_open(self, prev_state, new_state, name):
        """Called when circuit opens."""
        if new_state == "open":
            logger.warning(f"Circuit breaker '{name}' opened - too many failures")

    def _on_circuit_close(self, prev_state, new_state, name):
        """Called when circuit closes."""
        if new_state == "closed":
            logger.info(f"Circuit breaker '{name}' closed - service recovered")

    def _on_circuit_half_open(self, prev_state, new_state, name):
        """Called when circuit becomes half-open."""
        if new_state == "half-open":
            logger.info(f"Circuit breaker '{name}' half-open - testing service")

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    # Use circuit breaker for async function
                    result = await asyncio.to_thread(
                        lambda: self._circuit_breaker(lambda: asyncio.run(func(*args, **kwargs)))()
                    )
                    return result
                except Exception as e:
                    logger.error(
                        f"Circuit breaker '{self.name}' caught exception in {func.__name__}",
                        extra={"error": str(e), "function": func.__name__}
                    )
                    raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return self._circuit_breaker(func)(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        f"Circuit breaker '{self.name}' caught exception in {func.__name__}",
                        extra={"error": str(e), "function": func.__name__}
                    )
                    raise
            return sync_wrapper

    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        return self._circuit_breaker.current_state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._circuit_breaker.failure_count

    def reset(self):
        """Reset circuit breaker to closed state."""
        self._circuit_breaker.reset()
        logger.info(f"Circuit breaker '{self.name}' manually reset")


# Predefined circuit breakers for common use cases
database_circuit_breaker = AsyncCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=(Exception,),
    name="database"
)

external_api_circuit_breaker = AsyncCircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60,
    expected_exception=(Exception,),
    name="external_api"
)

email_service_circuit_breaker = AsyncCircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=(Exception,),
    name="email_service"
)


# Convenience decorators
def with_database_circuit_breaker(func: Callable) -> Callable:
    """Decorator to add database circuit breaker protection."""
    return database_circuit_breaker(func)


def with_external_api_circuit_breaker(func: Callable) -> Callable:
    """Decorator to add external API circuit breaker protection."""
    return external_api_circuit_breaker(func)


def with_email_service_circuit_breaker(func: Callable) -> Callable:
    """Decorator to add email service circuit breaker protection."""
    return email_service_circuit_breaker(func)


def circuit_breaker(
    failure_threshold: int = None,
    recovery_timeout: int = None,
    expected_exception: Optional[Union[Type[Exception], tuple]] = None,
    name: str = None
) -> Callable:
    """
    Decorator factory for creating custom circuit breakers.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before trying to close circuit
        expected_exception: Expected exception types that trigger circuit opening
        name: Circuit breaker name for logging

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        cb = AsyncCircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=breaker_name
        )
        return cb(func)
    return decorator


def get_circuit_breaker_status() -> dict:
    """Get status of all circuit breakers."""
    return {
        "database": {
            "state": database_circuit_breaker.state,
            "failure_count": database_circuit_breaker.failure_count,
        },
        "external_api": {
            "state": external_api_circuit_breaker.state,
            "failure_count": external_api_circuit_breaker.failure_count,
        },
        "email_service": {
            "state": email_service_circuit_breaker.state,
            "failure_count": email_service_circuit_breaker.failure_count,
        },
    }