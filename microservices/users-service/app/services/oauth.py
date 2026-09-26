"""Google sign-in.

Three cases come back from a provider callback:

* the provider identity is already linked  -> sign in
* the email matches an existing account    -> link, then sign in
* nobody we know                           -> we still don't know whether they
  are a brand or a creator, and Google can't tell us, so the account is not
  created yet: the caller gets a short-lived signup token and must come back
  with a role.

Neither the token pair nor the signup token travel in the redirect URL — the
browser gets a one-time handoff instead, which is exchanged over POST. A URL
lands in history, logs and referrers; a refresh token should not.
"""
import hashlib
import hmac
import secrets
import time
from typing import Optional, Tuple

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..clients.oauth_provider import ProviderIdentity, get_provider
from ..core import security
from ..core.config import settings
from ..models.auth import OAuthAccount
from ..models.users import Users
from ..repositories import auth as repo
from ..schemas.auth import TokenPair
from .auth import _issue_tokens, _now

_STATE_TTL = 600  # the round trip through Google
_HANDOFF_TTL = 120  # browser redirect -> POST /exchange
_SIGNUP_TTL = 900  # long enough to pick a role


def _sign(payload: dict, ttl: int) -> str:
    return jwt.encode(
        {**payload, "exp": int(time.time()) + ttl},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def _verify(token: str, kind: str) -> dict:
    try:
        claims = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This link has expired")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid link")
    if claims.get("typ") != kind:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid link")
    return claims


def redirect_uri(provider: str) -> str:
    """Where the provider sends the browser back. Must match the client's
    registered redirect exactly, so it is built from configuration, not from
    the incoming request."""
    return f"{settings.api_base_url.rstrip('/')}/auth/oauth/{provider}/callback"


STATE_COOKIE = "ndorsify_oauth_nonce"


def start(provider: str) -> Tuple[str, str]:
    """Returns (authorize_url, nonce).

    The nonce goes to the browser as a cookie and its hash into the signed
    state. A signature alone only proves *we* minted the state, not that this
    browser asked for it — without the pairing, anyone can fetch a state, hand
    a victim a crafted callback URL, and have the victim's browser silently
    finish signing in as the attacker's Google account.
    """
    try:
        client = get_provider(provider)
    except ValueError as exc:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, str(exc))
    nonce = secrets.token_urlsafe(32)
    state = _sign(
        {
            "typ": "oauth_state",
            "provider": provider,
            "nonce": hashlib.sha256(nonce.encode()).hexdigest(),
        },
        _STATE_TTL,
    )
    return client.authorize_url(state, redirect_uri(provider)), nonce


async def _link_or_find(
    session: AsyncSession, identity: ProviderIdentity
) -> Optional[Users]:
    linked = await session.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == identity.provider,
            OAuthAccount.provider_user_id == identity.provider_user_id,
        )
    )
    account = linked.scalar_one_or_none()
    if account is not None:
        return await repo.get_user_by_id(session, account.user_id)

    # Same person, signed up with a password before: link rather than collide
    # on the unique email. Only ever on a provider-verified address.
    existing = await repo.get_user_by_email(session, identity.email)
    if existing is not None:
        if not identity.email_verified:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "That email is already registered. Sign in with your password.",
            )
        session.add(
            OAuthAccount(
                user_id=existing.id,
                provider=identity.provider,
                provider_user_id=identity.provider_user_id,
            )
        )
        if existing.email_verified_at is None:
            existing.email_verified_at = _now()
        await session.commit()
        return existing
    return None


async def callback(
    session: AsyncSession,
    provider: str,
    code: str,
    state: str,
    nonce: Optional[str],
) -> Tuple[str, str]:
    """Returns (kind, token) where kind is 'handoff' or 'signup'."""
    claims = _verify(state, "oauth_state")
    if claims.get("provider") != provider:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid link")

    # The state must be the one this browser was given.
    expected = claims.get("nonce") or ""
    presented = hashlib.sha256(nonce.encode()).hexdigest() if nonce else ""
    if not expected or not hmac.compare_digest(expected, presented):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "This sign-in didn't start in this browser. Try again.",
        )

    try:
        client = get_provider(provider)
        identity = await client.identity(code, redirect_uri(provider))
    except ValueError as exc:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, str(exc))
    except Exception:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Could not complete sign-in with the provider"
        )

    if not identity.email_verified:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Your provider has not verified that address"
        )

    user = await _link_or_find(session, identity)
    if user is not None:
        return "handoff", _sign(
            {"typ": "oauth_handoff", "sub": str(user.id)}, _HANDOFF_TTL
        )

    return "signup", _sign(
        {
            "typ": "oauth_signup",
            "provider": identity.provider,
            "provider_user_id": identity.provider_user_id,
            "email": identity.email,
        },
        _SIGNUP_TTL,
    )


async def exchange(session: AsyncSession, handoff: str) -> TokenPair:
    claims = _verify(handoff, "oauth_handoff")
    user = await repo.get_user_by_id(session, int(claims["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid link")
    return await _issue_tokens(session, user)


async def complete_signup(session: AsyncSession, signup: str, role: str) -> Users:
    """Create the account now that the role is known."""
    claims = _verify(signup, "oauth_signup")

    if await repo.get_user_by_email(session, claims["email"]) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = Users(
        email=claims["email"],
        role=role,
        # No password: this account signs in through the provider. Reset is
        # refused for it, rather than silently mailing a link that sets one.
        password_hash=None,
        is_active=True,
        status="active",
        # The provider verified the address; that is the whole point of using it.
        email_verified_at=_now(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    session.add(
        OAuthAccount(
            user_id=user.id,
            provider=claims["provider"],
            provider_user_id=claims["provider_user_id"],
        )
    )
    await session.commit()
    return user
