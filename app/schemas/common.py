from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')


class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    total_pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int) -> "PageResponse[T]":
        total_pages = (total + size - 1) // size if size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
