"""Rate-card HTTP layer (Phase 3) — /profiles/creators/.../rate-card."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import Principal, require_role
from ..db.session import get_session
from ..schemas.rate_cards import RateCardResponse, RateCardUpdate
from ..services import rate_cards as service

router = APIRouter(prefix="/profiles/creators", tags=["rate-cards"])


@router.get("/me/rate-card", response_model=RateCardResponse)
async def get_my_rate_card(
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> RateCardResponse:
    return await service.get_for_owner(session, principal.user_id)


@router.put("/me/rate-card", response_model=RateCardResponse)
async def save_my_rate_card(
    body: RateCardUpdate,
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> RateCardResponse:
    return await service.save(session, principal.user_id, body)
