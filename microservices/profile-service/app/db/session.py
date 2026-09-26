"""Async engine, session factory, and FastAPI DB dependency.

profile-service is a skeleton (no models yet — matches the original Java state).
The engine is wired so the first model can be added with no plumbing work.
"""
from typing import AsyncGenerator

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.config import settings
from .base import Base

# Postgres-facing settings, harmless on SQLite:
# * pool_pre_ping discards connections a pooler or an idle timeout closed
#   underneath us, which is the usual "server closed the connection
#   unexpectedly" on Neon and friends.
# * DB_NULL_POOL=true turns pooling off entirely — the right setting once this
#   runs as short-lived serverless instances, where a per-instance pool just
#   holds connections nobody reuses.
_engine_kwargs = {"future": True, "pool_pre_ping": True}
if settings.db_null_pool:
    _engine_kwargs = {"future": True, "poolclass": NullPool}

engine = create_async_engine(settings.database_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    # Postgres schema is owned by Alembic (`alembic upgrade head`). On SQLite
    # (local/dev/tests) create tables directly.
    if not settings.database_url.startswith("sqlite"):
        return

    # Import models so they register on Base.metadata before create_all.
    from .. import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
