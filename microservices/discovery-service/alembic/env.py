"""Alembic environment (async), wired to the app's settings and metadata."""
import asyncio

from alembic import context
import sqlalchemy as sa
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.session import DATABASE_URL, _connect_args
from app.db.base import Base
from app import models  # noqa: F401  (register models on Base.metadata)

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    schema = settings.db_schema
    if connection.dialect.name == "postgresql":
        # The schema has to exist before anything is migrated into it, and
        # alembic_version belongs beside the tables it tracks — otherwise the
        # seven services would share one version table in public and each
        # would think the others' migrations were its own.
        connection.execute(sa.schema.CreateSchema(schema, if_not_exists=True))
        connection.execute(sa.text(f'SET search_path TO "{schema}"'))
        connection.commit()

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=schema if connection.dialect.name == "postgresql" else None,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=_connect_args,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
