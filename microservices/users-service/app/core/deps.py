"""Reusable FastAPI auth dependencies.

This module is intentionally self-contained (only needs the JWT secret/public
key and the shared service token) so it can be **copied into every service** —
there is no shared package in Phase 1. See the P0 foundation spec.
"""
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .security import decode_access_token

_bearer = HTTPBearer(auto_error=True)


@dataclass
class Principal:
    """The authenticated caller, derived from a validated access token."""

    user_id: int
    role: Optional[str]


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Principal:
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    return Principal(user_id=int(payload["sub"]), role=payload.get("role"))


def require_role(*roles: str):
    """Dependency factory: require the caller to hold one of ``roles``."""

    def _dep(principal: Principal = Depends(require_auth)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Insufficient role for this action"
            )
        return principal

    return _dep


def require_service_token(x_service_token: Optional[str] = Header(default=None)) -> None:
    """Guard for internal, service-to-service endpoints (not user-facing)."""
    if not x_service_token or x_service_token != settings.service_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid service token")
