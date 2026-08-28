"""Data-access for collaborations, deliverables, submissions, reviews."""
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.collaboration import Collaboration, Deliverable, Review, Submission


async def get_collaboration(
    session: AsyncSession, collaboration_id: int
) -> Optional[Collaboration]:
    return await session.get(Collaboration, collaboration_id)


async def list_for_participant(
    session: AsyncSession, user_id: int
) -> List[Collaboration]:
    result = await session.execute(
        select(Collaboration)
        .where(
            or_(
                Collaboration.brand_id == user_id,
                Collaboration.creator_id == user_id,
            )
        )
        .order_by(Collaboration.created_at.desc())
    )
    return list(result.scalars().all())


async def list_deliverables(
    session: AsyncSession, collaboration_id: int
) -> List[Deliverable]:
    result = await session.execute(
        select(Deliverable)
        .where(Deliverable.collaboration_id == collaboration_id)
        .order_by(Deliverable.id.asc())
    )
    return list(result.scalars().all())


async def get_deliverable(
    session: AsyncSession, deliverable_id: int
) -> Optional[Deliverable]:
    return await session.get(Deliverable, deliverable_id)


async def next_submission_version(
    session: AsyncSession, deliverable_id: int
) -> int:
    result = await session.execute(
        select(func.max(Submission.version)).where(
            Submission.deliverable_id == deliverable_id
        )
    )
    current = result.scalar_one_or_none()
    return (current or 0) + 1


async def latest_submission(
    session: AsyncSession, deliverable_id: int
) -> Optional[Submission]:
    result = await session.execute(
        select(Submission)
        .where(Submission.deliverable_id == deliverable_id)
        .order_by(Submission.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_submissions(
    session: AsyncSession, deliverable_ids: List[int]
) -> List[Submission]:
    if not deliverable_ids:
        return []
    result = await session.execute(
        select(Submission).where(Submission.deliverable_id.in_(deliverable_ids))
    )
    return list(result.scalars().all())


async def list_reviews(
    session: AsyncSession, submission_ids: List[int]
) -> List[Review]:
    if not submission_ids:
        return []
    result = await session.execute(
        select(Review).where(Review.submission_id.in_(submission_ids))
    )
    return list(result.scalars().all())


async def save(session: AsyncSession, obj):
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj
