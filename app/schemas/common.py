from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    correlation_id: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody

    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        correlation_id: str,
        details: list[ErrorDetail] | None = None,
    ) -> "ErrorResponse":
        return cls(
            error=ErrorBody(
                code=code,
                message=message,
                correlation_id=correlation_id,
                details=details,
            )
        )


class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> "PageResponse[T]":
        return cls(items=items, total=total, page=page, page_size=page_size)
