"""Collaboration HTTP layer (E3) — /collaborations, /deliverables.

Creation is internal (service token, called by campaign-service on acceptance).
Everything else is participant-scoped via the user's JWT.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import Principal, require_auth, require_service_token
from ..db.session import get_session
from ..schemas.collaboration import (
    CollaborationResponse,
    CreateCollaboration,
    ReviewRequest,
    SubmitRequest,
    TimelineEntry,
)
from ..services import collaboration as service

router = APIRouter(tags=["collaborations"])


@router.post(
    "/collaborations",
    response_model=CollaborationResponse,
    dependencies=[Depends(require_service_token)],
)
async def create_collaboration(
    body: CreateCollaboration,
    session: AsyncSession = Depends(get_session),
) -> CollaborationResponse:
    return await service.create_collaboration(session, body)


@router.get("/collaborations/mine", response_model=List[CollaborationResponse])
async def my_collaborations(
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> List[CollaborationResponse]:
    return await service.list_mine(session, principal.user_id)


@router.get("/collaborations/{collaboration_id}", response_model=CollaborationResponse)
async def get_collaboration(
    collaboration_id: int,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> CollaborationResponse:
    return await service.get_collaboration(session, principal.user_id, collaboration_id)


@router.get(
    "/collaborations/{collaboration_id}/timeline",
    response_model=List[TimelineEntry],
)
async def get_timeline(
    collaboration_id: int,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> List[TimelineEntry]:
    return await service.timeline(session, principal.user_id, collaboration_id)


@router.post("/deliverables/{deliverable_id}/submit", response_model=CollaborationResponse)
async def submit_deliverable(
    deliverable_id: int,
    body: SubmitRequest,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> CollaborationResponse:
    return await service.submit_deliverable(
        session, principal.user_id, deliverable_id, body.file_refs, body.note
    )


@router.post("/deliverables/{deliverable_id}/review", response_model=CollaborationResponse)
async def review_deliverable(
    deliverable_id: int,
    body: ReviewRequest,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> CollaborationResponse:
    return await service.review_deliverable(
        session, principal.user_id, deliverable_id, body.decision, body.feedback
    )


@router.post("/deliverables/{deliverable_id}/mark-live", response_model=CollaborationResponse)
async def mark_live(
    deliverable_id: int,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> CollaborationResponse:
    return await service.mark_live(session, principal.user_id, deliverable_id)
