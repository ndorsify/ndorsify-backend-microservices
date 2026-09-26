"""Auth HTTP layer (P0) — /auth.

Email/password + JWT, and Google sign-in. Without Google credentials the
provider routes answer 501, or use a deterministic stub when
OAUTH_ALLOW_STUB is set (dev, tests, previews).
"""
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.deps import Principal, require_auth
from ..db.session import get_session
from ..schemas.auth import (
    AuthUser,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    OAuthCompleteRequest,
    OAuthExchangeRequest,
    OAuthStartResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenPair,
    VerifyEmailRequest,
)
from ..services import auth as service
from ..services import auth as auth_service
from ..services import oauth as oauth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
async def register(
    body: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> RegisterResponse:
    user, tokens, verify_token = await service.register(session, body)
    return RegisterResponse(
        user=service.to_auth_user(user),
        tokens=tokens,
        verification_token=verify_token if settings.expose_dev_tokens else None,
    )


@router.post("/login", response_model=TokenPair)
async def login(
    body: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenPair:
    return await service.login(session, body)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest, session: AsyncSession = Depends(get_session)
) -> TokenPair:
    return await service.refresh(session, body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest, session: AsyncSession = Depends(get_session)
) -> Response:
    await service.logout(session, body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    body: VerifyEmailRequest, session: AsyncSession = Depends(get_session)
) -> Response:
    await service.verify_email(session, body.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    body: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    raw = await service.request_password_reset(session, body.email)
    # Always the same response shape — no account enumeration.
    return MessageResponse(
        reset_token=raw if (settings.expose_dev_tokens and raw) else None
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest, session: AsyncSession = Depends(get_session)
) -> Response:
    await service.reset_password(session, body.token, body.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=AuthUser)
async def me(
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> AuthUser:
    user = await service_get_me(session, principal)
    return service.to_auth_user(user)


async def service_get_me(session: AsyncSession, principal: Principal):
    from fastapi import HTTPException

    from ..repositories import auth as repo

    user = await repo.get_user_by_id(session, principal.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


# --- Social sign-in ---------------------------------------------------------
@router.get("/oauth/{provider}/start", response_model=OAuthStartResponse)
async def oauth_start(provider: str) -> OAuthStartResponse:
    return OAuthStartResponse(authorize_url=oauth_service.start(provider))


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """The provider sends the browser here.

    Neither a token pair nor a signup token goes in the redirect URL — a URL
    ends up in history, logs and referrer headers. The browser carries a
    one-time reference instead and posts it back.
    """
    kind, token = await oauth_service.callback(session, provider, code, state)
    return RedirectResponse(
        f"{settings.app_url.rstrip('/')}/oauth/callback?{kind}={token}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


@router.post("/oauth/exchange", response_model=TokenPair)
async def oauth_exchange(
    body: OAuthExchangeRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    return await oauth_service.exchange(session, body.handoff)


@router.post("/oauth/complete", response_model=RegisterResponse)
async def oauth_complete(
    body: OAuthCompleteRequest,
    session: AsyncSession = Depends(get_session),
) -> RegisterResponse:
    """First sign-in: create the account now that the role is known."""
    user = await oauth_service.complete_signup(session, body.signup, body.role.value)
    tokens = await auth_service._issue_tokens(session, user)
    return RegisterResponse(user=auth_service.to_auth_user(user), tokens=tokens)
