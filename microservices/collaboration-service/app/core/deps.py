"""Reusable auth dependencies (copied per service; no shared package in Phase 1).

Provides user-token auth (require_auth / require_role) and a service-token guard
for internal endpoints such as the creator-index ingest.
"""
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

_bearer = HTTPBearer(auto_error=True)


@dataclass
class Principal:
    user_id: int
    role: Optional[str]


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Principal:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    return Principal(user_id=int(payload["sub"]), role=payload.get("role"))


def require_role(*roles: str):
    def _dep(principal: Principal = Depends(require_auth)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Insufficient role for this action"
            )
        return principal

    return _dep


def require_service_token(x_service_token: Optional[str] = Header(default=None)) -> None:
    if not x_service_token or x_service_token != settings.service_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid service token")
