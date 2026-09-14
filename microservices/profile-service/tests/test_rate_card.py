"""End-to-end tests for creator rate cards (Phase 3).

Access tokens are minted locally with the same JWT secret require_auth uses —
same pattern as test_social.py.
"""
import os

import jwt
import pytest


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


def _package(**kw):
    return {
        "name": "Single Reel",
        "price": 1600,
        "description": "1 Reel, 30-45s",
        "turnaround_days": 5,
        "visible": True,
        "items": [{"platform": "instagram", "type": "reel", "quantity": 1}],
        **kw,
    }


# --- owner read / replace ----------------------------------------------------
def test_owner_with_no_card_gets_an_empty_card(client):
    r = client.get("/profiles/creators/me/rate-card", headers=_auth(200))
    assert r.status_code == 200, r.text
    assert r.json() == {"hidden": False, "packages": [], "updated_at": None}


def test_save_then_read_round_trips(client):
    body = {
        "hidden": False,
        "packages": [
            _package(),
            _package(name="Launch bundle", price=3200, visible=False),
        ],
    }
    saved = client.put(
        "/profiles/creators/me/rate-card", headers=_auth(201), json=body
    )
    assert saved.status_code == 200, saved.text

    read = client.get("/profiles/creators/me/rate-card", headers=_auth(201)).json()
    assert [p["name"] for p in read["packages"]] == ["Single Reel", "Launch bundle"]
    assert read["packages"][1]["visible"] is False
    assert read["packages"][0]["items"][0]["type"] == "reel"
    assert read["updated_at"] is not None


def test_save_replaces_the_whole_card(client):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(202),
        json={"hidden": False, "packages": [_package(), _package(name="Second")]},
    )
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(202),
        json={"hidden": True, "packages": [_package(name="Only one")]},
    )

    read = client.get("/profiles/creators/me/rate-card", headers=_auth(202)).json()
    assert [p["name"] for p in read["packages"]] == ["Only one"]
    assert read["hidden"] is True


def test_package_order_is_preserved(client):
    names = ["A", "B", "C"]
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(203),
        json={"hidden": False, "packages": [_package(name=n) for n in names]},
    )
    read = client.get("/profiles/creators/me/rate-card", headers=_auth(203)).json()
    assert [p["name"] for p in read["packages"]] == names


def test_owner_endpoints_require_creator_role(client):
    assert (
        client.get(
            "/profiles/creators/me/rate-card", headers=_auth(204, "brand")
        ).status_code
        == 403
    )
    assert (
        client.put(
            "/profiles/creators/me/rate-card",
            headers=_auth(204, "brand"),
            json={"hidden": False, "packages": []},
        ).status_code
        == 403
    )


def test_invalid_package_is_rejected_by_the_endpoint(client):
    r = client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(205),
        json={"hidden": False, "packages": [_package(price=0)]},
    )
    assert r.status_code == 422


# --- public read -------------------------------------------------------------
def test_public_read_shows_visible_packages_only(client):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(210),
        json={
            "hidden": False,
            "packages": [_package(), _package(name="Hidden one", visible=False)],
        },
    )
    body = client.get("/profiles/creators/210/rate-card").json()
    assert [p["name"] for p in body["packages"]] == ["Single Reel"]


def test_public_read_never_leaks_visibility_fields(client):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(211),
        json={"hidden": False, "packages": [_package()]},
    )
    body = client.get("/profiles/creators/211/rate-card").json()
    assert "hidden" not in body
    assert "visible" not in body["packages"][0]


def test_public_read_of_a_hidden_card_is_empty(client):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(212),
        json={"hidden": True, "packages": [_package()]},
    )
    assert client.get("/profiles/creators/212/rate-card").json() == {"packages": []}


def test_public_read_of_a_missing_card_is_empty_not_404(client):
    r = client.get("/profiles/creators/9999/rate-card")
    assert r.status_code == 200
    assert r.json() == {"packages": []}


# --- discovery push ----------------------------------------------------------
@pytest.fixture()
def pushes(monkeypatch):
    """Capture what would be sent to discovery-service's creator index."""
    captured = []

    async def fake_upsert(**kwargs):
        captured.append(kwargs)

    monkeypatch.setattr(
        "app.clients.discovery.upsert_creator_index", fake_upsert
    )
    return captured


def test_save_pushes_the_lowest_visible_price(client, pushes):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(220),
        json={
            "hidden": False,
            "packages": [
                _package(name="Bundle", price=3200),
                _package(name="Cheapest", price=900),
                _package(name="Invisible", price=100, visible=False),
            ],
        },
    )
    assert pushes[-1]["rate_per_post"] == 900


def test_hidden_card_pushes_zero(client, pushes):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(221),
        json={"hidden": True, "packages": [_package(price=900)]},
    )
    assert pushes[-1]["rate_per_post"] == 0


def test_all_invisible_packages_push_zero(client, pushes):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(222),
        json={"hidden": False, "packages": [_package(price=900, visible=False)]},
    )
    assert pushes[-1]["rate_per_post"] == 0


def test_a_later_profile_save_keeps_the_rate(client, pushes):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(223),
        json={"hidden": False, "packages": [_package(price=900)]},
    )
    client.put(
        "/profiles/creators/me",
        headers=_auth(223),
        json={"display_name": "Ada", "bio": "Skincare"},
    )
    assert pushes[-1]["rate_per_post"] == 900


def test_a_social_connect_keeps_the_rate(client, pushes):
    client.put(
        "/profiles/creators/me/rate-card",
        headers=_auth(224),
        json={"hidden": False, "packages": [_package(price=900)]},
    )
    start = client.get("/social/instagram/connect", headers=_auth(224))
    state = start.json()["connect_url"].split("state=")[1]
    client.get(
        "/social/instagram/callback",
        params={"state": state, "external_account_id": "ext-224"},
    )
    assert pushes[-1]["rate_per_post"] == 900
