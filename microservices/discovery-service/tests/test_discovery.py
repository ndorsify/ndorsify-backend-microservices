"""End-to-end tests for discovery-service (run against SQLite).

Access tokens are minted locally with the same JWT secret require_auth uses; the
internal ingest is called with the shared service token.
"""
import os

import jwt


def _auth(user_id: int, role: str = "brand") -> dict:
    token = jwt.encode(
        {"sub": str(user_id), "role": role, "type": "access"},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _svc() -> dict:
    return {"X-Service-Token": os.environ["SERVICE_TOKEN"]}


def _ingest(client, **kw):
    body = {"user_id": kw["user_id"], "display_name": kw.get("display_name"),
            "niches": kw.get("niches", []), "location": kw.get("location"),
            "follower_count": kw.get("follower_count", 0),
            "engagement_rate": kw.get("engagement_rate", 0.0),
            "rate_per_post": kw.get("rate_per_post", 0),
            "avg_rating": kw.get("avg_rating", 0.0)}
    return client.put("/internal/creator-index", headers=_svc(), json=body)


def test_health(client):
    assert client.get("/health").json()["status"] == "UP"


# --- internal ingest --------------------------------------------------------
def test_ingest_requires_service_token(client):
    r = client.put("/internal/creator-index", json={"user_id": 1, "niches": []})
    assert r.status_code in (401, 403)
    r = client.put(
        "/internal/creator-index",
        headers={"X-Service-Token": "wrong"},
        json={"user_id": 1, "niches": []},
    )
    assert r.status_code == 401


def test_ingest_upsert_is_idempotent(client):
    a = _ingest(client, user_id=1, display_name="Ada", follower_count=100)
    assert a.status_code == 200, a.text
    # re-ingest updates in place (no duplicate)
    b = _ingest(client, user_id=1, display_name="Ada L.", follower_count=200)
    assert b.json()["display_name"] == "Ada L."
    results = client.get("/discovery/creators", headers=_auth(9)).json()
    assert sum(1 for r in results if r["user_id"] == 1) == 1


# --- search -----------------------------------------------------------------
def test_search_filters_and_sort(client):
    _ingest(client, user_id=10, display_name="Tech Ada", niches=["tech"], follower_count=5000)
    _ingest(client, user_id=11, display_name="Foodie Bea", niches=["food"], follower_count=50000)
    _ingest(client, user_id=12, display_name="Tech Cleo", niches=["tech", "ai"], follower_count=1000)

    # niche filter
    tech = client.get("/discovery/creators", headers=_auth(9), params={"niche": "tech"}).json()
    assert {r["user_id"] for r in tech} == {10, 12}

    # text query on display_name (DB accumulates across tests, so assert
    # membership rather than exact equality)
    ada_ids = [r["user_id"] for r in
               client.get("/discovery/creators", headers=_auth(9), params={"q": "ada"}).json()]
    assert 10 in ada_ids and 11 not in ada_ids and 12 not in ada_ids

    # follower range
    big = client.get(
        "/discovery/creators", headers=_auth(9), params={"min_followers": 4000}
    ).json()
    assert {r["user_id"] for r in big} == {10, 11}

    # sort by followers desc (default) — Bea (50k) before Ada (5k)
    ordered = client.get("/discovery/creators", headers=_auth(9), params={"niche": []}).json()
    ids = [r["user_id"] for r in ordered]
    assert ids.index(11) < ids.index(10) < ids.index(12)


def test_search_requires_auth(client):
    assert client.get("/discovery/creators").status_code in (401, 403)


# --- shortlists -------------------------------------------------------------
def test_shortlist_flow(client):
    created = client.post(
        "/discovery/shortlists", headers=_auth(100, "brand"), json={"name": "Q3 picks"}
    )
    assert created.status_code == 200, created.text
    sid = created.json()["id"]

    # add two creators (idempotent on repeat)
    client.post(f"/discovery/shortlists/{sid}/items", headers=_auth(100, "brand"), json={"creator_id": 10})
    client.post(f"/discovery/shortlists/{sid}/items", headers=_auth(100, "brand"), json={"creator_id": 11})
    dup = client.post(f"/discovery/shortlists/{sid}/items", headers=_auth(100, "brand"), json={"creator_id": 10})
    assert dup.json()["creator_ids"] == [10, 11]

    got = client.get(f"/discovery/shortlists/{sid}", headers=_auth(100, "brand"))
    assert got.json()["creator_ids"] == [10, 11]


def test_shortlist_requires_brand_role(client):
    r = client.post(
        "/discovery/shortlists", headers=_auth(101, "creator"), json={"name": "nope"}
    )
    assert r.status_code == 403


def test_shortlist_owner_only(client):
    sid = client.post(
        "/discovery/shortlists", headers=_auth(200, "brand"), json={"name": "mine"}
    ).json()["id"]
    # a different brand cannot read it
    assert client.get(f"/discovery/shortlists/{sid}", headers=_auth(201, "brand")).status_code == 403


def test_shortlist_not_found(client):
    assert client.get(
        "/discovery/shortlists/999999", headers=_auth(100, "brand")
    ).status_code == 404


def test_list_shortlists(client):
    client.post("/discovery/shortlists", headers=_auth(300, "brand"), json={"name": "A"})
    client.post("/discovery/shortlists", headers=_auth(300, "brand"), json={"name": "B"})
    r = client.get("/discovery/shortlists", headers=_auth(300, "brand"))
    assert r.status_code == 200
    names = [s["name"] for s in r.json() if s["brand_id"] == 300]
    assert set(names) >= {"A", "B"}
    # creators cannot list shortlists
    assert (
        client.get("/discovery/shortlists", headers=_auth(301, "creator")).status_code
        == 403
    )


# --- rate filter -------------------------------------------------------------
def test_rate_filters_exclude_creators_without_a_rate(client):
    _ingest(client, user_id=901, display_name="Priced", rate_per_post=1200)
    _ingest(client, user_id=902, display_name="Unpriced", rate_per_post=0)

    names = lambda r: {c["display_name"] for c in r.json()}

    max_only = client.get("/discovery/creators", params={"max_rate": 2000}, headers=_auth(1))
    assert "Priced" in names(max_only)
    assert "Unpriced" not in names(max_only)

    min_only = client.get("/discovery/creators", params={"min_rate": 100}, headers=_auth(1))
    assert "Unpriced" not in names(min_only)


def test_unfiltered_search_still_includes_unpriced_creators(client):
    _ingest(client, user_id=903, display_name="Also unpriced", rate_per_post=0)
    r = client.get("/discovery/creators", headers=_auth(1))
    assert "Also unpriced" in {c["display_name"] for c in r.json()}
