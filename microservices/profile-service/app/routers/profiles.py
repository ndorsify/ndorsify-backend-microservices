"""Profiles HTTP layer (P0) — /profiles.

Public reads by user_id; self-upsert guarded by role (creator/brand).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import Principal, require_role
from ..db.session import get_session
from ..schemas.profiles import (
    BrandProfileResponse,
    BrandProfileUpdate,
    CreatorProfileResponse,
    CreatorProfileUpdate,
)
from ..services import profiles as service

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/creators/{user_id}", response_model=CreatorProfileResponse)
async def get_creator_profile(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> CreatorProfileResponse:
    profile = await service.get_creator(session, user_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Creator profile not found")
    return profile


@router.put("/creators/me", response_model=CreatorProfileResponse)
async def upsert_creator_profile(
    body: CreatorProfileUpdate,
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> CreatorProfileResponse:
    return await service.upsert_creator(session, principal.user_id, body)


@router.get("/brands/{user_id}", response_model=BrandProfileResponse)
async def get_brand_profile(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> BrandProfileResponse:
    profile = await service.get_brand(session, user_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand profile not found")
    return profile


@router.put("/brands/me", response_model=BrandProfileResponse)
async def upsert_brand_profile(
    body: BrandProfileUpdate,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> BrandProfileResponse:
    return await service.upsert_brand(session, principal.user_id, body)
