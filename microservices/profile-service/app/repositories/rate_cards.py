"""Rate-card persistence. `replace_card` is the only writer.

Old packages are deleted explicitly rather than left to the FK cascade: SQLite
(dev and tests) does not enforce cascades unless foreign keys are switched on
per connection, so relying on it would silently orphan rows.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.rate_cards import RateCard, RateCardPackage


async def get_card(session: AsyncSession, user_id: int) -> Optional[RateCard]:
    result = await session.execute(
        select(RateCard).where(RateCard.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_packages(
    session: AsyncSession, rate_card_id: int
) -> List[RateCardPackage]:
    result = await session.execute(
        select(RateCardPackage)
        .where(RateCardPackage.rate_card_id == rate_card_id)
        .order_by(RateCardPackage.sort_order.asc())
    )
    return list(result.scalars().all())


async def replace_card(
    session: AsyncSession, user_id: int, *, hidden: bool, packages: List[dict]
) -> RateCard:
    card = await get_card(session, user_id)
    if card is None:
        card = RateCard(user_id=user_id)
        session.add(card)
    card.hidden = hidden
    card.updated_at = datetime.utcnow()
    await session.flush()  # card.id for the package rows below

    await session.execute(
        delete(RateCardPackage).where(RateCardPackage.rate_card_id == card.id)
    )
    for index, package in enumerate(packages):
        session.add(
            RateCardPackage(
                rate_card_id=card.id,
                sort_order=index,
                name=package["name"],
                price=package["price"],
                description=package.get("description", ""),
                turnaround_days=package["turnaround_days"],
                visible=package.get("visible", True),
                items=package.get("items", []),
            )
        )
    await session.commit()
    await session.refresh(card)
    return card


async def min_visible_price(session: AsyncSession, user_id: int) -> int:
    """What discovery-service indexes as `rate_per_post` — 0 when there is
    nothing a brand could actually buy."""
    card = await get_card(session, user_id)
    if card is None or card.hidden:
        return 0
    prices = [p.price for p in await list_packages(session, card.id) if p.visible]
    return min(prices) if prices else 0
