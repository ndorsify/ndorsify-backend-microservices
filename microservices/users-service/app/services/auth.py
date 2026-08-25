"""Auth business logic (P0): register, login, token refresh/rotation, logout,
email verification, and password reset.

All DB expiry timestamps are stored as **naive UTC** to match the DateTime
columns (which use ``func.now()``), avoiding aware/naive comparison errors.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import security
from ..core.config import settings
from ..models.auth import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
)
from ..models.users import Users
from ..repositories import auth as repo
from ..schemas.auth import (
    AuthUser,
    LoginRequest,
    RegisterRequest,
    TokenPair,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_auth_user(user: Users) -> AuthUser:
    return AuthUser(
        id=user.id,
        email=user.email,
        role=user.role,
        email_verified=user.email_verified_at is not None,
    )


async def _issue_tokens(session: AsyncSession, user: Users) -> TokenPair:
    access = security.create_access_token(user.id, user.role)
    raw_refresh = security.generate_opaque_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=security.hash_token(raw_refresh),
            expires_at=_now() + timedelta(days=settings.refresh_token_days),
        )
    )
    await session.commit()
    return TokenPair(access_token=access, refresh_token=raw_refresh)


async def _create_verification(session: AsyncSession, user: Users) -> str:
    raw = security.generate_opaque_token()
    session.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=security.hash_token(raw),
            expires_at=_now() + timedelta(hours=settings.verify_token_hours),
        )
    )
    await session.commit()
    return raw


async def register(
    session: AsyncSession, req: RegisterRequest
) -> Tuple[Users, TokenPair, str]:
    if await repo.get_user_by_email(session, req.email) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = Users(
        email=req.email,
        role=req.role.value,
        password_hash=security.hash_password(req.password),
        is_active=True,
        status="active",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    tokens = await _issue_tokens(session, user)
    raw_verify = await _create_verification(session, user)
    return user, tokens, raw_verify


async def login(session: AsyncSession, req: LoginRequest) -> TokenPair:
    user = await repo.get_user_by_email(session, req.email)
    # Constant-ish message; do not reveal which half was wrong.
    if (
        user is None
        or not user.password_hash
        or not security.verify_password(req.password, user.password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user.status != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is not active")
    return await _issue_tokens(session, user)


async def refresh(session: AsyncSession, raw_refresh: str) -> TokenPair:
    rt = await repo.get_refresh_token(session, security.hash_token(raw_refresh))
    if rt is None or rt.revoked_at is not None or rt.expires_at < _now():
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token"
        )
    # Rotate: revoke the presented token, issue a fresh pair.
    rt.revoked_at = _now()
    user = await repo.get_user_by_id(session, rt.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    await session.commit()
    return await _issue_tokens(session, user)


async def logout(session: AsyncSession, raw_refresh: str) -> None:
    """Idempotent: revoke the refresh token if it is still active."""
    rt = await repo.get_refresh_token(session, security.hash_token(raw_refresh))
    if rt is not None and rt.revoked_at is None:
        rt.revoked_at = _now()
        await session.commit()


async def verify_email(session: AsyncSession, token: str) -> None:
    ev = await repo.get_verification_token(session, security.hash_token(token))
    if ev is None or ev.used_at is not None or ev.expires_at < _now():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invalid or expired verification token"
        )
    user = await repo.get_user_by_id(session, ev.user_id)
    if user is not None:
        user.email_verified_at = _now()
    ev.used_at = _now()
    await session.commit()


async def request_password_reset(
    session: AsyncSession, email: str
) -> Optional[str]:
    """Create a reset token if the email exists. Returns the raw token (for the
    email provider / dev echo), or ``None`` — the caller always responds 204 so
    accounts are not enumerable."""
    user = await repo.get_user_by_email(session, email)
    if user is None:
        return None
    raw = security.generate_opaque_token()
    session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=security.hash_token(raw),
            expires_at=_now() + timedelta(hours=settings.reset_token_hours),
        )
    )
    await session.commit()
    return raw


async def reset_password(session: AsyncSession, token: str, new_password: str) -> None:
    pr = await repo.get_reset_token(session, security.hash_token(token))
    if pr is None or pr.used_at is not None or pr.expires_at < _now():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token"
        )
    user = await repo.get_user_by_id(session, pr.user_id)
    if user is not None:
        user.password_hash = security.hash_password(new_password)
        # Invalidate every existing session on password change.
        await repo.revoke_all_refresh_tokens(session, user.id, _now())
    pr.used_at = _now()
    await session.commit()
