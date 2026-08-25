"""End-to-end tests for the P0 auth module (run against SQLite).

EXPOSE_DEV_TOKENS is on (see conftest), so register echoes a verification token
and forgot-password echoes a reset token — standing in for the not-yet-built
email provider.
"""


def _register(client, email, password="password123", role="creator"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": role},
    )


# --- unit-ish: security helpers --------------------------------------------
def test_password_hash_and_jwt_roundtrip():
    from app.core import security

    h = security.hash_password("secret-pw")
    assert h != "secret-pw"
    assert security.verify_password("secret-pw", h)
    assert not security.verify_password("wrong", h)

    token = security.create_access_token(42, "brand")
    payload = security.decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "brand"
    assert payload["type"] == "access"


# --- register ---------------------------------------------------------------
def test_register_returns_user_and_tokens(client):
    r = _register(client, "ada@ndorsify.io", role="creator")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["email"] == "ada@ndorsify.io"
    assert body["user"]["role"] == "creator"
    assert body["user"]["email_verified"] is False
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["verification_token"]  # dev echo


def test_register_duplicate_email_conflict(client):
    _register(client, "dup@ndorsify.dev")
    r = _register(client, "dup@ndorsify.dev")
    assert r.status_code == 409


def test_register_rejects_short_password(client):
    r = client.post(
        "/auth/register",
        json={"email": "x@ndorsify.dev", "password": "short", "role": "brand"},
    )
    assert r.status_code == 422


# --- login ------------------------------------------------------------------
def test_login_success_and_wrong_password(client):
    _register(client, "grace@ndorsify.dev", password="hopper-pw-1")

    ok = client.post(
        "/auth/login", json={"email": "grace@ndorsify.dev", "password": "hopper-pw-1"}
    )
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    bad = client.post(
        "/auth/login", json={"email": "grace@ndorsify.dev", "password": "nope"}
    )
    assert bad.status_code == 401


def test_login_unknown_email(client):
    r = client.post(
        "/auth/login", json={"email": "ghost@ndorsify.dev", "password": "whatever12"}
    )
    assert r.status_code == 401


# --- /me --------------------------------------------------------------------
def test_me_requires_and_accepts_token(client):
    reg = _register(client, "me@ndorsify.dev").json()
    access = reg["tokens"]["access_token"]

    # missing credentials -> unauthenticated (401/403 depending on FastAPI ver)
    assert client.get("/auth/me").status_code in (401, 403)
    # malformed token -> 401
    assert client.get(
        "/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    ).status_code == 401

    ok = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert ok.status_code == 200
    assert ok.json()["email"] == "me@ndorsify.dev"


# --- refresh rotation -------------------------------------------------------
def test_refresh_rotates_and_revokes_old(client):
    reg = _register(client, "rot@ndorsify.dev").json()
    refresh1 = reg["tokens"]["refresh_token"]

    first = client.post("/auth/refresh", json={"refresh_token": refresh1})
    assert first.status_code == 200
    refresh2 = first.json()["refresh_token"]
    assert refresh2 != refresh1

    # old refresh token is now revoked
    replay = client.post("/auth/refresh", json={"refresh_token": refresh1})
    assert replay.status_code == 401
    # new one still works
    assert client.post("/auth/refresh", json={"refresh_token": refresh2}).status_code == 200


def test_logout_revokes_refresh(client):
    reg = _register(client, "out@ndorsify.dev").json()
    refresh = reg["tokens"]["refresh_token"]

    assert client.post("/auth/logout", json={"refresh_token": refresh}).status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": refresh}).status_code == 401
    # logout is idempotent
    assert client.post("/auth/logout", json={"refresh_token": refresh}).status_code == 204


# --- email verification -----------------------------------------------------
def test_verify_email_flow(client):
    reg = _register(client, "verify@ndorsify.dev").json()
    access = reg["tokens"]["access_token"]
    token = reg["verification_token"]

    assert client.post("/auth/verify-email", json={"token": token}).status_code == 204
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.json()["email_verified"] is True

    # token is single-use
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 400


# --- password reset ---------------------------------------------------------
def test_forgot_and_reset_password(client):
    _register(client, "reset@ndorsify.dev", password="original-pw")

    forgot = client.post("/auth/forgot-password", json={"email": "reset@ndorsify.dev"})
    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]
    assert reset_token

    done = client.post(
        "/auth/reset-password", json={"token": reset_token, "password": "brand-new-pw"}
    )
    assert done.status_code == 204

    # new password works, old one does not
    assert client.post(
        "/auth/login", json={"email": "reset@ndorsify.dev", "password": "brand-new-pw"}
    ).status_code == 200
    assert client.post(
        "/auth/login", json={"email": "reset@ndorsify.dev", "password": "original-pw"}
    ).status_code == 401


def test_forgot_password_unknown_email_is_silent(client):
    # No account enumeration: same 200 shape, no token.
    r = client.post("/auth/forgot-password", json={"email": "nobody@ndorsify.dev"})
    assert r.status_code == 200
    assert r.json()["reset_token"] is None


def test_reset_with_bad_token(client):
    r = client.post(
        "/auth/reset-password", json={"token": "garbage", "password": "whatever123"}
    )
    assert r.status_code == 400
