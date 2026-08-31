"""Campaign business logic (E1): CRUD + publish/close state machine, marketplace,
invitations, and applications.

On acceptance (invitation or application) a Collaboration should be created via
collaboration-service (E3) and events emitted to notification-service (E5).
Both are marked TODO — those services do not exist yet.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..clients import collaboration as collaboration_client
from ..models.campaign import Application, Campaign, Invitation
from ..repositories import campaign as repo
from ..schemas.campaign import (
    ApplicationResponse,
    CampaignCreate,
    CampaignResponse,
    CampaignUpdate,
    InvitationResponse,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _deliverable_specs(campaign: Campaign) -> list:
    return [
        {"platform": d.get("platform"), "type": d.get("type")}
        for d in (campaign.deliverables or [])
    ]


def to_campaign_response(c: Campaign) -> CampaignResponse:
    return CampaignResponse(
        id=c.id,
        brand_id=c.brand_id,
        title=c.title,
        objective=c.objective,
        deliverables=c.deliverables or [],
        platforms=c.platforms or [],
        budget_amount=c.budget_amount,
        budget_currency=c.budget_currency,
        starts_on=c.starts_on,
        ends_on=c.ends_on,
        target_audience=c.target_audience or {},
        status=c.status,
        published_at=c.published_at,
        funded_at=c.funded_at,
    )


def _to_invitation(i: Invitation) -> InvitationResponse:
    return InvitationResponse(
        id=i.id,
        campaign_id=i.campaign_id,
        creator_id=i.creator_id,
        status=i.status,
        message=i.message,
    )


def _to_application(a: Application) -> ApplicationResponse:
    return ApplicationResponse(
        id=a.id,
        campaign_id=a.campaign_id,
        creator_id=a.creator_id,
        proposal=a.proposal,
        proposed_rate=a.proposed_rate,
        status=a.status,
    )


# --- campaign CRUD ----------------------------------------------------------
async def create_campaign(
    session: AsyncSession, brand_id: int, dto: CampaignCreate
) -> CampaignResponse:
    campaign = Campaign(
        brand_id=brand_id,
        title=dto.title,
        objective=dto.objective,
        deliverables=[d.model_dump() for d in dto.deliverables],
        platforms=dto.platforms,
        budget_amount=dto.budget_amount,
        budget_currency=dto.budget_currency,
        starts_on=dto.starts_on,
        ends_on=dto.ends_on,
        target_audience=dto.target_audience,
        status="draft",
    )
    return to_campaign_response(await repo.save(session, campaign))


async def _owned_campaign(
    session: AsyncSession, brand_id: int, campaign_id: int
) -> Campaign:
    campaign = await repo.get_campaign(session, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found")
    if campaign.brand_id != brand_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your campaign")
    return campaign


async def get_campaign_visible(
    session: AsyncSession, campaign_id: int, viewer_id: int
) -> CampaignResponse:
    campaign = await repo.get_campaign(session, campaign_id)
    # Owners see any status; everyone else only open campaigns. Hide the rest
    # as 404 so drafts are not discoverable.
    if campaign is None or (
        campaign.brand_id != viewer_id and campaign.status != "open"
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found")
    return to_campaign_response(campaign)


async def update_campaign(
    session: AsyncSession, brand_id: int, campaign_id: int, dto: CampaignUpdate
) -> CampaignResponse:
    campaign = await _owned_campaign(session, brand_id, campaign_id)
    if campaign.status not in ("draft", "open"):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only draft or open campaigns can be edited"
        )
    data = dto.model_dump(exclude_unset=True)
    if "deliverables" in data and data["deliverables"] is not None:
        data["deliverables"] = [d for d in data["deliverables"]]  # already dicts
    for key, value in data.items():
        setattr(campaign, key, value)
    return to_campaign_response(await repo.save(session, campaign))


_PUBLISH_REQUIRED = ("title", "objective", "budget_amount", "starts_on", "ends_on")


async def publish_campaign(
    session: AsyncSession, brand_id: int, campaign_id: int
) -> CampaignResponse:
    campaign = await _owned_campaign(session, brand_id, campaign_id)
    if campaign.status != "draft":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only a draft campaign can be published"
        )
    missing = [f for f in _PUBLISH_REQUIRED if not getattr(campaign, f)]
    if not campaign.deliverables:
        missing.append("deliverables")
    if missing:
        raise HTTPException(
            422, f"Cannot publish — missing: {', '.join(missing)}"
        )
    campaign.status = "open"
    campaign.published_at = _now()
    return to_campaign_response(await repo.save(session, campaign))


async def close_campaign(
    session: AsyncSession, brand_id: int, campaign_id: int
) -> CampaignResponse:
    campaign = await _owned_campaign(session, brand_id, campaign_id)
    if campaign.status != "open":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only an open campaign can be closed"
        )
    campaign.status = "closed"
    return to_campaign_response(await repo.save(session, campaign))


async def fund_campaign(
    session: AsyncSession, brand_id: int, campaign_id: int
) -> CampaignResponse:
    """Record a funding acknowledgment — no real payment processing (Phase 5
    payments-service, not built yet). Idempotent: re-confirming an already
    -funded campaign is a no-op, not an error, since there's no charge to
    duplicate. Deliberately does not touch `status` — marketplace visibility
    and everything else keyed on `status == "open"` must be unaffected.
    """
    campaign = await _owned_campaign(session, brand_id, campaign_id)
    if campaign.status != "open":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Campaign must be published before it can be funded",
        )
    if campaign.funded_at is None:
        campaign.funded_at = _now()
        campaign = await repo.save(session, campaign)
    return to_campaign_response(campaign)


async def list_mine(
    session: AsyncSession, brand_id: int, *, page: int, size: int
) -> List[CampaignResponse]:
    rows = await repo.list_campaigns_for_brand(
        session, brand_id, offset=page * size, limit=size
    )
    return [to_campaign_response(c) for c in rows]


async def search_marketplace(
    session: AsyncSession,
    *,
    q: Optional[str],
    min_budget: Optional[float],
    max_budget: Optional[float],
    page: int,
    size: int,
) -> List[CampaignResponse]:
    rows = await repo.search_open_campaigns(
        session,
        q=q,
        min_budget=min_budget,
        max_budget=max_budget,
        offset=page * size,
        limit=size,
    )
    return [to_campaign_response(c) for c in rows]


# --- invitations ------------------------------------------------------------
async def invite(
    session: AsyncSession, brand_id: int, campaign_id: int, creator_id: int, message
) -> InvitationResponse:
    await _owned_campaign(session, brand_id, campaign_id)
    if await repo.get_invitation_pair(session, campaign_id, creator_id) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Creator already invited to this campaign"
        )
    invitation = Invitation(
        campaign_id=campaign_id, creator_id=creator_id, message=message
    )
    saved = await repo.save(session, invitation)
    # TODO(E5): emit campaign.invited
    return _to_invitation(saved)


async def list_invitations_mine(
    session: AsyncSession, creator_id: int
) -> List[InvitationResponse]:
    rows = await repo.list_invitations_for_creator(session, creator_id)
    return [_to_invitation(i) for i in rows]


async def respond_invitation(
    session: AsyncSession, creator_id: int, invitation_id: int, decision: str
) -> InvitationResponse:
    invitation = await repo.get_invitation(session, invitation_id)
    if invitation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invitation not found")
    if invitation.creator_id != creator_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your invitation")
    if invitation.status != "pending":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Invitation already responded to"
        )
    if decision not in ("accepted", "declined"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid decision")
    invitation.status = decision
    invitation.responded_at = _now()
    saved = await repo.save(session, invitation)
    if decision == "accepted":
        campaign = await repo.get_campaign(session, invitation.campaign_id)
        if campaign is not None:
            await collaboration_client.create_collaboration(
                campaign.id,
                campaign.brand_id,
                invitation.creator_id,
                _deliverable_specs(campaign),
            )
    # TODO(E5): emit invitation.accepted / invitation.declined
    return _to_invitation(saved)


# --- applications -----------------------------------------------------------
async def apply(
    session: AsyncSession, creator_id: int, campaign_id: int, proposal, proposed_rate
) -> ApplicationResponse:
    campaign = await repo.get_campaign(session, campaign_id)
    if campaign is None or campaign.status != "open":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Campaign is not open for applications"
        )
    if await repo.get_application_pair(session, campaign_id, creator_id) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "You have already applied to this campaign"
        )
    application = Application(
        campaign_id=campaign_id,
        creator_id=creator_id,
        proposal=proposal,
        proposed_rate=proposed_rate,
    )
    saved = await repo.save(session, application)
    # TODO(E5): emit campaign.applied
    return _to_application(saved)


async def list_applications(
    session: AsyncSession, brand_id: int, campaign_id: int
) -> List[ApplicationResponse]:
    await _owned_campaign(session, brand_id, campaign_id)
    rows = await repo.list_applications_for_campaign(session, campaign_id)
    return [_to_application(a) for a in rows]


async def decide_application(
    session: AsyncSession, brand_id: int, application_id: int, decision: str
) -> ApplicationResponse:
    application = await repo.get_application(session, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    await _owned_campaign(session, brand_id, application.campaign_id)
    if application.status != "submitted":
        raise HTTPException(status.HTTP_409_CONFLICT, "Application already decided")
    if decision not in ("accepted", "rejected"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid decision")
    application.status = decision
    application.decided_at = _now()
    saved = await repo.save(session, application)
    if decision == "accepted":
        campaign = await repo.get_campaign(session, application.campaign_id)
        if campaign is not None:
            await collaboration_client.create_collaboration(
                campaign.id,
                campaign.brand_id,
                application.creator_id,
                _deliverable_specs(campaign),
            )
    # TODO(E5): emit application.accepted / application.rejected
    return _to_application(saved)
