"""Data-access for campaigns, invitations, applications."""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.campaign import Application, Campaign, Invitation


async def get_campaign(session: AsyncSession, campaign_id: int) -> Optional[Campaign]:
    campaign = await session.get(Campaign, campaign_id)
    if campaign is not None and campaign.is_deleted:
        return None
    return campaign


async def list_campaigns_for_brand(
    session: AsyncSession, brand_id: int, *, offset: int, limit: int
) -> List[Campaign]:
    result = await session.execute(
        select(Campaign)
        .where(Campaign.brand_id == brand_id, Campaign.is_deleted.is_(False))
        .order_by(Campaign.created_at.desc(), Campaign.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def search_open_campaigns(
    session: AsyncSession,
    *,
    q: Optional[str],
    min_budget: Optional[float],
    max_budget: Optional[float],
    offset: int,
    limit: int,
) -> List[Campaign]:
    stmt = select(Campaign).where(
        Campaign.status == "open", Campaign.is_deleted.is_(False)
    )
    if q:
        stmt = stmt.where(Campaign.title.ilike(f"%{q}%"))
    if min_budget is not None:
        stmt = stmt.where(Campaign.budget_amount >= min_budget)
    if max_budget is not None:
        stmt = stmt.where(Campaign.budget_amount <= max_budget)
    stmt = (
        stmt.order_by(Campaign.published_at.desc().nullslast(), Campaign.id.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_invitation(session: AsyncSession, invitation_id: int) -> Optional[Invitation]:
    return await session.get(Invitation, invitation_id)


async def get_invitation_pair(
    session: AsyncSession, campaign_id: int, creator_id: int
) -> Optional[Invitation]:
    result = await session.execute(
        select(Invitation).where(
            Invitation.campaign_id == campaign_id,
            Invitation.creator_id == creator_id,
        )
    )
    return result.scalar_one_or_none()


async def list_invitations_for_creator(
    session: AsyncSession, creator_id: int
) -> List[Invitation]:
    result = await session.execute(
        select(Invitation)
        .where(Invitation.creator_id == creator_id)
        .order_by(Invitation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_application(session: AsyncSession, application_id: int) -> Optional[Application]:
    return await session.get(Application, application_id)


async def get_application_pair(
    session: AsyncSession, campaign_id: int, creator_id: int
) -> Optional[Application]:
    result = await session.execute(
        select(Application).where(
            Application.campaign_id == campaign_id,
            Application.creator_id == creator_id,
        )
    )
    return result.scalar_one_or_none()


async def list_applications_for_campaign(
    session: AsyncSession, campaign_id: int
) -> List[Application]:
    result = await session.execute(
        select(Application)
        .where(Application.campaign_id == campaign_id)
        .order_by(Application.created_at.desc())
    )
    return list(result.scalars().all())


async def save(session: AsyncSession, obj):
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj
