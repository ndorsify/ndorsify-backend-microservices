"""Data-access layer — analogue of Spring's ``ContentRepository``."""
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.content import Content


async def find_all_by_lookup_text1(session: AsyncSession, text: str) -> List[Content]:
    stmt = select(Content).where(Content.lookup_text1 == text).order_by(Content.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())
