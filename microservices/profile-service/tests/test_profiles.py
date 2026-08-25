"""End-to-end tests for profile-service (run against SQLite).

Access tokens are minted locally with the same JWT secret require_auth uses,
standing in for tokens users-service would issue.
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


# --- creator ----------------------------------------------------------------
def test_creator_upsert_creates_then_updates(client):
    # create
    r = client.put(
        "/profiles/creators/me",
        headers=_auth(1, "creator"),
        json={"display_name": "Ada", "niches": ["tech"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user_id"] == 1
    assert body["display_name"] == "Ada"
    assert body["niches"] == ["tech"]

    # update (partial) — bio added, display_name unchanged
    r = client.put(
        "/profiles/creators/me",
        headers=_auth(1, "creator"),
        json={"bio": "Builder of engines"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["display_name"] == "Ada"  # preserved
    assert body["bio"] == "Builder of engines"


def test_creator_completion_percentage(client):
    # 2 of 6 required fields present -> round(2/6*100) = 33
    r = client.put(
        "/profiles/creators/me",
        headers=_auth(2, "creator"),
        json={"display_name": "Grace", "niches": ["systems"]},
    )
    assert r.json()["completion_pct"] == 33

    # all 6 present -> 100
    r = client.put(
        "/profiles/creators/me",
        headers=_auth(2, "creator"),
        json={
            "bio": "b",
            "location": "NYC",
            "languages": ["en"],
            "avatar_url": "http://img/g.png",
        },
    )
    assert r.json()["completion_pct"] == 100


def test_creator_public_get(client):
    assert client.get("/profiles/creators/999").status_code == 404
    client.put(
        "/profiles/creators/me", headers=_auth(3, "creator"), json={"display_name": "Kay"}
    )
    r = client.get("/profiles/creators/3")
    assert r.status_code == 200
    assert r.json()["display_name"] == "Kay"


# --- brand ------------------------------------------------------------------
def test_brand_upsert_and_get(client):
    r = client.put(
        "/profiles/brands/me",
        headers=_auth(10, "brand"),
        json={"company_name": "Acme", "industry": "Retail"},
    )
    assert r.status_code == 200
    assert r.json()["company_name"] == "Acme"

    r = client.get("/profiles/brands/10")
    assert r.status_code == 200
    assert r.json()["industry"] == "Retail"


# --- auth / role guards -----------------------------------------------------
def test_creator_endpoint_requires_creator_role(client):
    # a brand token cannot write a creator profile
    r = client.put(
        "/profiles/creators/me",
        headers=_auth(20, "brand"),
        json={"display_name": "Nope"},
    )
    assert r.status_code == 403


def test_brand_endpoint_requires_brand_role(client):
    r = client.put(
        "/profiles/brands/me",
        headers=_auth(21, "creator"),
        json={"company_name": "Nope"},
    )
    assert r.status_code == 403


def test_upsert_requires_auth(client):
    # missing token -> unauthenticated
    assert client.put(
        "/profiles/creators/me", json={"display_name": "x"}
    ).status_code in (401, 403)
    # malformed token -> 401
    assert client.put(
        "/profiles/creators/me",
        headers={"Authorization": "Bearer nope"},
        json={"display_name": "x"},
    ).status_code == 401
