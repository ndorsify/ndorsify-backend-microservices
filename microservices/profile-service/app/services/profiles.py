"""Profile business logic (P0): public reads and self-upsert, with a
completion-percentage recomputed from required-field presence on every write."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..clients import discovery as discovery_client
from ..models.profiles import BrandProfile, CreatorProfile
from ..repositories import profiles as repo
from ..schemas.profiles import (
    BrandProfileResponse,
    BrandProfileUpdate,
    CreatorProfileResponse,
    CreatorProfileUpdate,
)


async def aggregate_and_push(session: AsyncSession, user_id: int) -> None:
    """Push the *complete* current picture of a creator to discovery-service —
    identity fields from CreatorProfile, stats aggregated across every
    connected SocialAccount. `upsert_creator_index` is a full replace, so this
    is the only function allowed to call it; every caller (a basic profile
    save, a social connect/sync/disconnect) goes through here so neither side
    ever silently overwrites the other's fields with defaults.

    Aggregation: follower_count sums across platforms; engagement_rate is the
    simple average; verified is true once at least one platform is connected;
    handle is the first connected account's (arbitrary but stable — accounts
    are returned in insertion order).
    """
    profile = await repo.get_creator(session, user_id)
    accounts = await repo.list_social_accounts(session, user_id)

    follower_count = sum(a.follower_count for a in accounts)
    engagement_rate = (
        round(sum(a.engagement_rate for a in accounts) / len(accounts), 1)
        if accounts
        else 0.0
    )
    handle = accounts[0].handle if accounts else None
    platforms = [a.platform for a in accounts]

    await discovery_client.upsert_creator_index(
        user_id=user_id,
        display_name=profile.display_name if profile else None,
        handle=handle,
        bio=profile.bio if profile else None,
        niches=(profile.niches or []) if profile else [],
        platforms=platforms,
        location=profile.location if profile else None,
        follower_count=follower_count,
        engagement_rate=engagement_rate,
        verified=bool(accounts),
    )

# Required fields for a "campaign-ready" profile. Equal-weighted; a value counts
# as present when it is a non-empty string or a non-empty list.
_CREATOR_REQUIRED = (
    "display_name",
    "bio",
    "niches",
    "location",
    "languages",
    "avatar_url",
)
_BRAND_REQUIRED = ("company_name", "industry", "logo_url", "website", "about")


def _completion(obj, fields) -> int:
    present = sum(1 for f in fields if getattr(obj, f))
    return round(present / len(fields) * 100)


def _creator_response(p: CreatorProfile) -> CreatorProfileResponse:
    return CreatorProfileResponse(
        user_id=p.user_id,
        display_name=p.display_name,
        bio=p.bio,
        niches=p.niches or [],
        location=p.location,
        languages=p.languages or [],
        avatar_url=p.avatar_url,
        completion_pct=p.completion_pct,
    )


def _brand_response(p: BrandProfile) -> BrandProfileResponse:
    return BrandProfileResponse(
        user_id=p.user_id,
        company_name=p.company_name,
        industry=p.industry,
        logo_url=p.logo_url,
        website=p.website,
        about=p.about,
    )


async def get_creator(
    session: AsyncSession, user_id: int
) -> Optional[CreatorProfileResponse]:
    p = await repo.get_creator(session, user_id)
    return _creator_response(p) if p else None


async def upsert_creator(
    session: AsyncSession, user_id: int, dto: CreatorProfileUpdate
) -> CreatorProfileResponse:
    p = await repo.get_creator(session, user_id)
    if p is None:
        p = CreatorProfile(user_id=user_id, niches=[], languages=[])
    for key, value in dto.model_dump(exclude_unset=True).items():
        setattr(p, key, value)
    p.completion_pct = _completion(p, _CREATOR_REQUIRED)
    saved = await repo.save(session, p)
    # Best-effort: make the creator searchable in discovery (stand-in for a
    # profile.updated event). Never fails the profile save. Goes through the
    # shared aggregator so any already-connected social stats aren't wiped.
    await aggregate_and_push(session, saved.user_id)
    return _creator_response(saved)


async def get_brand(
    session: AsyncSession, user_id: int
) -> Optional[BrandProfileResponse]:
    p = await repo.get_brand(session, user_id)
    return _brand_response(p) if p else None


async def upsert_brand(
    session: AsyncSession, user_id: int, dto: BrandProfileUpdate
) -> BrandProfileResponse:
    p = await repo.get_brand(session, user_id)
    if p is None:
        p = BrandProfile(user_id=user_id)
    for key, value in dto.model_dump(exclude_unset=True).items():
        setattr(p, key, value)
    return _brand_response(await repo.save(session, p))
