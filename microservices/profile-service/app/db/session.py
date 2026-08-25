"""Async engine, session factory, and FastAPI DB dependency.

profile-service is a skeleton (no models yet — matches the original Java state).
The engine is wired so the first model can be added with no plumbing work.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.config import settings
from .base import Base

engine = create_async_engine(settings.database_url, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    # Postgres schema is owned by Alembic (`alembic upgrade head`). On SQLite
    # (local/dev/tests) create tables directly. Either way this is a no-op until
    # the first model lands under app/models/ — startup wiring is already here.
    if not settings.database_url.startswith("sqlite"):
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
