"""Circuit breaker implementation for external calls and unstable operations."""

import time
from typing import Any, Callable, Dict, Optional, Type, Union
from functools import wraps
from circuitbreaker import CircuitBreaker, CircuitBreakerError as CBError

from app.core.config import settings
from app.core.exceptions import CircuitBreakerError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AppCircuitBreaker:
    """Application-specific circuit breaker wrapper."""

    def __init__(
        self,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        expected_exception: Union[Type[Exception], tuple] = None,
        name: str = "default",
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception types that trigger the circuit breaker
            name: Name for this circuit breaker instance
        """
        self.name = name
        self.failure_threshold = failure_threshold or settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self.recovery_timeout = recovery_timeout or settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        self.expected_exception = expected_exception or settings.CIRCUIT_BREAKER_EXPECTED_EXCEPTION

        # Create circuit breaker instance
        self.breaker = CircuitBreaker(
            failure_threshold=self.failure_threshold,
            recovery_timeout=self.recovery_timeout,
            expected_exception=self.expected_exception,
        )

        # Metrics
        self.metrics = {
            "total_calls": 0,
            "failed_calls": 0,
            "successful_calls": 0,
            "circuit_open_count": 0,
            "last_failure_time": None,
            "last_success_time": None,
        }

        logger.info(
            f"Circuit breaker '{self.name}' initialized",
            extra={
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "expected_exception": str(self.expected_exception),
            },
        )

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker.

        Args:
            func: Function to wrap

        Returns:
            Wrapped function
        """
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self._execute_with_breaker(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return self._execute_with_breaker_sync(func, *args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    async def _execute_with_breaker(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        try:
            self.metrics["total_calls"] += 1

            # Check if circuit is open
            if self.breaker.current_state == "open":
                self.metrics["circuit_open_count"] += 1
                logger.warning(
                    f"Circuit breaker '{self.name}' is open, rejecting call",
                    extra={"function": func.__name__},
                )
                raise CircuitBreakerError(
                    f"Service temporarily unavailable (circuit breaker '{self.name}' open)"
                )

            # Execute function
            result = await func(*args, **kwargs)

            # Record success
            self.metrics["successful_calls"] += 1
            self.metrics["last_success_time"] = time.time()

            logger.debug(
                f"Circuit breaker '{self.name}' call succeeded",
                extra={"function": func.__name__},
            )

            return result

        except CBError:
            # Circuit breaker is open
            self.metrics["circuit_open_count"] += 1
            raise CircuitBreakerError(
                f"Service temporarily unavailable (circuit breaker '{self.name}' open)"
            )
        except Exception as e:
            # Record failure
            self.metrics["failed_calls"] += 1
            self.metrics["last_failure_time"] = time.time()

            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure",
                extra={
                    "function": func.__name__,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            # Re-raise the original exception
            raise

    def _execute_with_breaker_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Execute sync function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        try:
            self.metrics["total_calls"] += 1

            # Use the circuit breaker directly for sync functions
            result = self.breaker(func)(*args, **kwargs)

            # Record success
            self.metrics["successful_calls"] += 1
            self.metrics["last_success_time"] = time.time()

            logger.debug(
                f"Circuit breaker '{self.name}' call succeeded",
                extra={"function": func.__name__},
            )

            return result

        except CBError:
            # Circuit breaker is open
            self.metrics["circuit_open_count"] += 1
            raise CircuitBreakerError(
                f"Service temporarily unavailable (circuit breaker '{self.name}' open)"
            )
        except Exception as e:
            # Record failure
            self.metrics["failed_calls"] += 1
            self.metrics["last_failure_time"] = time.time()

            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure",
                extra={
                    "function": func.__name__,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            # Re-raise the original exception
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics.

        Returns:
            Dictionary with metrics data
        """
        return {
            **self.metrics,
            "current_state": self.breaker.current_state,
            "failure_count": self.breaker.fail_counter,
            "name": self.name,
        }

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self.breaker.reset()
        logger.info(f"Circuit breaker '{self.name}' has been reset")


# Pre-configured circuit breakers for common use cases
external_api_breaker = AppCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    name="external_api",
)

database_breaker = AppCircuitBreaker(
    failure_threshold=10,
    recovery_timeout=60,
    name="database",
)

# Convenience decorator functions
def circuit_breaker(
    failure_threshold: int = None,
    recovery_timeout: int = None,
    expected_exception: Union[Type[Exception], tuple] = None,
    name: str = None,
):
    """Decorator factory for circuit breaker.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time in seconds before attempting recovery
        expected_exception: Exception types that trigger the circuit breaker
        name: Name for this circuit breaker instance

    Returns:
        Circuit breaker decorator
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        breaker = AppCircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=breaker_name,
        )
        return breaker(func)

    return decorator


# Example usage decorators
external_api = external_api_breaker
database_operation = database_breaker