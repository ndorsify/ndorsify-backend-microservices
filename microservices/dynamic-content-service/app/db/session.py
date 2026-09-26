"""Async engine, session factory, and FastAPI DB dependency."""
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
    """Ensure the schema exists, then seed reference content when empty.

    On Postgres the schema is owned by **Alembic** (`alembic upgrade head`, run
    before the server starts). On SQLite (local poking and the test suite) the
    tables are created directly. Seeding is idempotent and runs on both.
    """
    from .. import models  # noqa: F401
    from .seed import seed_content

    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await seed_content(session)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
