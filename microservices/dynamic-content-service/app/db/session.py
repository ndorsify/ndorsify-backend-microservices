"""Async engine, session factory, and FastAPI DB dependency."""
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
