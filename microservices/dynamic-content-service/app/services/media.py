"""Media storage (E7 §1) — signed upload/download URLs over a key namespace.

The client never uploads through an authenticated API call: it asks for a
signed URL, PUTs the bytes to it, and hands the returned ``key`` to whichever
service stores the reference (collaboration submissions' ``file_refs``, the
media kit, an avatar).

ponytail: the bytes land on the local filesystem under ``MEDIA_ROOT`` instead
of S3, so local dev needs no MinIO/cloud account. Everything client-facing —
sign-upload → PUT → key → sign-download — is the shape S3 presigning gives,
so swapping the store means rewriting only ``save``/``open_key``/``exists``
here. Upgrade when there is more than one API instance, since two instances do
not share a disk.
"""
import mimetypes
import os
import time
import uuid
from pathlib import Path
from typing import Optional

import jwt

from ..core.config import settings

# Private by default; only these ever get a signed upload URL.
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "video/mp4",
    "video/quicktime",
    "application/pdf",
}

# scope -> whether the caller supplies the id segment (else it's their user id).
SCOPES = {
    "submissions": True,   # submissions/{collaboration_id}/...
    "media-kit": False,    # media-kit/{user_id}/...
    "avatars": False,      # avatars/{user_id}/...
}


class MediaError(Exception):
    """Invalid sign/upload request — routers turn this into a 400."""


def _root() -> Path:
    return Path(settings.media_root).resolve()


def build_key(*, scope: str, user_id: int, ref_id: Optional[str], content_type: str) -> str:
    if scope not in SCOPES:
        raise MediaError(f"Unknown scope '{scope}'")
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise MediaError(f"Content type '{content_type}' is not allowed")
    if SCOPES[scope]:
        if not ref_id or not str(ref_id).isdigit():
            raise MediaError(f"scope '{scope}' needs a numeric ref_id")
        segment = str(ref_id)
    else:
        segment = str(user_id)
    ext = mimetypes.guess_extension(content_type) or ""
    return f"{scope}/{segment}/{uuid.uuid4().hex}{ext}"


def _sign(payload: dict) -> str:
    return jwt.encode(
        {**payload, "exp": int(time.time()) + settings.media_url_ttl_seconds},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def _verify(token: str, kind: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise MediaError("This link has expired")
    except jwt.PyJWTError:
        raise MediaError("Invalid link")
    if payload.get("typ") != kind:
        raise MediaError("Invalid link")
    return payload


def sign_upload(
    *, scope: str, user_id: int, ref_id: Optional[str], content_type: str, size_bytes: int
) -> dict:
    if size_bytes <= 0:
        raise MediaError("size_bytes must be positive")
    if size_bytes > settings.media_max_bytes:
        raise MediaError(f"File exceeds the {settings.media_max_bytes} byte limit")
    key = build_key(
        scope=scope, user_id=user_id, ref_id=ref_id, content_type=content_type
    )
    token = _sign(
        {"typ": "upload", "k": key, "ct": content_type, "max": size_bytes, "sub": str(user_id)}
    )
    return {"key": key, "token": token, "content_type": content_type}


def sign_download(key: str) -> str:
    if not exists(key):
        raise MediaError("No such key")
    return _sign({"typ": "download", "k": key})


def save(token: str, body: bytes, content_type: str) -> str:
    """Store the PUT body against a signed upload token; returns the key."""
    payload = _verify(token, "upload")
    if content_type.split(";")[0].strip() != payload["ct"]:
        raise MediaError("Content-Type does not match the signed upload")
    if len(body) > payload["max"]:
        raise MediaError("Body is larger than the signed upload declared")
    if not body:
        raise MediaError("Empty body")
    path = _resolve(payload["k"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return payload["k"]


def open_key(token: str) -> tuple[Path, str]:
    """Resolve a signed download token to (path, content_type)."""
    payload = _verify(token, "download")
    path = _resolve(payload["k"])
    if not path.is_file():
        raise MediaError("No such key")
    return path, mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def exists(key: str) -> bool:
    try:
        return _resolve(key).is_file()
    except MediaError:
        return False


def _resolve(key: str) -> Path:
    """Key -> path, refusing anything that escapes MEDIA_ROOT.

    Keys are server-minted and signed, so traversal shouldn't be reachable —
    this is the belt for the braces, and it also guards `sign-download?key=`,
    which takes a caller-supplied key.
    """
    root = _root()
    path = (root / key).resolve()
    if not str(path).startswith(str(root) + os.sep):
        raise MediaError("Invalid key")
    return path
