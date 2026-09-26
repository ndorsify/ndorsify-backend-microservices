"""Test fixtures — run the full stack against a throwaway SQLite database."""
import os
import shutil
import tempfile

import pytest

_db_fd, _db_path = tempfile.mkstemp(suffix=".sqlite3")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_db_path}"
# Deterministic JWT secret so tests can mint access tokens require_auth accepts.
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long!")
# Uploaded bytes land in a throwaway directory, never the working tree.
_media_root = tempfile.mkdtemp(prefix="media-store-")
os.environ["MEDIA_ROOT"] = _media_root


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:  # lifespan creates tables + seeds
        yield c


def teardown_module(module):  # pragma: no cover - cleanup
    shutil.rmtree(_media_root, ignore_errors=True)
    try:
        os.remove(_db_path)
    except OSError:
        pass
