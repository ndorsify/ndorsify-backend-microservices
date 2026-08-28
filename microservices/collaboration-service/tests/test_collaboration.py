"""End-to-end tests for collaboration-service (run against SQLite)."""
import os

import jwt

BRAND = 10
CREATOR = 20


def _auth(user_id: int, role: str) -> dict:
    token = jwt.encode(
        {"sub": str(user_id), "role": role, "type": "access"},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _svc() -> dict:
    return {"X-Service-Token": os.environ["SERVICE_TOKEN"]}


def _create(client, brand=BRAND, creator=CREATOR, n=2):
    deliverables = [
        {"platform": "instagram", "type": "post"} for _ in range(n)
    ]
    return client.post(
        "/collaborations",
        headers=_svc(),
        json={
            "campaign_id": 1,
            "brand_id": brand,
            "creator_id": creator,
            "deliverables": deliverables,
        },
    )


def test_health(client):
    assert client.get("/health").json()["status"] == "UP"


def test_create_requires_service_token(client):
    r = client.post("/collaborations", json={"campaign_id": 1, "brand_id": 1, "creator_id": 2})
    assert r.status_code in (401, 403)
    # a user JWT is not a service token
    r = client.post(
        "/collaborations",
        headers=_auth(1, "brand"),
        json={"campaign_id": 1, "brand_id": 1, "creator_id": 2, "deliverables": []},
    )
    assert r.status_code == 401


def test_create_and_visibility(client):
    r = _create(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "accepted"
    assert len(body["deliverables"]) == 2
    assert all(d["status"] == "todo" for d in body["deliverables"])
    cid = body["id"]

    # both participants can see it; a stranger cannot
    assert client.get(f"/collaborations/{cid}", headers=_auth(BRAND, "brand")).status_code == 200
    assert client.get(f"/collaborations/{cid}", headers=_auth(CREATOR, "creator")).status_code == 200
    assert client.get(f"/collaborations/{cid}", headers=_auth(999, "creator")).status_code == 403

    mine = client.get("/collaborations/mine", headers=_auth(CREATOR, "creator")).json()
    assert any(c["id"] == cid for c in mine)


def test_full_submit_review_live_flow(client):
    body = _create(client, brand=30, creator=40, n=2).json()
    cid = body["id"]
    d1, d2 = [d["id"] for d in body["deliverables"]]

    # creator submits d1
    r = client.post(f"/deliverables/{d1}/submit", headers=_auth(40, "creator"),
                    json={"file_refs": ["submissions/k1"], "note": "v1"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"  # d1 submitted, d2 todo

    # brand cannot submit; creator required
    assert client.post(f"/deliverables/{d2}/submit", headers=_auth(30, "brand"),
                       json={"file_refs": []}).status_code == 403

    # brand requests changes on d1, creator resubmits (v2), brand approves
    client.post(f"/deliverables/{d1}/review", headers=_auth(30, "brand"),
                json={"decision": "changes_requested", "feedback": "tweak"})
    client.post(f"/deliverables/{d1}/submit", headers=_auth(40, "creator"),
                json={"file_refs": ["submissions/k2"]})
    client.post(f"/deliverables/{d1}/review", headers=_auth(30, "brand"),
                json={"decision": "approved"})

    # submit + approve d2 -> collaboration becomes approved
    client.post(f"/deliverables/{d2}/submit", headers=_auth(40, "creator"), json={"file_refs": []})
    approved = client.post(f"/deliverables/{d2}/review", headers=_auth(30, "brand"),
                           json={"decision": "approved"})
    assert approved.json()["status"] == "approved"

    # creator marks both live -> collaboration live
    client.post(f"/deliverables/{d1}/mark-live", headers=_auth(40, "creator"))
    live = client.post(f"/deliverables/{d2}/mark-live", headers=_auth(40, "creator"))
    assert live.json()["status"] == "live"

    # timeline has submissions + reviews
    tl = client.get(f"/collaborations/{cid}/timeline", headers=_auth(40, "creator")).json()
    kinds = [e["kind"] for e in tl]
    assert "submission" in kinds and "review" in kinds


def test_illegal_transitions(client):
    body = _create(client, brand=50, creator=60, n=1).json()
    d = body["deliverables"][0]["id"]
    # review before submit -> 409
    assert client.post(f"/deliverables/{d}/review", headers=_auth(50, "brand"),
                       json={"decision": "approved"}).status_code == 409
    # mark-live before approve -> 409
    assert client.post(f"/deliverables/{d}/mark-live", headers=_auth(60, "creator")).status_code == 409
    # only brand reviews
    client.post(f"/deliverables/{d}/submit", headers=_auth(60, "creator"), json={"file_refs": []})
    assert client.post(f"/deliverables/{d}/review", headers=_auth(60, "creator"),
                       json={"decision": "approved"}).status_code == 403
