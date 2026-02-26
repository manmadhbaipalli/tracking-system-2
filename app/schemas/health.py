from pydantic import BaseModel


class LivenessResponse(BaseModel):
    status: str = "ok"


class ReadinessResponse(BaseModel):
    status: str
    database: str
    circuit_breakers: dict[str, str]


class CircuitBreakerStatusResponse(BaseModel):
    name: str
    state: str
    failure_count: int
