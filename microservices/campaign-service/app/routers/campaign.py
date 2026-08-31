"""Campaign HTTP layer (E1) — /campaigns, /invitations, /applications."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import Principal, require_auth, require_role
from ..db.session import get_session
from ..schemas.campaign import (
    ApplicationResponse,
    ApplyRequest,
    CampaignCreate,
    CampaignResponse,
    CampaignUpdate,
    DecideRequest,
    InvitationResponse,
    InviteRequest,
    RespondRequest,
)
from ..services import campaign as service

router = APIRouter(tags=["campaigns"])


# --- campaign CRUD (brand) + marketplace ------------------------------------
@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    body: CampaignCreate,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    return await service.create_campaign(session, principal.user_id, body)


@router.get("/campaigns", response_model=List[CampaignResponse])
async def marketplace(
    q: Optional[str] = Query(None),
    min_budget: Optional[float] = Query(None, ge=0),
    max_budget: Optional[float] = Query(None, ge=0),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    _principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> List[CampaignResponse]:
    return await service.search_marketplace(
        session, q=q, min_budget=min_budget, max_budget=max_budget, page=page, size=size
    )


@router.get("/campaigns/mine", response_model=List[CampaignResponse])
async def my_campaigns(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> List[CampaignResponse]:
    return await service.list_mine(session, principal.user_id, page=page, size=size)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    return await service.get_campaign_visible(session, campaign_id, principal.user_id)


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    body: CampaignUpdate,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    return await service.update_campaign(session, principal.user_id, campaign_id, body)


@router.post("/campaigns/{campaign_id}/publish", response_model=CampaignResponse)
async def publish_campaign(
    campaign_id: int,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    return await service.publish_campaign(session, principal.user_id, campaign_id)


@router.post("/campaigns/{campaign_id}/close", response_model=CampaignResponse)
async def close_campaign(
    campaign_id: int,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    return await service.close_campaign(session, principal.user_id, campaign_id)


@router.post("/campaigns/{campaign_id}/fund", response_model=CampaignResponse)
async def fund_campaign(
    campaign_id: int,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    return await service.fund_campaign(session, principal.user_id, campaign_id)


# --- invitations ------------------------------------------------------------
@router.post("/campaigns/{campaign_id}/invitations", response_model=InvitationResponse)
async def invite(
    campaign_id: int,
    body: InviteRequest,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> InvitationResponse:
    return await service.invite(
        session, principal.user_id, campaign_id, body.creator_id, body.message
    )


@router.get("/invitations/mine", response_model=List[InvitationResponse])
async def my_invitations(
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> List[InvitationResponse]:
    return await service.list_invitations_mine(session, principal.user_id)


@router.post("/invitations/{invitation_id}/respond", response_model=InvitationResponse)
async def respond_invitation(
    invitation_id: int,
    body: RespondRequest,
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> InvitationResponse:
    return await service.respond_invitation(
        session, principal.user_id, invitation_id, body.decision
    )


# --- applications -----------------------------------------------------------
@router.post("/campaigns/{campaign_id}/applications", response_model=ApplicationResponse)
async def apply(
    campaign_id: int,
    body: ApplyRequest,
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    return await service.apply(
        session, principal.user_id, campaign_id, body.proposal, body.proposed_rate
    )


@router.get(
    "/campaigns/{campaign_id}/applications",
    response_model=List[ApplicationResponse],
)
async def list_applications(
    campaign_id: int,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> List[ApplicationResponse]:
    return await service.list_applications(session, principal.user_id, campaign_id)


@router.post("/applications/{application_id}/decide", response_model=ApplicationResponse)
async def decide_application(
    application_id: int,
    body: DecideRequest,
    principal: Principal = Depends(require_role("brand")),
    session: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    return await service.decide_application(
        session, principal.user_id, application_id, body.decision
    )
