"""HTTP layer — port of the Java ``UsersController`` (@RequestMapping("/users"))."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session
from ..schemas.pagination import PageResponse
from ..schemas.users import UsersRequestDto, UsersResponseDto
from ..services import users as service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/list", response_model=List[UsersResponseDto])
async def get_all_list(
    page: int = Query(0),
    size: int = Query(10),
    sortBy: str = Query("id"),
    session: AsyncSession = Depends(get_session),
) -> List[UsersResponseDto]:
    return await service.get_all_users(session, page=page, size=size, sort_by=sortBy)


@router.get("", response_model=PageResponse[UsersResponseDto])
async def get_all_page(
    page: int = Query(0),
    size: int = Query(10),
    sortBy: str = Query("id"),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[UsersResponseDto]:
    return await service.get_all_users_page(session, page=page, size=size, sort_by=sortBy)


@router.post("", response_model=UsersResponseDto)
async def create_user(
    body: UsersRequestDto,
    session: AsyncSession = Depends(get_session),
) -> UsersResponseDto:
    return await service.create_user(session, body)


@router.put("/{user_id}", response_model=UsersResponseDto)
async def update_user(
    user_id: int,
    body: UsersRequestDto,
    session: AsyncSession = Depends(get_session),
) -> UsersResponseDto:
    updated = await service.update_user(session, user_id, body)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return updated
