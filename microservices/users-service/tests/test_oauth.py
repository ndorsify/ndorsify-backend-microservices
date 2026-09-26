"""Google sign-in, exercised through the stub provider.

The stub treats the `code` as the email, so the whole shape — first sign-in,
role choice, returning user, linking to a password account — is testable
without Google credentials.
"""
import os
from urllib.parse import parse_qs, urlparse

import pytest

os.environ.setdefault("OAUTH_ALLOW_STUB", "true")


@pytest.fixture(autouse=True)
def _stub_enabled():
    from app.core.config import settings

    previous = settings.oauth_allow_stub
    settings.oauth_allow_stub = True
    yield
    settings.oauth_allow_stub = previous


def _start(client):
    r = client.get("/auth/oauth/google/start")
    assert r.status_code == 200, r.text
    return parse_qs(urlparse(r.json()["authorize_url"]).query)["state"][0]


def _callback(client, email, state=None):
    """Returns (kind, token) parsed out of the redirect the provider triggers."""
    r = client.get(
        "/auth/oauth/google/callback",
        params={"code": email, "state": state or _start(client)},
        follow_redirects=False,
    )
    assert r.status_code == 307, r.text
    q = parse_qs(urlparse(r.headers["location"]).query)
    kind = "handoff" if "handoff" in q else "signup"
    return kind, q[kind][0]


def test_first_sign_in_asks_for_a_role_before_creating_anything(client):
    kind, signup = _callback(client, "newcomer@example.com")
    assert kind == "signup"

    # Nothing exists yet: the password flow still says no such account.
    assert client.post(
        "/auth/login", json={"email": "newcomer@example.com", "password": "whatever"}
    ).status_code == 401

    r = client.post("/auth/oauth/complete", json={"signup": signup, "role": "brand"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["role"] == "brand"
    assert body["user"]["email_verified"] is True  # Google verified it
    assert body["tokens"]["access_token"]


def test_returning_user_signs_straight_in(client):
    _, signup = _callback(client, "returning@example.com")
    client.post("/auth/oauth/complete", json={"signup": signup, "role": "creator"})

    kind, handoff = _callback(client, "returning@example.com")
    assert kind == "handoff"
    r = client.post("/auth/oauth/exchange", json={"handoff": handoff})
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]


def test_google_links_to_an_existing_password_account(client):
    client.post(
        "/auth/register",
        json={
            "email": "both@example.com",
            "password": "Passw0rd!x",
            "role": "creator",
            "name": "both",
        },
    )
    kind, handoff = _callback(client, "both@example.com")
    assert kind == "handoff", "an existing account should be linked, not duplicated"
    assert client.post("/auth/oauth/exchange", json={"handoff": handoff}).status_code == 200
    # The password still works — linking adds a way in, it doesn't replace one.
    assert client.post(
        "/auth/login", json={"email": "both@example.com", "password": "Passw0rd!x"}
    ).status_code == 200


def test_a_signup_token_cannot_be_reused(client):
    _, signup = _callback(client, "once@example.com")
    assert client.post(
        "/auth/oauth/complete", json={"signup": signup, "role": "creator"}
    ).status_code == 200
    again = client.post("/auth/oauth/complete", json={"signup": signup, "role": "brand"})
    assert again.status_code == 409, again.text


def test_tokens_are_not_interchangeable(client):
    _, signup = _callback(client, "mixed@example.com")
    # A signup token is not a handoff token.
    assert client.post("/auth/oauth/exchange", json={"handoff": signup}).status_code == 400

    client.post("/auth/oauth/complete", json={"signup": signup, "role": "creator"})
    _, handoff = _callback(client, "mixed@example.com")
    assert client.post(
        "/auth/oauth/complete", json={"signup": handoff, "role": "brand"}
    ).status_code == 400


def test_a_forged_state_is_refused(client):
    r = client.get(
        "/auth/oauth/google/callback",
        params={"code": "forged@example.com", "state": "not-a-real-state"},
        follow_redirects=False,
    )
    assert r.status_code == 400


def test_a_provider_account_gets_no_password_reset(client):
    _, signup = _callback(client, "nopassword@example.com")
    client.post("/auth/oauth/complete", json={"signup": signup, "role": "creator"})

    r = client.post("/auth/forgot-password", json={"email": "nopassword@example.com"})
    assert r.status_code == 200, r.text
    # Same answer as for an unknown address, and no token minted — a reset would
    # quietly attach a password to a Google account.
    assert r.json().get("reset_token") is None
