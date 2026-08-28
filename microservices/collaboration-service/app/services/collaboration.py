"""Collaboration business logic (E3): create from acceptance, submit/review/
mark-live deliverables, and roll the collaboration status up.

Events to notification-service (E5) are TODOs — that service does not exist yet.
"""
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.collaboration import (
    Collaboration,
    Deliverable,
    Review,
    Submission,
)
from ..repositories import collaboration as repo
from ..schemas.collaboration import (
    CollaborationResponse,
    CreateCollaboration,
    DeliverableResponse,
    TimelineEntry,
)
from .status import next_collab_status


def _deliverable_response(d: Deliverable) -> DeliverableResponse:
    return DeliverableResponse(
        id=d.id,
        collaboration_id=d.collaboration_id,
        platform=d.platform,
        type=d.type,
        description=d.description,
        due_on=d.due_on,
        status=d.status,
    )


async def _to_response(
    session: AsyncSession, collab: Collaboration
) -> CollaborationResponse:
    deliverables = await repo.list_deliverables(session, collab.id)
    return CollaborationResponse(
        id=collab.id,
        campaign_id=collab.campaign_id,
        brand_id=collab.brand_id,
        creator_id=collab.creator_id,
        status=collab.status,
        deliverables=[_deliverable_response(d) for d in deliverables],
    )


async def create_collaboration(
    session: AsyncSession, dto: CreateCollaboration
) -> CollaborationResponse:
    collab = Collaboration(
        campaign_id=dto.campaign_id,
        brand_id=dto.brand_id,
        creator_id=dto.creator_id,
        status="accepted",
    )
    session.add(collab)
    await session.flush()  # assign collab.id
    for spec in dto.deliverables:
        session.add(
            Deliverable(
                collaboration_id=collab.id,
                platform=spec.platform,
                type=spec.type,
                description=spec.description,
                due_on=spec.due_on,
            )
        )
    await session.commit()
    await session.refresh(collab)
    return await _to_response(session, collab)


def _is_participant(collab: Collaboration, user_id: int) -> bool:
    return user_id in (collab.brand_id, collab.creator_id)


async def _participant_collab(
    session: AsyncSession, user_id: int, collaboration_id: int
) -> Collaboration:
    collab = await repo.get_collaboration(session, collaboration_id)
    if collab is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collaboration not found")
    if not _is_participant(collab, user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a participant")
    return collab


async def get_collaboration(
    session: AsyncSession, user_id: int, collaboration_id: int
) -> CollaborationResponse:
    collab = await _participant_collab(session, user_id, collaboration_id)
    return await _to_response(session, collab)


async def list_mine(
    session: AsyncSession, user_id: int
) -> List[CollaborationResponse]:
    rows = await repo.list_for_participant(session, user_id)
    return [await _to_response(session, c) for c in rows]


async def _load_deliverable(
    session: AsyncSession, deliverable_id: int
) -> Tuple[Deliverable, Collaboration]:
    deliverable = await repo.get_deliverable(session, deliverable_id)
    if deliverable is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deliverable not found")
    collab = await repo.get_collaboration(session, deliverable.collaboration_id)
    return deliverable, collab


async def _recompute(session: AsyncSession, collab: Collaboration) -> None:
    deliverables = await repo.list_deliverables(session, collab.id)
    collab.status = next_collab_status([d.status for d in deliverables])
    await session.commit()
    await session.refresh(collab)


async def submit_deliverable(
    session: AsyncSession,
    user_id: int,
    deliverable_id: int,
    file_refs: list,
    note: Optional[str],
) -> CollaborationResponse:
    deliverable, collab = await _load_deliverable(session, deliverable_id)
    if collab.creator_id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the creator can submit")
    if deliverable.status not in ("todo", "changes_requested"):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Deliverable is not open for submission"
        )
    version = await repo.next_submission_version(session, deliverable_id)
    session.add(
        Submission(
            deliverable_id=deliverable_id,
            version=version,
            file_refs=file_refs,
            note=note,
            submitted_by=user_id,
        )
    )
    deliverable.status = "submitted"
    await session.commit()
    await _recompute(session, collab)
    # TODO(E5): emit deliverable.submitted
    return await _to_response(session, collab)


async def review_deliverable(
    session: AsyncSession,
    user_id: int,
    deliverable_id: int,
    decision: str,
    feedback: Optional[str],
) -> CollaborationResponse:
    deliverable, collab = await _load_deliverable(session, deliverable_id)
    if collab.brand_id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the brand can review")
    if deliverable.status != "submitted":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Deliverable is not awaiting review"
        )
    latest = await repo.latest_submission(session, deliverable_id)
    if latest is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nothing submitted to review")
    session.add(
        Review(
            submission_id=latest.id,
            decision=decision,
            feedback=feedback,
            reviewed_by=user_id,
        )
    )
    deliverable.status = "approved" if decision == "approved" else "changes_requested"
    await session.commit()
    await _recompute(session, collab)
    # TODO(E5): emit deliverable.approved / changes.requested
    return await _to_response(session, collab)


async def mark_live(
    session: AsyncSession, user_id: int, deliverable_id: int
) -> CollaborationResponse:
    deliverable, collab = await _load_deliverable(session, deliverable_id)
    if collab.creator_id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the creator can mark live")
    if deliverable.status != "approved":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only an approved deliverable can go live"
        )
    deliverable.status = "live"
    await session.commit()
    await _recompute(session, collab)
    # TODO(E5): emit collaboration.completed when all live
    return await _to_response(session, collab)


async def timeline(
    session: AsyncSession, user_id: int, collaboration_id: int
) -> List[TimelineEntry]:
    await _participant_collab(session, user_id, collaboration_id)
    deliverables = await repo.list_deliverables(session, collaboration_id)
    deliverable_ids = [d.id for d in deliverables]
    submissions = await repo.list_submissions(session, deliverable_ids)
    reviews = await repo.list_reviews(session, [s.id for s in submissions])
    sub_to_deliverable = {s.id: s.deliverable_id for s in submissions}

    entries: List[TimelineEntry] = []
    for s in submissions:
        entries.append(
            TimelineEntry(
                kind="submission",
                deliverable_id=s.deliverable_id,
                at=s.created_at,
                detail={"version": s.version, "note": s.note},
            )
        )
    for r in reviews:
        entries.append(
            TimelineEntry(
                kind="review",
                deliverable_id=sub_to_deliverable.get(r.submission_id),
                at=r.created_at,
                detail={"decision": r.decision, "feedback": r.feedback},
            )
        )
    entries.sort(key=lambda e: e.at)
    return entries
