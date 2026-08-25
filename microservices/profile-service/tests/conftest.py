"""Test fixtures — run against a throwaway SQLite database."""
import os
import tempfile

import pytest

_db_fd, _db_path = tempfile.mkstemp(suffix=".sqlite3")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_db_path}"
# Deterministic JWT secret so tests can mint access tokens require_auth accepts.
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long!")


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


def teardown_module(module):  # pragma: no cover - cleanup
    try:
        os.remove(_db_path)
    except OSError:
        pass
