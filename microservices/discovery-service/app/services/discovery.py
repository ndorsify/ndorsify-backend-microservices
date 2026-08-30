"""Discovery business logic (P0): maintain the creator index, search it, and
manage brand shortlists."""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.discovery import CreatorIndex, Shortlist, ShortlistItem
from ..repositories import discovery as repo
from ..schemas.discovery import (
    CreatorIndexUpsert,
    CreatorResult,
    ShortlistDetailResponse,
    ShortlistResponse,
)


def _to_result(c: CreatorIndex) -> CreatorResult:
    return CreatorResult(
        user_id=c.user_id,
        display_name=c.display_name,
        handle=c.handle,
        niches=c.niches or [],
        platforms=c.platforms or [],
        location=c.location,
        follower_count=c.follower_count,
        engagement_rate=c.engagement_rate,
        avg_rating=c.avg_rating,
        rate_per_post=c.rate_per_post,
        verified=c.verified,
    )


async def upsert_creator_index(
    session: AsyncSession, dto: CreatorIndexUpsert
) -> CreatorResult:
    """Idempotent upsert keyed by user_id (called by the internal ingest)."""
    c = await repo.get_creator(session, dto.user_id)
    if c is None:
        c = CreatorIndex(user_id=dto.user_id)
    c.display_name = dto.display_name
    c.handle = dto.handle
    c.bio = dto.bio
    c.niches = dto.niches
    c.niches_text = " ".join(n.lower() for n in dto.niches)
    c.platforms = dto.platforms
    c.platforms_text = " ".join(p.lower() for p in dto.platforms)
    c.location = dto.location
    c.follower_count = dto.follower_count
    c.engagement_rate = dto.engagement_rate
    c.avg_rating = dto.avg_rating
    c.rate_per_post = dto.rate_per_post
    c.verified = dto.verified
    return _to_result(await repo.save(session, c))


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
    page: int,
    size: int,
) -> List[CreatorResult]:
    rows = await repo.search_creators(
        session,
        q=q,
        niches=niches,
        platforms=platforms,
        min_followers=min_followers,
        max_followers=max_followers,
        min_engagement=min_engagement,
        min_rate=min_rate,
        max_rate=max_rate,
        verified=verified,
        location=location,
        sort=sort,
        offset=page * size,
        limit=size,
    )
    return [_to_result(r) for r in rows]


async def get_creator(session: AsyncSession, user_id: int) -> CreatorResult:
    c = await repo.get_creator(session, user_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Creator not found")
    return _to_result(c)


async def create_shortlist(
    session: AsyncSession, brand_id: int, name: str
) -> ShortlistResponse:
    sl = await repo.save(session, Shortlist(brand_id=brand_id, name=name))
    return ShortlistResponse(id=sl.id, brand_id=sl.brand_id, name=sl.name)


async def list_shortlists(
    session: AsyncSession, brand_id: int
) -> List[ShortlistResponse]:
    rows = await repo.list_shortlists_for_brand(session, brand_id)
    return [
        ShortlistResponse(id=sl.id, brand_id=sl.brand_id, name=sl.name) for sl in rows
    ]


async def _owned_shortlist(
    session: AsyncSession, brand_id: int, shortlist_id: int
) -> Shortlist:
    sl = await repo.get_shortlist(session, shortlist_id)
    if sl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shortlist not found")
    if sl.brand_id != brand_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your shortlist")
    return sl


async def add_shortlist_item(
    session: AsyncSession, brand_id: int, shortlist_id: int, creator_id: int
) -> ShortlistDetailResponse:
    await _owned_shortlist(session, brand_id, shortlist_id)
    existing = await repo.get_shortlist_item(session, shortlist_id, creator_id)
    if existing is None:  # idempotent add
        await repo.save(
            session, ShortlistItem(shortlist_id=shortlist_id, creator_id=creator_id)
        )
    return await get_shortlist(session, brand_id, shortlist_id)


async def get_shortlist(
    session: AsyncSession, brand_id: int, shortlist_id: int
) -> ShortlistDetailResponse:
    sl = await _owned_shortlist(session, brand_id, shortlist_id)
    items = await repo.list_shortlist_items(session, shortlist_id)
    return ShortlistDetailResponse(
        id=sl.id,
        brand_id=sl.brand_id,
        name=sl.name,
        creator_ids=[i.creator_id for i in items],
    )
