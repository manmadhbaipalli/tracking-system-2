from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    status: int
    error: str
    message: str
    details: list[FieldError] | None = None
    timestamp: datetime

    @classmethod
    def create(cls, status: int, error: str, message: str, details: list[FieldError] | None = None):
        return cls(status=status, error=error, message=message, details=details, timestamp=datetime.now())


T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    content: list[T]
    page: int
    size: int
    total_elements: int
    total_pages: int
    first: bool
    last: bool

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int):
        total_pages = (total + size - 1) // size if size > 0 else 0
        return cls(
            content=items,
            page=page,
            size=size,
            total_elements=total,
            total_pages=total_pages,
            first=page == 0,
            last=page >= total_pages - 1,
        )


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str | None = None
    circuit_breaker: str | None = None