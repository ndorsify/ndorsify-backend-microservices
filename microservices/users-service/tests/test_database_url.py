"""The provider's URL is not the URL the driver accepts.

Neon (via Vercel) issues `postgres://…?sslmode=require&channel_binding=require`.
Every part of that needs translating, and a miss is invisible until a deploy
runs migrations — which is exactly how channel_binding was found.
"""
from app.db.session import _normalise

NEON = (
    "postgres://neondb_owner:secret@ep-cool-wind-123.us-east-1.aws.neon.tech"
    "/neondb?sslmode=require&channel_binding=require"
)


def test_neon_url_becomes_an_asyncpg_url():
    got = _normalise(NEON)
    assert got.startswith("postgresql+asyncpg://neondb_owner:secret@")
    assert "sslmode" not in got
    assert "channel_binding" not in got
    assert got.endswith("/neondb")


def test_other_query_parameters_survive():
    got = _normalise("postgres://u:p@host/db?sslmode=require&application_name=ndorsify")
    assert "application_name=ndorsify" in got
    assert "sslmode" not in got


def test_sqlite_and_already_correct_urls_are_left_alone():
    assert _normalise("sqlite+aiosqlite:///run.sqlite3") == "sqlite+aiosqlite:///run.sqlite3"
    assert _normalise("postgresql+asyncpg://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"
