"""Data-access layer — the SQLAlchemy analogue of Spring's ``UsersRepository``."""
from typing import List, Optional

from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.users import Users


async def find_all(
    session: AsyncSession, *, offset: int, limit: int, sort_column: str
) -> List[Users]:
    order_col = getattr(Users, sort_column)
    stmt = select(Users).order_by(asc(order_col)).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Users))
    return int(result.scalar_one())


async def find_by_id(session: AsyncSession, user_id: int) -> Optional[Users]:
    return await session.get(Users, user_id)


async def save(session: AsyncSession, user: Users) -> Users:
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
