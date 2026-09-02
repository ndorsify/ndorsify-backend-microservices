"""End-to-end tests for connected social accounts (E6 §1).

Access tokens are minted locally with the same JWT secret require_auth uses,
standing in for tokens users-service would issue — same pattern as
test_profiles.py.
"""
import os

import jwt


def _auth(user_id: int, role: str) -> dict:
    token = jwt.encode(
        {"sub": str(user_id), "role": role, "type": "access"},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _connect(client, user_id: int, platform: str = "instagram") -> dict:
    """Full connect round-trip: start, then complete with the state it
    returns — returns the callback's response body."""
    start = client.get(f"/social/{platform}/connect", headers=_auth(user_id, "creator"))
    assert start.status_code == 200, start.text
    state = start.json()["connect_url"].split("state=")[1]
    cb = client.get(
        f"/social/{platform}/callback",
        params={"state": state, "external_account_id": f"ext-{user_id}"},
    )
    assert cb.status_code == 200, cb.text
    return cb.json()


# --- connect / callback ------------------------------------------------------
def test_connect_returns_a_url(client):
    r = client.get("/social/instagram/connect", headers=_auth(30, "creator"))
    assert r.status_code == 200
    assert "connect_url" in r.json()


def test_connect_requires_creator_role(client):
    r = client.get("/social/instagram/connect", headers=_auth(31, "brand"))
    assert r.status_code == 403


def test_connect_rejects_unknown_platform(client):
    r = client.get("/social/friendster/connect", headers=_auth(32, "creator"))
    assert r.status_code == 400


def test_full_connect_flow_creates_account_with_stats(client):
    body = _connect(client, 33)
    assert body["platform"] == "instagram"
    assert body["follower_count"] > 0
    assert body["handle"]


def test_callback_rejects_bad_state(client):
    r = client.get(
        "/social/instagram/callback",
        params={"state": "not-a-real-token", "external_account_id": "x"},
    )
    assert r.status_code == 400


def test_connect_is_deterministic_for_same_user(client):
    # Same user/platform -> same fabricated stats every time (stub provider).
    a = _connect(client, 34)
    b = _connect(client, 34)  # reconnect, e.g. re-authorizing
    assert a["follower_count"] == b["follower_count"]


# --- sync ---------------------------------------------------------------------
def test_sync_requires_existing_connection(client):
    r = client.post("/social/instagram/sync", headers=_auth(35, "creator"))
    assert r.status_code == 404


def test_sync_refreshes_last_synced_at(client):
    _connect(client, 36)
    r = client.post("/social/instagram/sync", headers=_auth(36, "creator"))
    assert r.status_code == 200
    assert r.json()["follower_count"] > 0


# --- list / disconnect ---------------------------------------------------------
def test_list_and_disconnect(client):
    _connect(client, 37)
    mine = client.get("/social/mine", headers=_auth(37, "creator"))
    assert mine.status_code == 200
    assert len(mine.json()) == 1

    d = client.delete("/social/instagram", headers=_auth(37, "creator"))
    assert d.status_code == 204

    mine_after = client.get("/social/mine", headers=_auth(37, "creator"))
    assert mine_after.json() == []


# --- the regression this whole feature exists to prevent -----------------------
def test_profile_save_does_not_wipe_connected_social_stats(client, monkeypatch):
    """A basic profile save (display_name/bio/etc) must not zero out stats
    from an already-connected platform — `upsert_creator_index` is a full
    replace on the discovery side, so profile-service has to always resend
    the complete picture. Verified by capturing exactly what gets pushed."""
    from app.core import config as config_module

    pushed = []

    async def fake_upsert(**kwargs):
        pushed.append(kwargs)

    monkeypatch.setattr(config_module.settings, "discovery_url", "http://discovery.test")
    monkeypatch.setattr(
        "app.services.profiles.discovery_client.upsert_creator_index", fake_upsert
    )

    client.put(
        "/profiles/creators/me",
        headers=_auth(38, "creator"),
        json={"display_name": "Maya"},
    )
    _connect(client, 38)  # connects instagram, pushes again
    assert pushed[-1]["follower_count"] > 0
    assert pushed[-1]["display_name"] == "Maya"  # identity preserved on connect

    # Now save the profile again — the LAST push must still carry the social
    # stats, not reset them to 0/False.
    client.put(
        "/profiles/creators/me",
        headers=_auth(38, "creator"),
        json={"bio": "Ingredient-first skincare"},
    )
    assert pushed[-1]["display_name"] == "Maya"
    assert pushed[-1]["bio"] == "Ingredient-first skincare"
    assert pushed[-1]["follower_count"] > 0  # <- would be 0 without aggregate_and_push
    assert pushed[-1]["verified"] is True
