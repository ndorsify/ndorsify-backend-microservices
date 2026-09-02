"""Data-access for profiles."""
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.profiles import BrandProfile, CreatorProfile, SocialAccount


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


async def list_social_accounts(
    session: AsyncSession, user_id: int
) -> List[SocialAccount]:
    result = await session.execute(
        select(SocialAccount).where(SocialAccount.user_id == user_id)
    )
    return list(result.scalars().all())


async def get_social_account(
    session: AsyncSession, user_id: int, platform: str
) -> Optional[SocialAccount]:
    result = await session.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user_id, SocialAccount.platform == platform
        )
    )
    return result.scalar_one_or_none()


async def delete_social_account(session: AsyncSession, user_id: int, platform: str) -> None:
    await session.execute(
        delete(SocialAccount).where(
            SocialAccount.user_id == user_id, SocialAccount.platform == platform
        )
    )
    await session.commit()
