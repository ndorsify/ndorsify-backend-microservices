"""Data-access for discovery: creator index search and shortlists."""
from typing import List, Optional

from sqlalchemy import func, or_, select
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
    platforms: List[str],
    min_followers: Optional[int],
    max_followers: Optional[int],
    min_engagement: Optional[float],
    min_rate: Optional[int],
    max_rate: Optional[int],
    verified: Optional[bool],
    location: Optional[str],
    sort: str,
    offset: int,
    limit: int,
) -> List[CreatorIndex]:
    stmt = select(CreatorIndex)

    if q:
        # Free-text over name, handle, niches, and location.
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(CreatorIndex.display_name).like(like),
                func.lower(CreatorIndex.handle).like(like),
                CreatorIndex.niches_text.like(like),
                func.lower(CreatorIndex.location).like(like),
            )
        )
    for niche in niches:
        stmt = stmt.where(CreatorIndex.niches_text.like(f"%{niche.lower()}%"))
    # Platforms: match a creator carrying ANY of the requested platforms.
    if platforms:
        stmt = stmt.where(
            or_(
                *(
                    CreatorIndex.platforms_text.like(f"%{p.lower()}%")
                    for p in platforms
                )
            )
        )
    if min_followers is not None:
        stmt = stmt.where(CreatorIndex.follower_count >= min_followers)
    if max_followers is not None:
        stmt = stmt.where(CreatorIndex.follower_count <= max_followers)
    if min_engagement is not None:
        stmt = stmt.where(CreatorIndex.engagement_rate >= min_engagement)
    # A price filter only matches creators who have published a price. Without
    # this, unpriced creators (rate_per_post 0) satisfy any "<= max" bound.
    if min_rate is not None or max_rate is not None:
        stmt = stmt.where(CreatorIndex.rate_per_post > 0)
    if min_rate is not None:
        stmt = stmt.where(CreatorIndex.rate_per_post >= min_rate)
    if max_rate is not None:
        stmt = stmt.where(CreatorIndex.rate_per_post <= max_rate)
    if verified:
        stmt = stmt.where(CreatorIndex.verified.is_(True))
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


async def list_shortlists_for_brand(
    session: AsyncSession, brand_id: int
) -> List[Shortlist]:
    result = await session.execute(
        select(Shortlist)
        .where(Shortlist.brand_id == brand_id)
        .order_by(Shortlist.created_at.desc(), Shortlist.id.desc())
    )
    return list(result.scalars().all())


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
