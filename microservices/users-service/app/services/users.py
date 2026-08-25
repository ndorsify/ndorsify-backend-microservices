"""Business logic — port of the Java ``UsersService``."""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import users as repo
from ..schemas.pagination import PageResponse
from ..schemas.users import UsersRequestDto, UsersResponseDto
from ..utils.mapping import (
    resolve_sort_column,
    user_entity_to_response_dto,
    user_request_dto_to_entity,
)


async def get_all_users(
    session: AsyncSession, *, page: int, size: int, sort_by: str
) -> List[UsersResponseDto]:
    rows = await repo.find_all(
        session,
        offset=page * size,
        limit=size,
        sort_column=resolve_sort_column(sort_by),
    )
    return [user_entity_to_response_dto(u) for u in rows]


async def get_all_users_page(
    session: AsyncSession, *, page: int, size: int, sort_by: str
) -> PageResponse[UsersResponseDto]:
    rows = await repo.find_all(
        session,
        offset=page * size,
        limit=size,
        sort_column=resolve_sort_column(sort_by),
    )
    total = await repo.count(session)
    return PageResponse.build(
        content=[user_entity_to_response_dto(u) for u in rows],
        page=page,
        size=size,
        total_elements=total,
        sort_by=sort_by,
    )


async def create_user(
    session: AsyncSession, dto: UsersRequestDto
) -> UsersResponseDto:
    entity = user_request_dto_to_entity(dto)
    saved = await repo.save(session, entity)
    return user_entity_to_response_dto(saved)


async def update_user(
    session: AsyncSession, user_id: int, dto: UsersRequestDto
) -> Optional[UsersResponseDto]:
    """Update an existing user, or return ``None`` when it does not exist
    (the caller turns that into a 404, mirroring the Java ResponseEntity)."""
    existing = await repo.find_by_id(session, user_id)
    if existing is None:
        return None
    existing.first_name = dto.firstName
    existing.last_name = dto.lastName
    existing.email = dto.email
    existing.image_url = dto.imageUrl
    saved = await repo.save(session, existing)
    return user_entity_to_response_dto(saved)
