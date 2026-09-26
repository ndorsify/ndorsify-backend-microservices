"""Auth request/response DTOs (P0)."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    brand = "brand"
    creator = "creator"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthUser(BaseModel):
    id: int
    email: Optional[str] = None
    role: Optional[str] = None
    email_verified: bool = False


class RegisterResponse(BaseModel):
    user: AuthUser
    tokens: TokenPair
    # DEV/TEST ONLY (settings.expose_dev_tokens) — no email provider yet.
    verification_token: Optional[str] = None


class MessageResponse(BaseModel):
    status: str = "ok"
    # DEV/TEST ONLY (settings.expose_dev_tokens).
    reset_token: Optional[str] = None


# --- Social sign-in ---
class OAuthStartResponse(BaseModel):
    authorize_url: str


class OAuthExchangeRequest(BaseModel):
    handoff: str


class OAuthCompleteRequest(BaseModel):
    """First sign-in: the provider gave us an identity, not a role."""

    signup: str
    role: Role
