"""Discovery HTTP layer (P0) — /discovery (creator search + brand shortlists)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import Principal, require_auth, require_role
from ..db.session import get_session
from ..schemas.discovery import (
    AddShortlistItemRequest,
    CreateShortlistRequest,
    CreatorResult,
    ShortlistDetailResponse,
    ShortlistResponse,
)
from ..services import discovery as service

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/creators", response_model=List[CreatorResult])
async def search_creators(
    q: Optional[str] = Query(None),
    niche: List[str] = Query(default_factory=list),
    min_followers: Optional[int] = Query(None, ge=0),
    max_followers: Optional[int] = Query(None, ge=0),
    min_engagement: Optional[float] = Query(None, ge=0),
    location: Optional[str] = Query(None),
    sort: str = Query("followers", pattern="^(followers|engagement|rating)$"),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    _principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> List[CreatorResult]:
    return await service.search_creators(
        session,
        q=q,
        niches=niche,
        min_followers=min_followers,
        max_followers=max_followers,
        min_engagement=min_engagement,
        location=location,
        sort=sort,
        page=page,
        size=size,
    )


@router.post("/shortlists", response_model=ShortlistResponse)
async def create_shortlist(
    body: CreateShortlistRequest,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> ShortlistResponse:
    return await service.create_shortlist(session, principal.user_id, body.name)


@router.post("/shortlists/{shortlist_id}/items", response_model=ShortlistDetailResponse)
async def add_shortlist_item(
    shortlist_id: int,
    body: AddShortlistItemRequest,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> ShortlistDetailResponse:
    return await service.add_shortlist_item(
        session, principal.user_id, shortlist_id, body.creator_id
    )


@router.get("/shortlists/{shortlist_id}", response_model=ShortlistDetailResponse)
async def get_shortlist(
    shortlist_id: int,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> ShortlistDetailResponse:
    return await service.get_shortlist(session, principal.user_id, shortlist_id)
