"""Password hashing, JWT access tokens, and opaque-token helpers.

Kept dependency-free of the DB so it can be unit-tested in isolation and, later,
copied into other services that only need to *verify* access tokens.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from .config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- passwords --------------------------------------------------------------
def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


# --- access tokens (JWT) ----------------------------------------------------
def create_access_token(user_id: int, role: Optional[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises ``jwt.PyJWTError`` subclasses on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# --- opaque tokens (refresh / verify / reset) -------------------------------
def generate_opaque_token() -> str:
    """A high-entropy URL-safe secret. Returned to the client once; only its
    SHA-256 hash is stored, so a DB leak does not expose usable tokens."""
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
