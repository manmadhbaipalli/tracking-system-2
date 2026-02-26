import enum


class Role(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class CircuitBreakerState(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
