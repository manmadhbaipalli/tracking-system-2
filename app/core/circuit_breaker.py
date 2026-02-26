import time
import logging
from typing import Callable, Any, Optional
from app.models.enums import CircuitBreakerState
from app.config import settings

logger = logging.getLogger(__name__)

_registry: dict[str, "CircuitBreaker"] = {}


class CircuitBreaker:
    """Simple in-memory circuit breaker."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = settings.cb_failure_threshold,
        open_duration_seconds: int = settings.cb_open_duration_seconds,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.open_duration_seconds = open_duration_seconds
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self._opened_at: Optional[float] = None
        _registry[name] = self

    def _transition_to_open(self) -> None:
        self.state = CircuitBreakerState.OPEN
        self._opened_at = time.monotonic()
        logger.warning("Circuit breaker '%s' OPENED after %d failures", self.name, self.failure_count)

    def _try_half_open(self) -> bool:
        if self.state == CircuitBreakerState.OPEN:
            elapsed = time.monotonic() - (self._opened_at or 0)
            if elapsed >= self.open_duration_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker '%s' -> HALF_OPEN", self.name)
                return True
        return False

    def is_open(self) -> bool:
        if self.state == CircuitBreakerState.CLOSED:
            return False
        if self.state == CircuitBreakerState.HALF_OPEN:
            return False
        # OPEN — check if we should try HALF_OPEN
        self._try_half_open()
        return self.state == CircuitBreakerState.OPEN

    def record_success(self) -> None:
        self.failure_count = 0
        if self.state != CircuitBreakerState.CLOSED:
            logger.info("Circuit breaker '%s' -> CLOSED (recovered)", self.name)
        self.state = CircuitBreakerState.CLOSED
        self._opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self._transition_to_open()

    async def call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        from app.exceptions import AppException
        if self.is_open():
            raise AppException(
                message=f"Circuit breaker '{self.name}' is OPEN — call rejected",
                error_code="CIRCUIT_OPEN",
                status_code=503,
            )
        try:
            result = await fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:
            self.record_failure()
            raise exc


def get_circuit_breaker(name: str) -> CircuitBreaker:
    if name not in _registry:
        return CircuitBreaker(name=name)
    return _registry[name]


def get_all_states() -> dict[str, str]:
    return {name: cb.state.value for name, cb in _registry.items()}
