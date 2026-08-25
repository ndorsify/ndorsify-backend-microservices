"""Auth HTTP layer (P0) — /auth.

Email/password + JWT is fully implemented. Social OAuth endpoints are stubbed
(501) because they require provider apps; the flow is specified in
docs/plans/technical-specifications/p0-foundation.md.
"""
from fastapi import APIRouter, Depends, Response, status
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
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenPair,
    VerifyEmailRequest,
)
from ..services import auth as service

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


# --- Social OAuth (stubbed in P0) ------------------------------------------
@router.get("/oauth/{provider}/start", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def oauth_start(provider: str) -> dict:
    return {"detail": f"OAuth for {provider!r} is not implemented yet (P0 stub)."}


@router.get("/oauth/{provider}/callback", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def oauth_callback(provider: str) -> dict:
    return {"detail": f"OAuth for {provider!r} is not implemented yet (P0 stub)."}
