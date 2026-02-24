import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Any, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "CLOSED"        # Normal operation
    OPEN = "OPEN"            # Failing, reject calls
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreakerOpenException(Exception):
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker is OPEN for service: {service_name}")


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Too many failures, calls rejected immediately
    - HALF_OPEN: Testing recovery, limited calls allowed
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def _transition_to_open(self) -> None:
        self._state = CircuitState.OPEN
        self._last_failure_time = time.monotonic()
        logger.warning("Circuit breaker '%s' transitioned to OPEN state", self.name)

    async def _transition_to_half_open(self) -> None:
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._failure_count = 0
        logger.info("Circuit breaker '%s' transitioned to HALF_OPEN state", self.name)

    async def _transition_to_closed(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        logger.info("Circuit breaker '%s' transitioned to CLOSED state", self.name)

    async def _check_state_transition(self) -> None:
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                await self._transition_to_half_open()

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function with circuit breaker protection."""
        await self._check_state_transition()

        if self._state == CircuitState.OPEN:
            raise CircuitBreakerOpenException(self.name)

        if self._state == CircuitState.HALF_OPEN:
            async with self._lock:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenException(self.name)
                self._half_open_calls += 1

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result
        except CircuitBreakerOpenException:
            raise
        except Exception as exc:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            async with self._lock:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    await self._transition_to_closed()
        elif self._state == CircuitState.CLOSED:
            async with self._lock:
                self._failure_count = 0

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            logger.warning(
                "Circuit breaker '%s' failure count: %d/%d",
                self.name,
                self._failure_count,
                self.failure_threshold,
            )
            if self._failure_count >= self.failure_threshold:
                await self._transition_to_open()

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self._last_failure_time,
        }


_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    half_open_max_calls: int = 3,
) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
        )
    return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return _circuit_breakers
