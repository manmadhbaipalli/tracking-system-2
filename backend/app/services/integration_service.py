"""
Claims Service Platform - Integration Service

External integration coordinator with circuit breaker pattern
and error handling for third-party services.
"""

from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import random
from sqlalchemy.orm import Session

from app.services.audit_service import log_action
from app.core.config import settings


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class ServiceHealth(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitBreaker:
    """Circuit breaker implementation for external service calls"""

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        timeout_duration: int = 60,
        reset_timeout: int = 300
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.reset_timeout = reset_timeout

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""

        if self.state == CircuitBreakerState.OPEN:
            # Check if we should transition to half-open
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker OPEN for {self.service_name}")

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Success - reset failure count and close circuit
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None

            return result

        except Exception as e:
            # Record failure
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            # Check if we should open the circuit
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN

            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True

        return datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.reset_timeout)

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "service": self.service_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class RetryPolicy:
    """Retry policy with exponential backoff"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier

    async def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""

        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    # Add jitter to delay
                    jittered_delay = delay * (0.5 + random.random() * 0.5)
                    await asyncio.sleep(jittered_delay)

                    # Increase delay for next attempt
                    delay = min(delay * self.backoff_multiplier, self.max_delay)
                else:
                    # Final attempt failed
                    break

        raise last_exception


class IntegrationService:
    """External service integration coordination"""

    def __init__(self, db: Session):
        self.db = db
        self.circuit_breakers = {}
        self.service_health = {}
        self.retry_policies = {}

        # Initialize circuit breakers for known services
        self._initialize_circuit_breakers()

    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for external services"""

        services = [
            "stripe",
            "bank_ach",
            "bank_wire",
            "xactimate",
            "bill_review",
            "general_ledger",
            "document_management"
        ]

        for service in services:
            self.circuit_breakers[service] = CircuitBreaker(
                service_name=service,
                failure_threshold=getattr(settings, f"{service.upper()}_FAILURE_THRESHOLD", 5),
                timeout_duration=getattr(settings, f"{service.upper()}_TIMEOUT", 30),
                reset_timeout=getattr(settings, f"{service.upper()}_RESET_TIMEOUT", 300)
            )

            self.retry_policies[service] = RetryPolicy(
                max_retries=getattr(settings, f"{service.upper()}_MAX_RETRIES", 3),
                initial_delay=getattr(settings, f"{service.upper()}_INITIAL_DELAY", 1.0)
            )

    async def call_external_service(
        self,
        service_name: str,
        operation: str,
        func: Callable,
        user_id: Optional[int] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Call external service with circuit breaker and retry logic"""

        start_time = datetime.utcnow()
        operation_details = {
            "service": service_name,
            "operation": operation,
            "start_time": start_time.isoformat()
        }

        try:
            # Get circuit breaker and retry policy
            circuit_breaker = self.circuit_breakers.get(service_name)
            retry_policy = self.retry_policies.get(service_name, RetryPolicy())

            if not circuit_breaker:
                # Create circuit breaker if it doesn't exist
                circuit_breaker = CircuitBreaker(service_name=service_name)
                self.circuit_breakers[service_name] = circuit_breaker

            # Execute with circuit breaker and retry
            async def execute_operation():
                return await retry_policy.execute_with_retry(func, *args, **kwargs)

            result = await circuit_breaker.call(execute_operation)

            # Record successful operation
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            operation_details.update({
                "status": "success",
                "duration_ms": duration_ms,
                "end_time": end_time.isoformat()
            })

            # Update service health
            self.service_health[service_name] = ServiceHealth.HEALTHY

            # Log successful operation
            if user_id:
                await log_action(
                    self.db,
                    user_id,
                    "external_service_call",
                    entity_type="integration",
                    entity_id=None,
                    details=operation_details
                )

            return {
                "success": True,
                "result": result,
                "service": service_name,
                "operation": operation,
                "duration_ms": duration_ms
            }

        except Exception as e:
            # Record failed operation
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            operation_details.update({
                "status": "failed",
                "error": str(e),
                "duration_ms": duration_ms,
                "end_time": end_time.isoformat()
            })

            # Update service health
            self.service_health[service_name] = ServiceHealth.UNHEALTHY

            # Log failed operation
            if user_id:
                await log_action(
                    self.db,
                    user_id,
                    "external_service_error",
                    entity_type="integration",
                    entity_id=None,
                    details=operation_details
                )

            return {
                "success": False,
                "error": str(e),
                "service": service_name,
                "operation": operation,
                "duration_ms": duration_ms
            }

    async def get_service_health(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get health status of external services"""

        if service_name:
            # Get health for specific service
            circuit_breaker = self.circuit_breakers.get(service_name)
            health_status = self.service_health.get(service_name, ServiceHealth.UNKNOWN)

            return {
                "service": service_name,
                "health": health_status.value,
                "circuit_breaker": circuit_breaker.get_status() if circuit_breaker else None
            }

        # Get health for all services
        services_health = {}
        overall_health = ServiceHealth.HEALTHY

        for service, health in self.service_health.items():
            circuit_breaker = self.circuit_breakers.get(service)

            services_health[service] = {
                "health": health.value,
                "circuit_breaker": circuit_breaker.get_status() if circuit_breaker else None
            }

            # Determine overall health
            if health == ServiceHealth.UNHEALTHY:
                overall_health = ServiceHealth.UNHEALTHY
            elif health == ServiceHealth.DEGRADED and overall_health != ServiceHealth.UNHEALTHY:
                overall_health = ServiceHealth.DEGRADED

        return {
            "overall_health": overall_health.value,
            "services": services_health,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def reset_circuit_breaker(self, service_name: str, user_id: int) -> Dict[str, Any]:
        """Manually reset a circuit breaker"""

        try:
            circuit_breaker = self.circuit_breakers.get(service_name)

            if not circuit_breaker:
                raise ValueError(f"Circuit breaker for service '{service_name}' not found")

            # Reset circuit breaker
            circuit_breaker.failure_count = 0
            circuit_breaker.last_failure_time = None
            circuit_breaker.state = CircuitBreakerState.CLOSED

            # Update service health
            self.service_health[service_name] = ServiceHealth.UNKNOWN

            # Log reset action
            await log_action(
                self.db,
                user_id,
                "circuit_breaker_reset",
                entity_type="integration",
                entity_id=None,
                details={
                    "service": service_name,
                    "reset_time": datetime.utcnow().isoformat()
                }
            )

            return {
                "success": True,
                "service": service_name,
                "message": f"Circuit breaker for {service_name} has been reset"
            }

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "circuit_breaker_reset_error",
                entity_type="integration",
                entity_id=None,
                details={
                    "service": service_name,
                    "error": str(e)
                }
            )
            raise Exception(f"Failed to reset circuit breaker: {str(e)}")

    async def configure_service(
        self,
        service_name: str,
        config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Configure external service integration settings"""

        try:
            # Update circuit breaker configuration
            if service_name in self.circuit_breakers:
                circuit_breaker = self.circuit_breakers[service_name]

                if "failure_threshold" in config:
                    circuit_breaker.failure_threshold = config["failure_threshold"]
                if "timeout_duration" in config:
                    circuit_breaker.timeout_duration = config["timeout_duration"]
                if "reset_timeout" in config:
                    circuit_breaker.reset_timeout = config["reset_timeout"]

            # Update retry policy configuration
            if service_name in self.retry_policies:
                retry_policy = self.retry_policies[service_name]

                if "max_retries" in config:
                    retry_policy.max_retries = config["max_retries"]
                if "initial_delay" in config:
                    retry_policy.initial_delay = config["initial_delay"]
                if "max_delay" in config:
                    retry_policy.max_delay = config["max_delay"]

            # Log configuration change
            await log_action(
                self.db,
                user_id,
                "service_configuration_update",
                entity_type="integration",
                entity_id=None,
                details={
                    "service": service_name,
                    "configuration": config,
                    "update_time": datetime.utcnow().isoformat()
                }
            )

            return {
                "success": True,
                "service": service_name,
                "configuration": config,
                "message": f"Configuration updated for {service_name}"
            }

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "service_configuration_error",
                entity_type="integration",
                entity_id=None,
                details={
                    "service": service_name,
                    "error": str(e)
                }
            )
            raise Exception(f"Failed to configure service: {str(e)}")

    async def test_service_connectivity(self, service_name: str, user_id: int) -> Dict[str, Any]:
        """Test connectivity to an external service"""

        try:
            start_time = datetime.utcnow()

            # Mock connectivity test - in production, implement actual service calls
            async def mock_health_check():
                # Simulate network call
                await asyncio.sleep(0.1)

                # Simulate success/failure based on service health
                current_health = self.service_health.get(service_name, ServiceHealth.UNKNOWN)
                if current_health == ServiceHealth.UNHEALTHY:
                    raise Exception(f"Service {service_name} is not responding")

                return {"status": "healthy", "version": "1.0.0"}

            # Test with circuit breaker
            result = await self.call_external_service(
                service_name,
                "health_check",
                mock_health_check,
                user_id
            )

            end_time = datetime.utcnow()
            response_time_ms = (end_time - start_time).total_seconds() * 1000

            if result["success"]:
                return {
                    "service": service_name,
                    "connectivity": "healthy",
                    "response_time_ms": response_time_ms,
                    "test_time": end_time.isoformat(),
                    "details": result.get("result", {})
                }
            else:
                return {
                    "service": service_name,
                    "connectivity": "unhealthy",
                    "response_time_ms": response_time_ms,
                    "test_time": end_time.isoformat(),
                    "error": result.get("error", "Unknown error")
                }

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "service_connectivity_test_error",
                entity_type="integration",
                entity_id=None,
                details={
                    "service": service_name,
                    "error": str(e)
                }
            )
            raise Exception(f"Connectivity test failed: {str(e)}")

    async def get_integration_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get integration performance and reliability metrics"""

        try:
            metrics = {
                "services": {},
                "overall_metrics": {
                    "total_services": len(self.circuit_breakers),
                    "healthy_services": 0,
                    "degraded_services": 0,
                    "unhealthy_services": 0
                },
                "generated_at": datetime.utcnow().isoformat()
            }

            # Calculate metrics for each service
            for service_name, circuit_breaker in self.circuit_breakers.items():
                health = self.service_health.get(service_name, ServiceHealth.UNKNOWN)

                service_metrics = {
                    "health": health.value,
                    "circuit_breaker_state": circuit_breaker.state.value,
                    "failure_count": circuit_breaker.failure_count,
                    "last_failure": circuit_breaker.last_failure_time.isoformat() if circuit_breaker.last_failure_time else None
                }

                metrics["services"][service_name] = service_metrics

                # Update overall counts
                if health == ServiceHealth.HEALTHY:
                    metrics["overall_metrics"]["healthy_services"] += 1
                elif health == ServiceHealth.DEGRADED:
                    metrics["overall_metrics"]["degraded_services"] += 1
                elif health == ServiceHealth.UNHEALTHY:
                    metrics["overall_metrics"]["unhealthy_services"] += 1

            # Log metrics request
            await log_action(
                self.db,
                user_id,
                "integration_metrics_request",
                entity_type="integration",
                entity_id=None,
                details={"metrics_requested_at": datetime.utcnow().isoformat()}
            )

            return metrics

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "integration_metrics_error",
                entity_type="integration",
                entity_id=None,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to get integration metrics: {str(e)}")