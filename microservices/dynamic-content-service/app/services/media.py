"""Media storage (E7 §1) — signed upload/download URLs over a key namespace.

The client never uploads through an authenticated API call: it asks for a
signed URL, PUTs the bytes to it, and hands the returned ``key`` to whichever
service stores the reference (collaboration submissions' ``file_refs``, the
media kit, an avatar).

Two stores sit behind the same contract, chosen by whether
``BLOB_READ_WRITE_TOKEN`` is set:

* **Vercel Blob** in production. A serverless instance has no durable
  filesystem — a file written on one request is gone on the next — so the
  bytes have to leave the function.
* **The local filesystem** otherwise, so dev and tests need no cloud account.

Only ``save``/``open_key``/``exists`` know the difference; everything
client-facing — sign-upload → PUT → key → sign-download — is identical either
way, which is what makes a third store (S3, R2) a change to three functions.
"""
import mimetypes
import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import jwt
from fastapi.concurrency import run_in_threadpool

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

# Every key this service mints looks like this. Anything else is refused
# before it reaches a store: a caller who supplies a *prefix* ("submissions/42/")
# must not be able to fish out whichever object happens to sit under it.
KEY_RE = re.compile(r"^(submissions|media-kit|avatars)/[A-Za-z0-9_-]+/[0-9a-f]{32}(\.[A-Za-z0-9]+)?$")

# scope -> whether the caller supplies the id segment (else it's their user id).
SCOPES = {
    "submissions": True,   # submissions/{collaboration_id}/...
    "media-kit": False,    # media-kit/{user_id}/...
    "avatars": False,      # avatars/{user_id}/...
}


class MediaError(Exception):
    """Invalid sign/upload request — routers turn this into a 400."""


@dataclass
class StoredObject:
    """Where a caller holding a valid download token should be sent.

    Blob hands back a URL to redirect to; the local store hands back a path to
    serve. Exactly one of the two is set.
    """

    content_type: str
    url: Optional[str] = None
    path: Optional[Path] = None


def _blob_enabled() -> bool:
    return bool(settings.blob_read_write_token)


# The SDK is synchronous (requests), so every call goes through a threadpool
# rather than blocking the event loop. Wrapped in module-level functions so
# tests can swap the store without reaching for the network.
#
# It is imported inside the call, not at module load: vercel_blob needs Python
# 3.10+, the local dev venv is still 3.9, and nothing needs the SDK unless a
# Blob token is configured. Docker and Vercel both run 3.12.
def _blob_put(key: str, body: bytes) -> str:
    import vercel_blob

    result = vercel_blob.put(
        key,
        body,
        {
            # The key already carries a uuid4, so the path is the identity —
            # no suffix. allowOverwrite makes a retried PUT of the same signed
            # token idempotent instead of an error.
            "addRandomSuffix": "false",
            "allowOverwrite": "true",
            "token": settings.blob_read_write_token,
        },
    )
    return result["url"]


def _blob_list(prefix: str) -> list:
    import vercel_blob

    listing = vercel_blob.list(
        {"prefix": prefix, "limit": "20", "token": settings.blob_read_write_token}
    )
    return listing.get("blobs") or []


def _blob_url(key: str) -> Optional[str]:
    """The public URL for a key, or None if nothing is stored under *that* key.

    The store only offers prefix search, so the exact-pathname check here is
    what keeps a partial key from resolving to somebody else's object.
    """
    return next(
        (b["url"] for b in _blob_list(key) if b.get("pathname") == key), None
    )


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


async def sign_download(key: str) -> str:
    if not await exists(key):
        raise MediaError("No such key")
    return _sign({"typ": "download", "k": key})


async def save(token: str, body: bytes, content_type: str) -> str:
    """Store the PUT body against a signed upload token; returns the key."""
    payload = _verify(token, "upload")
    if content_type.split(";")[0].strip() != payload["ct"]:
        raise MediaError("Content-Type does not match the signed upload")
    if len(body) > payload["max"]:
        raise MediaError("Body is larger than the signed upload declared")
    if not body:
        raise MediaError("Empty body")
    key = payload["k"]
    if _blob_enabled():
        await run_in_threadpool(_blob_put, key, body)
    else:
        path = _resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return key


async def open_key(token: str) -> StoredObject:
    """Resolve a signed download token to the object it stands for."""
    payload = _verify(token, "download")
    key = payload["k"]
    content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"

    if _blob_enabled():
        url = await run_in_threadpool(_blob_url, key)
        if not url:
            raise MediaError("No such key")
        return StoredObject(content_type=content_type, url=url)

    path = _resolve(key)
    if not path.is_file():
        raise MediaError("No such key")
    return StoredObject(content_type=content_type, path=path)


async def exists(key: str) -> bool:
    if not KEY_RE.match(key):
        return False
    try:
        path = _resolve(key)  # lexical guard — runs whichever store is behind us
    except MediaError:
        return False
    if _blob_enabled():
        return (await run_in_threadpool(_blob_url, key)) is not None
    return path.is_file()


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
