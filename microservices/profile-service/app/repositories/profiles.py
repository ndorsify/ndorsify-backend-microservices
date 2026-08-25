"""Data-access for profiles."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.profiles import BrandProfile, CreatorProfile


async def get_creator(session: AsyncSession, user_id: int) -> Optional[CreatorProfile]:
    result = await session.execute(
        select(CreatorProfile).where(CreatorProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_brand(session: AsyncSession, user_id: int) -> Optional[BrandProfile]:
    result = await session.execute(
        select(BrandProfile).where(BrandProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def save(session: AsyncSession, profile):
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile
