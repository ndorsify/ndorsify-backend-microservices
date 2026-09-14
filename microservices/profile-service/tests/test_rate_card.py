"""End-to-end tests for creator rate cards (Phase 3).

Access tokens are minted locally with the same JWT secret require_auth uses —
same pattern as test_social.py.
"""
import os

import jwt


def _auth(user_id: int, role: str = "creator") -> dict:
    token = jwt.encode(
        {"sub": str(user_id), "role": role, "type": "access"},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_rate_card_tables_are_registered():
    from app import models  # noqa: F401  (registers models on the metadata)
    from app.db.base import Base

    assert "rate_cards" in Base.metadata.tables
    packages = Base.metadata.tables["rate_card_packages"]
    assert {
        "rate_card_id",
        "sort_order",
        "name",
        "price",
        "description",
        "turnaround_days",
        "visible",
        "items",
    } <= set(packages.columns.keys())
