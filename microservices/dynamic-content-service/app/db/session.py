"""Async engine, session factory, and FastAPI DB dependency."""
import re
from typing import AsyncGenerator

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.config import settings
from .base import Base


def _normalise(url: str) -> str:
    """Make a provider-issued Postgres URL usable by SQLAlchemy + asyncpg.

    Vercel and Neon hand out `postgres://…?sslmode=require`, which is libpq's
    spelling: SQLAlchemy needs the driver named, and asyncpg rejects `sslmode`
    as an unknown option. TLS is requested through connect_args instead.
    """
    for prefix in ("postgresql+asyncpg://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url[len(prefix):]
            break
    return re.sub(r"[?&]sslmode=[^&]*", "", url)


DATABASE_URL = _normalise(settings.database_url)
_WANTS_TLS = "sslmode=" in settings.database_url or ".neon.tech" in settings.database_url

# One Postgres for the whole project — Vercel injects a single DATABASE_URL for
# every service — so each service gets its own schema instead of its own
# database, and every connection starts with its search_path pointed there.
_connect_args = {}
if DATABASE_URL.startswith("postgresql"):
    _connect_args["server_settings"] = {"search_path": settings.db_schema}
    if _WANTS_TLS:
        _connect_args["ssl"] = True


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

engine = create_async_engine(DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)
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
