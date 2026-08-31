"""End-to-end tests for campaign-service (run against SQLite)."""
import os

import jwt


def _auth(user_id: int, role: str) -> dict:
    token = jwt.encode(
        {"sub": str(user_id), "role": role, "type": "access"},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


COMPLETE = {
    "title": "Summer launch",
    "objective": "Drive awareness",
    "deliverables": [{"platform": "instagram", "type": "post", "quantity": 2}],
    "platforms": ["instagram"],
    "budget_amount": 5000,
    "budget_currency": "USD",
    "starts_on": "2026-09-01",
    "ends_on": "2026-09-30",
    "target_audience": {"niches": ["tech"]},
}


def _create(client, brand, payload=None):
    return client.post("/campaigns", headers=_auth(brand, "brand"), json=payload or COMPLETE)


def _create_open(client, brand):
    cid = _create(client, brand).json()["id"]
    client.post(f"/campaigns/{cid}/publish", headers=_auth(brand, "brand"))
    return cid


def test_health(client):
    assert client.get("/health").json()["status"] == "UP"


# --- create / roles ---------------------------------------------------------
def test_create_requires_brand(client):
    r = _create(client, 1)
    assert r.status_code == 200
    assert r.json()["status"] == "draft"
    assert client.post("/campaigns", headers=_auth(2, "creator"), json=COMPLETE).status_code == 403


# --- visibility -------------------------------------------------------------
def test_draft_hidden_from_others(client):
    cid = _create(client, 10).json()["id"]
    assert client.get(f"/campaigns/{cid}", headers=_auth(10, "brand")).status_code == 200
    # a different user cannot see a draft
    assert client.get(f"/campaigns/{cid}", headers=_auth(99, "creator")).status_code == 404


# --- publish state machine --------------------------------------------------
def test_publish_validates_and_opens(client):
    incomplete = client.post(
        "/campaigns", headers=_auth(20, "brand"), json={"title": "Bare"}
    ).json()
    r = client.post(f"/campaigns/{incomplete['id']}/publish", headers=_auth(20, "brand"))
    assert r.status_code == 422  # missing required fields

    cid = _create(client, 20).json()["id"]
    pub = client.post(f"/campaigns/{cid}/publish", headers=_auth(20, "brand"))
    assert pub.status_code == 200
    assert pub.json()["status"] == "open"
    assert pub.json()["published_at"]
    # now visible to others
    assert client.get(f"/campaigns/{cid}", headers=_auth(88, "creator")).status_code == 200
    # cannot publish twice
    assert client.post(f"/campaigns/{cid}/publish", headers=_auth(20, "brand")).status_code == 409


def test_marketplace_lists_only_open(client):
    _create(client, 30)  # draft
    open_id = _create_open(client, 30)
    listing = client.get("/campaigns", headers=_auth(31, "creator")).json()
    ids = [c["id"] for c in listing]
    assert open_id in ids
    assert all(c["status"] == "open" for c in listing)


def test_close(client):
    cid = _create_open(client, 40)
    r = client.post(f"/campaigns/{cid}/close", headers=_auth(40, "brand"))
    assert r.status_code == 200 and r.json()["status"] == "closed"


def test_only_owner_edits(client):
    cid = _create(client, 50).json()["id"]
    assert client.patch(
        f"/campaigns/{cid}", headers=_auth(51, "brand"), json={"title": "Hijack"}
    ).status_code == 403
    ok = client.patch(f"/campaigns/{cid}", headers=_auth(50, "brand"), json={"title": "Renamed"})
    assert ok.status_code == 200 and ok.json()["title"] == "Renamed"


# --- invitations ------------------------------------------------------------
def test_invite_and_respond(client):
    cid = _create_open(client, 60)
    inv = client.post(
        f"/campaigns/{cid}/invitations", headers=_auth(60, "brand"), json={"creator_id": 61}
    )
    assert inv.status_code == 200 and inv.json()["status"] == "pending"
    # duplicate invite blocked
    assert client.post(
        f"/campaigns/{cid}/invitations", headers=_auth(60, "brand"), json={"creator_id": 61}
    ).status_code == 409
    # creator sees it and accepts
    mine = client.get("/invitations/mine", headers=_auth(61, "creator")).json()
    assert any(i["campaign_id"] == cid for i in mine)
    inv_id = inv.json()["id"]
    acc = client.post(
        f"/invitations/{inv_id}/respond", headers=_auth(61, "creator"), json={"decision": "accepted"}
    )
    assert acc.status_code == 200 and acc.json()["status"] == "accepted"
    # cannot respond again
    assert client.post(
        f"/invitations/{inv_id}/respond", headers=_auth(61, "creator"), json={"decision": "declined"}
    ).status_code == 409
    # only the invitee can respond
    inv2 = client.post(
        f"/campaigns/{cid}/invitations", headers=_auth(60, "brand"), json={"creator_id": 62}
    ).json()
    assert client.post(
        f"/invitations/{inv2['id']}/respond", headers=_auth(63, "creator"), json={"decision": "accepted"}
    ).status_code == 403


# --- applications -----------------------------------------------------------
def test_apply_and_decide(client):
    cid = _create_open(client, 70)
    app_res = client.post(
        f"/campaigns/{cid}/applications",
        headers=_auth(71, "creator"),
        json={"proposal": "I'd love to", "proposed_rate": 1200},
    )
    assert app_res.status_code == 200 and app_res.json()["status"] == "submitted"
    # duplicate application blocked
    assert client.post(
        f"/campaigns/{cid}/applications", headers=_auth(71, "creator"), json={"proposal": "again"}
    ).status_code == 409
    # brand reviews and accepts
    apps = client.get(f"/campaigns/{cid}/applications", headers=_auth(70, "brand")).json()
    assert len(apps) == 1
    dec = client.post(
        f"/applications/{app_res.json()['id']}/decide",
        headers=_auth(70, "brand"),
        json={"decision": "accepted"},
    )
    assert dec.status_code == 200 and dec.json()["status"] == "accepted"


def test_cannot_apply_to_draft(client):
    cid = _create(client, 80).json()["id"]  # draft, not open
    assert client.post(
        f"/campaigns/{cid}/applications", headers=_auth(81, "creator"), json={"proposal": "x"}
    ).status_code == 409


def test_marketplace_requires_auth(client):
    assert client.get("/campaigns").status_code in (401, 403)


# --- funding ------------------------------------------------------------
def test_fund_requires_open(client):
    cid = _create(client, 90).json()["id"]  # still draft
    assert client.post(f"/campaigns/{cid}/fund", headers=_auth(90, "brand")).status_code == 409


def test_fund_marks_funded_at_idempotently(client):
    cid = _create_open(client, 91)
    r1 = client.post(f"/campaigns/{cid}/fund", headers=_auth(91, "brand"))
    assert r1.status_code == 200 and r1.json()["funded_at"]
    first_ts = r1.json()["funded_at"]
    r2 = client.post(f"/campaigns/{cid}/fund", headers=_auth(91, "brand"))
    assert r2.status_code == 200 and r2.json()["funded_at"] == first_ts  # idempotent
    assert r2.json()["status"] == "open"  # status untouched by funding


def test_fund_requires_owner(client):
    cid = _create_open(client, 92)
    assert client.post(f"/campaigns/{cid}/fund", headers=_auth(93, "brand")).status_code == 403


# --- validation --------------------------------------------------------
def test_create_rejects_end_before_start(client):
    bad = dict(COMPLETE, starts_on="2026-09-30", ends_on="2026-09-01")
    assert _create(client, 94, bad).status_code == 422


def test_deliverable_usage_and_approval_round_trip(client):
    payload = dict(COMPLETE)
    payload["deliverables"] = [
        {
            "platform": "instagram",
            "type": "post",
            "quantity": 2,
            "usage": "Paid ads 30d",
            "requires_approval": False,
        }
    ]
    r = _create(client, 95, payload)
    assert r.json()["deliverables"][0]["usage"] == "Paid ads 30d"
    assert r.json()["deliverables"][0]["requires_approval"] is False
