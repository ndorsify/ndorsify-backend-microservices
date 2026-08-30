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
    # profile.updated event). Never fails the profile save.
    await discovery_client.upsert_creator_index(
        user_id=saved.user_id,
        display_name=saved.display_name,
        bio=saved.bio,
        niches=saved.niches or [],
        location=saved.location,
    )
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
