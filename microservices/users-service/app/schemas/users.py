"""Request/response DTOs — ports of the Java ``UsersRequestDto`` / ``UsersResponseDto``.

Field names are kept camelCase to preserve the existing JSON contract.
"""
from typing import Optional

from pydantic import BaseModel


class UsersRequestDto(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    imageUrl: Optional[str] = None
    # Present on the Java request DTO but absent from the entity; accepted and
    # ignored to preserve the original contract.
    country: Optional[str] = None


class UsersResponseDto(BaseModel):
    id: int
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    imageUrl: Optional[str] = None
