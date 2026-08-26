"""Data-access for discovery: creator index search and shortlists."""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.discovery import CreatorIndex, Shortlist, ShortlistItem


async def get_creator(session: AsyncSession, user_id: int) -> Optional[CreatorIndex]:
    result = await session.execute(
        select(CreatorIndex).where(CreatorIndex.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def search_creators(
    session: AsyncSession,
    *,
    q: Optional[str],
    niches: List[str],
    min_followers: Optional[int],
    max_followers: Optional[int],
    min_engagement: Optional[float],
    location: Optional[str],
    sort: str,
    offset: int,
    limit: int,
) -> List[CreatorIndex]:
    stmt = select(CreatorIndex)

    if q:
        stmt = stmt.where(CreatorIndex.display_name.ilike(f"%{q}%"))
    for niche in niches:
        stmt = stmt.where(CreatorIndex.niches_text.like(f"%{niche.lower()}%"))
    if min_followers is not None:
        stmt = stmt.where(CreatorIndex.follower_count >= min_followers)
    if max_followers is not None:
        stmt = stmt.where(CreatorIndex.follower_count <= max_followers)
    if min_engagement is not None:
        stmt = stmt.where(CreatorIndex.engagement_rate >= min_engagement)
    if location:
        stmt = stmt.where(CreatorIndex.location.ilike(f"%{location}%"))

    order_col = {
        "followers": CreatorIndex.follower_count.desc(),
        "engagement": CreatorIndex.engagement_rate.desc(),
        "rating": CreatorIndex.avg_rating.desc(),
    }.get(sort, CreatorIndex.follower_count.desc())

    stmt = stmt.order_by(order_col, CreatorIndex.user_id.asc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_shortlist(session: AsyncSession, shortlist_id: int) -> Optional[Shortlist]:
    return await session.get(Shortlist, shortlist_id)


async def list_shortlist_items(
    session: AsyncSession, shortlist_id: int
) -> List[ShortlistItem]:
    result = await session.execute(
        select(ShortlistItem)
        .where(ShortlistItem.shortlist_id == shortlist_id)
        .order_by(ShortlistItem.created_at.asc(), ShortlistItem.id.asc())
    )
    return list(result.scalars().all())


async def get_shortlist_item(
    session: AsyncSession, shortlist_id: int, creator_id: int
) -> Optional[ShortlistItem]:
    result = await session.execute(
        select(ShortlistItem).where(
            ShortlistItem.shortlist_id == shortlist_id,
            ShortlistItem.creator_id == creator_id,
        )
    )
    return result.scalar_one_or_none()


async def save(session: AsyncSession, obj):
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj
