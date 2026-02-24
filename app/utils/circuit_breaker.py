"""
Enhanced circuit breaker utilities with configuration and monitoring.

Provides:
- Configurable circuit breakers for external services
- Circuit breaker state monitoring
- Automatic recovery and health checks
- Integration with logging system
"""

from typing import Callable, Any, Optional, Dict
from functools import wraps
import asyncio
from datetime import datetime, timedelta

from circuitbreaker import circuit, CircuitBreakerError
import structlog

from app.core.config import settings
from app.utils.logging import get_logger, log_external_service_call

logger = get_logger(__name__)


class EnhancedCircuitBreaker:
    """Enhanced circuit breaker with monitoring and configuration."""

    def __init__(
        self,
        name: str,
        failure_threshold: Optional[int] = None,
        reset_timeout: Optional[int] = None,
        half_open_max_calls: Optional[int] = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold or settings.integrations.circuit_breaker_failure_threshold
        self.reset_timeout = reset_timeout or settings.integrations.circuit_breaker_reset_timeout
        self.half_open_max_calls = half_open_max_calls or settings.integrations.circuit_breaker_half_open_max_calls

        # Circuit breaker state tracking
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""

        @circuit(
            failure_threshold=self.failure_threshold,
            recovery_timeout=self.reset_timeout,
            name=self.name
        )
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()

            try:
                result = await func(*args, **kwargs)

                # Log successful call
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(
                    "Circuit breaker call succeeded",
                    circuit_breaker_name=self.name,
                    duration_seconds=duration
                )

                return result

            except CircuitBreakerError as e:
                logger.error(
                    "Circuit breaker is open",
                    circuit_breaker_name=self.name,
                    error=str(e)
                )
                raise

            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    "Circuit breaker call failed",
                    circuit_breaker_name=self.name,
                    error=str(e),
                    duration_seconds=duration
                )
                raise

        return wrapper

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "reset_timeout": self.reset_timeout,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


# Pre-configured circuit breakers for different services
stripe_circuit_breaker = EnhancedCircuitBreaker("stripe_service", failure_threshold=3, reset_timeout=30)
banking_circuit_breaker = EnhancedCircuitBreaker("banking_service", failure_threshold=5, reset_timeout=60)
edi_circuit_breaker = EnhancedCircuitBreaker("edi_service", failure_threshold=3, reset_timeout=45)
xactimate_circuit_breaker = EnhancedCircuitBreaker("xactimate_service", failure_threshold=3, reset_timeout=60)
database_circuit_breaker = EnhancedCircuitBreaker("database", failure_threshold=10, reset_timeout=30)


class RetryWithCircuitBreaker:
    """Combine retry logic with circuit breaker pattern."""

    def __init__(
        self,
        service_name: str,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        base_delay: Optional[float] = None,
        circuit_breaker: Optional[EnhancedCircuitBreaker] = None
    ):
        self.service_name = service_name
        self.max_retries = max_retries or settings.integrations.max_retry_attempts
        self.backoff_factor = backoff_factor or settings.integrations.retry_backoff_factor
        self.base_delay = base_delay or settings.integrations.retry_base_delay
        self.circuit_breaker = circuit_breaker

    def __call__(self, func: Callable) -> Callable:
        """Decorator that adds retry logic with circuit breaker."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    # Apply circuit breaker if configured
                    if self.circuit_breaker:
                        wrapped_func = self.circuit_breaker(func)
                        return await wrapped_func(*args, **kwargs)
                    else:
                        return await func(*args, **kwargs)

                except CircuitBreakerError:
                    # Circuit breaker is open, don't retry
                    logger.error(
                        "Circuit breaker is open, not retrying",
                        service_name=self.service_name,
                        attempt=attempt + 1
                    )
                    raise

                except Exception as e:
                    last_exception = e

                    if attempt < self.max_retries:
                        delay = self.base_delay * (self.backoff_factor ** attempt)

                        logger.warning(
                            "Retrying after failure",
                            service_name=self.service_name,
                            attempt=attempt + 1,
                            max_retries=self.max_retries,
                            retry_delay=delay,
                            error=str(e)
                        )

                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "All retry attempts failed",
                            service_name=self.service_name,
                            max_retries=self.max_retries,
                            final_error=str(e)
                        )

            # Re-raise the last exception if all retries failed
            raise last_exception

        return wrapper


# Circuit breaker health check
async def check_circuit_breaker_health() -> Dict[str, Any]:
    """Check the health status of all circuit breakers."""
    circuit_breakers = [
        stripe_circuit_breaker,
        banking_circuit_breaker,
        edi_circuit_breaker,
        xactimate_circuit_breaker,
        database_circuit_breaker
    ]

    health_status = {
        "healthy": True,
        "circuit_breakers": []
    }

    for cb in circuit_breakers:
        state = cb.get_state()
        health_status["circuit_breakers"].append(state)

        if state["state"] == "OPEN":
            health_status["healthy"] = False

    return health_status


# Decorator shortcuts for common services
def with_stripe_circuit_breaker(func: Callable) -> Callable:
    """Apply Stripe circuit breaker to function."""
    return stripe_circuit_breaker(func)


def with_banking_circuit_breaker(func: Callable) -> Callable:
    """Apply banking circuit breaker to function."""
    return banking_circuit_breaker(func)


def with_edi_circuit_breaker(func: Callable) -> Callable:
    """Apply EDI circuit breaker to function."""
    return edi_circuit_breaker(func)


def with_xactimate_circuit_breaker(func: Callable) -> Callable:
    """Apply Xactimate circuit breaker to function."""
    return xactimate_circuit_breaker(func)


def with_database_circuit_breaker(func: Callable) -> Callable:
    """Apply database circuit breaker to function."""
    return database_circuit_breaker(func)