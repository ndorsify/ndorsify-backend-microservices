"""The real Google provider, with Google replaced by a locally signed token.

The stub provider covers the sign-in *flow*; nothing else covers the part that
only runs with real credentials — exchanging a code and verifying an RS256
`id_token`. That verification needs PyJWT's crypto extra, and its absence is
invisible until a live sign-in fails.
"""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.clients import oauth_provider as mod

CLIENT_ID = "test-client.apps.googleusercontent.com"


@pytest.fixture()
def google(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "google_client_id", CLIENT_ID)
    monkeypatch.setattr(settings, "google_client_secret", "secret")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def id_token(**overrides):
        claims = {
            "iss": "https://accounts.google.com",
            "aud": CLIENT_ID,
            "sub": "1098765",
            "email": "person@gmail.com",
            "email_verified": True,
            "name": "A Person",
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
        }
        claims.update(overrides)
        return jwt.encode(claims, key, algorithm="RS256")

    class _Key:
        def __init__(self, k):
            self.key = k

    monkeypatch.setattr(
        mod, "_jwk_client", lambda: type("C", (), {
            "get_signing_key_from_jwt": staticmethod(lambda t: _Key(key.public_key()))
        })()
    )

    def use(token):
        class _Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"id_token": token}

        class _Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, *a, **kw):
                return _Response()

        monkeypatch.setattr(mod.httpx, "AsyncClient", lambda *a, **kw: _Client())

    return id_token, use


@pytest.mark.asyncio
async def test_a_valid_google_token_becomes_an_identity(google):
    id_token, use = google
    use(id_token())
    identity = await mod.GoogleOAuthProvider().identity("code", "https://app/callback")
    assert identity.provider == "google"
    assert identity.provider_user_id == "1098765"
    assert identity.email == "person@gmail.com"
    assert identity.email_verified is True


@pytest.mark.asyncio
async def test_a_token_for_another_client_is_refused(google):
    id_token, use = google
    use(id_token(aud="someone-else.apps.googleusercontent.com"))
    with pytest.raises(jwt.InvalidAudienceError):
        await mod.GoogleOAuthProvider().identity("code", "https://app/callback")


@pytest.mark.asyncio
async def test_a_token_from_another_issuer_is_refused(google):
    id_token, use = google
    use(id_token(iss="https://evil.example.com"))
    with pytest.raises(ValueError):
        await mod.GoogleOAuthProvider().identity("code", "https://app/callback")


@pytest.mark.asyncio
async def test_an_expired_token_is_refused(google):
    id_token, use = google
    use(id_token(exp=int(time.time()) - 60))
    with pytest.raises(jwt.ExpiredSignatureError):
        await mod.GoogleOAuthProvider().identity("code", "https://app/callback")
