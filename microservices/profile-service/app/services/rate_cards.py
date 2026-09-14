"""Rate-card business logic (Phase 3)."""
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.rate_cards import RateCardPackage
from ..repositories import rate_cards as repo
from ..schemas.rate_cards import (
    RateCardPackageIn,
    RateCardResponse,
    RateCardUpdate,
)


def _package_out(p: RateCardPackage) -> RateCardPackageIn:
    return RateCardPackageIn(
        name=p.name,
        price=p.price,
        description=p.description or "",
        turnaround_days=p.turnaround_days,
        visible=p.visible,
        items=p.items or [],
    )


async def get_for_owner(session: AsyncSession, user_id: int) -> RateCardResponse:
    card = await repo.get_card(session, user_id)
    if card is None:
        return RateCardResponse(hidden=False, packages=[], updated_at=None)
    packages = await repo.list_packages(session, card.id)
    return RateCardResponse(
        hidden=card.hidden,
        packages=[_package_out(p) for p in packages],
        updated_at=card.updated_at,
    )


async def save(
    session: AsyncSession, user_id: int, dto: RateCardUpdate
) -> RateCardResponse:
    await repo.replace_card(
        session,
        user_id,
        hidden=dto.hidden,
        packages=[p.model_dump() for p in dto.packages],
    )
    return await get_for_owner(session, user_id)
