"""Media storage HTTP layer (E7 §1) — /media.

Two of these routes are deliberately unauthenticated: the signed token in the
path *is* the credential (that's what makes the URL usable as a plain
PUT/GET from the browser, exactly like an S3 presigned URL). Minting a token
is what requires a logged-in user.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field

from ..core.deps import Principal, require_auth
from ..services import media as service

router = APIRouter(prefix="/media", tags=["media"])


class SignUploadRequest(BaseModel):
    scope: str = Field(..., description="submissions | media-kit | avatars")
    content_type: str
    size_bytes: int
    # Required for `submissions` (the collaboration id); ignored otherwise,
    # where the key is namespaced by the caller's own user id.
    ref_id: Optional[str] = None


class SignUploadResponse(BaseModel):
    key: str
    upload_url: str
    method: str = "PUT"
    headers: dict


class SignDownloadResponse(BaseModel):
    key: str
    download_url: str


@router.post("/sign-upload", response_model=SignUploadResponse)
async def sign_upload(
    body: SignUploadRequest,
    request: Request,
    principal: Principal = Depends(require_auth),
) -> SignUploadResponse:
    try:
        signed = service.sign_upload(
            scope=body.scope,
            user_id=principal.user_id,
            ref_id=body.ref_id,
            content_type=body.content_type,
            size_bytes=body.size_bytes,
        )
    except service.MediaError as exc:
        raise HTTPException(400, str(exc))
    return SignUploadResponse(
        key=signed["key"],
        upload_url=f"{str(request.base_url).rstrip('/')}/media/upload/{signed['token']}",
        headers={"Content-Type": signed["content_type"]},
    )


@router.put("/upload/{token}", status_code=204)
async def upload(token: str, request: Request) -> None:
    body = await request.body()
    try:
        await service.save(token, body, request.headers.get("content-type", ""))
    except service.MediaError as exc:
        raise HTTPException(400, str(exc))


@router.get("/sign-download", response_model=SignDownloadResponse)
async def sign_download(
    request: Request,
    key: str = Query(...),
    principal: Principal = Depends(require_auth),
) -> SignDownloadResponse:
    try:
        token = await service.sign_download(key, principal.user_id)
    except service.Forbidden as exc:
        raise HTTPException(403, str(exc))
    except service.MediaError as exc:
        raise HTTPException(404, str(exc))
    return SignDownloadResponse(
        key=key,
        download_url=f"{str(request.base_url).rstrip('/')}/media/file/{token}",
    )


@router.get("/file/{token}")
async def file(token: str):
    try:
        stored = await service.open_key(token)
    except service.MediaError as exc:
        raise HTTPException(404, str(exc))
    if stored.url:
        # Blob serves the bytes itself; the token check above is the gate.
        return RedirectResponse(stored.url, status_code=307)
    return FileResponse(stored.path, media_type=stored.content_type)
