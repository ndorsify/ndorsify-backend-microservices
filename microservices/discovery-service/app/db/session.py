"""Async engine, session factory, and FastAPI DB dependency."""
from typing import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.config import settings
from .base import Base


# Query parameters libpq understands and asyncpg does not. Neon's URL carries
# both; passing either through raises TypeError at connect time.
_LIBPQ_ONLY = {"sslmode", "channel_binding", "connect_timeout", "target_session_attrs"}


def _normalise(url: str) -> str:
    """Make a provider-issued Postgres URL usable by SQLAlchemy + asyncpg.

    Vercel and Neon hand out
    `postgres://…?sslmode=require&channel_binding=require` — libpq's spelling.
    SQLAlchemy needs the driver named, and asyncpg rejects libpq-only options
    as unexpected keyword arguments. TLS is requested through connect_args
    instead.
    """
    prefixes = ("postgresql+asyncpg://", "postgresql://", "postgres://")
    if not url.startswith(prefixes):
        # SQLite and anything else: untouched. Round-tripping a URL whose
        # netloc is empty (sqlite+aiosqlite:///file) drops a slash.
        return url
    for prefix in prefixes:
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url[len(prefix):]
            break

    parts = urlsplit(url)
    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in _LIBPQ_ONLY
    ]
    return urlunsplit(parts._replace(query=urlencode(kept)))


DATABASE_URL = _normalise(settings.database_url)
_WANTS_TLS = "sslmode=" in settings.database_url or ".neon.tech" in settings.database_url

# One Postgres for the whole project — Vercel injects a single DATABASE_URL for
# every service — so each service owns a schema instead of a database. The
# schema is carried by the models themselves (db/base.py), deliberately not by
# a connection search_path: the pooled endpoint is PgBouncer in transaction
# mode, where session state does not reliably follow a query to the server
# connection that runs it.
_connect_args = {}
if DATABASE_URL.startswith("postgresql") and _WANTS_TLS:
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
if DATABASE_URL.startswith("postgresql"):
    # Every unqualified table becomes <schema>.<table> at compile time, so the
    # SQL carries the schema and needs no session state to be correct.
    engine = engine.execution_options(
        schema_translate_map={None: settings.db_schema}
    )
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Postgres schema is owned by Alembic (`alembic upgrade head`). On SQLite
    (local/dev/tests) create tables directly."""
    if not settings.database_url.startswith("sqlite"):
        return

    # Import models so they register on Base.metadata before create_all.
    from .. import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
