"""End-to-end tests for messaging-service (run against SQLite).

Access tokens are minted locally with the same JWT secret require_auth uses.
"""
import os

import jwt


def _auth(user_id: int) -> dict:
    token = jwt.encode(
        {"sub": str(user_id), "role": "creator", "type": "access"},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/health").json()["status"] == "UP"


def test_create_conversation_is_idempotent_per_pair(client):
    a = client.post("/conversations", headers=_auth(1), json={"recipient_id": 2})
    assert a.status_code == 200, a.text
    conv_id = a.json()["id"]
    # Same pair from the other side resolves to the same conversation.
    b = client.post("/conversations", headers=_auth(2), json={"recipient_id": 1})
    assert b.json()["id"] == conv_id


def test_cannot_message_yourself(client):
    r = client.post("/conversations", headers=_auth(5), json={"recipient_id": 5})
    assert r.status_code == 400


def test_post_and_list_messages(client):
    conv = client.post(
        "/conversations", headers=_auth(10), json={"recipient_id": 11}
    ).json()
    cid = conv["id"]

    m1 = client.post(
        f"/conversations/{cid}/messages", headers=_auth(10), json={"body": "hello"}
    )
    assert m1.status_code == 200
    assert m1.json()["sender_id"] == 10
    client.post(
        f"/conversations/{cid}/messages", headers=_auth(11), json={"body": "hi back"}
    )

    msgs = client.get(f"/conversations/{cid}/messages", headers=_auth(10)).json()
    assert [m["body"] for m in msgs] == ["hello", "hi back"]  # chronological


def test_empty_body_rejected(client):
    conv = client.post(
        "/conversations", headers=_auth(10), json={"recipient_id": 12}
    ).json()
    r = client.post(
        f"/conversations/{conv['id']}/messages", headers=_auth(10), json={"body": ""}
    )
    assert r.status_code == 422


def test_non_participant_cannot_read_or_post(client):
    conv = client.post(
        "/conversations", headers=_auth(20), json={"recipient_id": 21}
    ).json()
    cid = conv["id"]
    # user 99 is not a participant
    assert client.get(f"/conversations/{cid}/messages", headers=_auth(99)).status_code == 403
    assert client.post(
        f"/conversations/{cid}/messages", headers=_auth(99), json={"body": "x"}
    ).status_code == 403


def test_missing_conversation_404(client):
    assert client.get("/conversations/999999/messages", headers=_auth(1)).status_code == 404


def test_mark_read(client):
    conv = client.post(
        "/conversations", headers=_auth(30), json={"recipient_id": 31}
    ).json()
    cid = conv["id"]
    client.post(f"/conversations/{cid}/messages", headers=_auth(30), json={"body": "yo"})

    # recipient marks the thread read
    assert client.post(f"/conversations/{cid}/read", headers=_auth(31)).status_code == 204
    msgs = client.get(f"/conversations/{cid}/messages", headers=_auth(31)).json()
    assert msgs[0]["read_at"] is not None


def test_list_conversations_orders_by_recent(client):
    # user 40 talks to 41 then 42; 42 is more recent -> should come first
    c1 = client.post("/conversations", headers=_auth(40), json={"recipient_id": 41}).json()
    c2 = client.post("/conversations", headers=_auth(40), json={"recipient_id": 42}).json()
    client.post(f"/conversations/{c1['id']}/messages", headers=_auth(40), json={"body": "a"})
    client.post(f"/conversations/{c2['id']}/messages", headers=_auth(40), json={"body": "b"})

    convs = client.get("/conversations", headers=_auth(40)).json()
    ids = [c["id"] for c in convs]
    assert ids.index(c2["id"]) < ids.index(c1["id"])


def test_requires_auth(client):
    assert client.get("/conversations").status_code in (401, 403)
    assert client.get(
        "/conversations", headers={"Authorization": "Bearer nope"}
    ).status_code == 401
