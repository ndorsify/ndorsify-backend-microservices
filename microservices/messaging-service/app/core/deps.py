"""Reusable auth dependencies — verifies access tokens issued by users-service.

Self-contained (needs only the shared JWT secret); copied per service by design
(no shared package in Phase 1).
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
