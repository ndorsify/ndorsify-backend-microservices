"""Test fixtures — run the full stack against a throwaway SQLite database."""
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

    with TestClient(app) as c:  # lifespan creates tables + seeds
        yield c


def teardown_module(module):  # pragma: no cover - cleanup
    try:
        os.remove(_db_path)
    except OSError:
        pass
