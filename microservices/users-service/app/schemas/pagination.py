"""A Spring-Data-``Page``-shaped envelope, so the JSON contract of the
paginated ``GET /users`` endpoint stays familiar to existing clients.
"""
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SortInfo(BaseModel):
    sorted: bool
    unsorted: bool
    empty: bool


class PageResponse(BaseModel, Generic[T]):
    content: List[T]
    number: int          # current page index (0-based)
    size: int            # page size requested
    numberOfElements: int
    totalElements: int
    totalPages: int
    first: bool
    last: bool
    empty: bool
    sort: SortInfo

    @classmethod
    def build(
        cls,
        *,
        content: List[T],
        page: int,
        size: int,
        total_elements: int,
        sort_by: str,
    ) -> "PageResponse[T]":
        total_pages = (total_elements + size - 1) // size if size > 0 else 0
        return cls(
            content=content,
            number=page,
            size=size,
            numberOfElements=len(content),
            totalElements=total_elements,
            totalPages=total_pages,
            first=page == 0,
            last=page >= total_pages - 1,
            empty=len(content) == 0,
            sort=SortInfo(sorted=bool(sort_by), unsorted=not bool(sort_by), empty=not bool(sort_by)),
        )
