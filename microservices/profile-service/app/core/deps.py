"""Reusable auth dependencies — verifies access tokens issued by users-service.

Self-contained (needs only the shared JWT secret), mirroring
users-service/app/core/deps.py. There is no shared package in Phase 1, so this
is copied per service by design.
"""
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
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
