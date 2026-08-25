"""Test fixtures.

Point DATABASE_URL at a throwaway SQLite file *before* the app is imported so
the whole stack (models, engine, lifespan create_all) exercises real code paths
without needing a running Postgres.
"""
import os
import tempfile

import pytest

_db_fd, _db_path = tempfile.mkstemp(suffix=".sqlite3")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_db_path}"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    # `with` runs the lifespan (init_db), creating tables on the SQLite file.
    with TestClient(app) as c:
        yield c


def teardown_module(module):  # pragma: no cover - cleanup
    try:
        os.remove(_db_path)
    except OSError:
        pass
