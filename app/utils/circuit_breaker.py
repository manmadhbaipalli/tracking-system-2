"""Circuit breaker implementation for external service calls"""
from functools import wraps
from typing import Any, Callable, Type
import logging
from circuitbreaker import circuit

from ..config import settings

logger = logging.getLogger(__name__)


class CircuitBreakerConfig:
    """Circuit breaker configuration wrapper"""

    def __init__(
        self,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        expected_exception: Type[Exception] = None
    ):
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.recovery_timeout = recovery_timeout or settings.circuit_breaker_recovery_timeout
        self.expected_exception = expected_exception or Exception


def circuit_breaker(
    failure_threshold: int = None,
    recovery_timeout: int = None,
    expected_exception: Type[Exception] = None
) -> Callable:
    """
    Circuit breaker decorator for external service calls.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type that triggers circuit breaker

    Returns:
        Callable: Decorated function with circuit breaker protection
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception
    )

    def decorator(func: Callable) -> Callable:
        # Use the circuitbreaker library decorator
        circuit_protected = circuit(
            failure_threshold=config.failure_threshold,
            recovery_timeout=config.recovery_timeout,
            expected_exception=config.expected_exception
        )(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            """Async wrapper for circuit breaker"""
            try:
                if hasattr(circuit_protected, '__call__'):
                    return await circuit_protected(*args, **kwargs)
                else:
                    return circuit_protected
            except Exception as e:
                logger.error(f"Circuit breaker opened for {func.__name__}: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            """Sync wrapper for circuit breaker"""
            try:
                return circuit_protected(*args, **kwargs)
            except Exception as e:
                logger.error(f"Circuit breaker opened for {func.__name__}: {e}")
                raise

        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Pre-configured circuit breakers for common use cases
database_circuit_breaker = circuit_breaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception
)

external_api_circuit_breaker = circuit_breaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)