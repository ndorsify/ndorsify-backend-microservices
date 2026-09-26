"""Social sign-in providers.

Google is the only real one for now. The interface exists so the stub can
stand in wherever credentials don't (tests, local runs, previews) and so a
second provider is a new subclass rather than a new code path — the
`oauth_accounts` table has always been keyed by (provider, provider_user_id).

Nothing here touches the database or issues Ndorsify tokens: a provider's only
job is to turn a redirect into a verified identity.
"""
import hashlib
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from fastapi.concurrency import run_in_threadpool

from ..core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")

_jwks_client: Optional["jwt.PyJWKClient"] = None


def _jwk_client() -> "jwt.PyJWKClient":
    """One client, so Google's signing keys are cached between requests."""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(GOOGLE_JWKS_URL)
    return _jwks_client


@dataclass
class ProviderIdentity:
    """Who the provider says this is."""

    provider: str
    provider_user_id: str
    email: str
    email_verified: bool
    name: Optional[str] = None


class OAuthProvider:
    name = "oauth"

    def authorize_url(self, state: str, redirect_uri: str) -> str:
        raise NotImplementedError

    async def identity(self, code: str, redirect_uri: str) -> ProviderIdentity:
        raise NotImplementedError


class GoogleOAuthProvider(OAuthProvider):
    name = "google"

    def authorize_url(self, state: str, redirect_uri: str) -> str:
        return GOOGLE_AUTH_URL + "?" + urlencode(
            {
                "client_id": settings.google_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                # Ndorsify never acts on the user's behalf, so there is nothing
                # to refresh and no reason to ask for offline access.
                "access_type": "online",
                "prompt": "select_account",
            }
        )

    async def identity(self, code: str, redirect_uri: str) -> ProviderIdentity:
        async with httpx.AsyncClient(timeout=10) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            id_token = token_response.json()["id_token"]

        # Verify the signature against Google's published keys rather than
        # trusting the payload: the code arrived through the user's browser.
        # PyJWKClient fetches over the network synchronously, so it goes to a
        # thread rather than blocking the event loop.
        signing_key = await run_in_threadpool(
            _jwk_client().get_signing_key_from_jwt, id_token
        )
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
            issuer=GOOGLE_ISSUERS[0],
            options={"verify_iss": False},  # checked explicitly below
        )
        if claims.get("iss") not in GOOGLE_ISSUERS:
            raise ValueError("Unexpected token issuer")

        return ProviderIdentity(
            provider=self.name,
            provider_user_id=claims["sub"],
            email=claims["email"],
            email_verified=bool(claims.get("email_verified")),
            name=claims.get("name"),
        )


class StubOAuthProvider(OAuthProvider):
    """Deterministic stand-in: the `code` is treated as the email.

    Lets the whole flow — first sign-in, role choice, returning user, account
    linking — be exercised without Google credentials. Refuses to run unless
    the service is explicitly in stub mode.
    """

    name = "google"

    def authorize_url(self, state: str, redirect_uri: str) -> str:
        return f"{redirect_uri}?code=stub@example.com&state={state}"

    async def identity(self, code: str, redirect_uri: str) -> ProviderIdentity:
        email = code.strip().lower()
        return ProviderIdentity(
            provider=self.name,
            provider_user_id=hashlib.sha256(email.encode()).hexdigest()[:21],
            email=email,
            email_verified=True,
            name=email.split("@")[0],
        )


def get_provider(provider: str) -> OAuthProvider:
    if provider != "google":
        raise ValueError(f"Unsupported provider {provider!r}")
    if settings.google_client_id and settings.google_client_secret:
        return GoogleOAuthProvider()
    if settings.oauth_allow_stub:
        return StubOAuthProvider()
    raise ValueError("Google sign-in is not configured")
