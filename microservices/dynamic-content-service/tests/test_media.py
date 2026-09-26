"""End-to-end tests for media storage (E7 §1).

Access tokens are minted locally with the same JWT secret require_auth uses,
standing in for tokens users-service would issue — same pattern as
profile-service's tests.
"""
import os
from pathlib import Path

import jwt
import pytest

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def _auth(user_id: int, role: str = "creator") -> dict:
    token = jwt.encode(
        {"sub": str(user_id), "role": role, "type": "access"},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _sign(client, user_id=7, **overrides):
    body = {"scope": "media-kit", "content_type": "image/png", "size_bytes": len(PNG)}
    body.update(overrides)
    return client.post("/media/sign-upload", json=body, headers=_auth(user_id))


def test_sign_upload_requires_auth(client):
    r = client.post(
        "/media/sign-upload",
        json={"scope": "media-kit", "content_type": "image/png", "size_bytes": 10},
    )
    assert r.status_code == 401  # HTTPBearer rejects a missing header


def test_round_trip_sign_put_download(client):
    signed = _sign(client)
    assert signed.status_code == 200, signed.text
    key, url = signed.json()["key"], signed.json()["upload_url"]
    assert key.startswith("media-kit/7/") and key.endswith(".png")

    put = client.put(url, content=PNG, headers={"Content-Type": "image/png"})
    assert put.status_code == 204, put.text

    signed_get = client.get(
        "/media/sign-download", params={"key": key}, headers=_auth(7)
    )
    assert signed_get.status_code == 200, signed_get.text
    got = client.get(signed_get.json()["download_url"])
    assert got.status_code == 200
    assert got.content == PNG
    assert got.headers["content-type"].startswith("image/png")


def test_submissions_scope_is_namespaced_by_collaboration(client):
    r = _sign(client, scope="submissions", ref_id="42")
    assert r.status_code == 200, r.text
    assert r.json()["key"].startswith("submissions/42/")


def test_submissions_scope_needs_a_ref_id(client):
    assert _sign(client, scope="submissions").status_code == 400


def test_rejects_unknown_scope_and_content_type(client):
    assert _sign(client, scope="anything").status_code == 400
    assert _sign(client, content_type="application/x-sh").status_code == 400


def test_rejects_oversized_declaration(client):
    assert _sign(client, size_bytes=26 * 1024 * 1024).status_code == 400


def test_upload_rejects_a_body_bigger_than_signed(client):
    url = _sign(client, size_bytes=len(PNG)).json()["upload_url"]
    r = client.put(url, content=PNG + b"x" * 100, headers={"Content-Type": "image/png"})
    assert r.status_code == 400


def test_upload_rejects_a_mismatched_content_type(client):
    url = _sign(client).json()["upload_url"]
    r = client.put(url, content=PNG, headers={"Content-Type": "application/pdf"})
    assert r.status_code == 400


def test_upload_rejects_a_tampered_token(client):
    url = _sign(client).json()["upload_url"]
    r = client.put(url + "x", content=PNG, headers={"Content-Type": "image/png"})
    assert r.status_code == 400


def test_download_token_is_required_and_signed(client):
    assert client.get("/media/file/not-a-token").status_code == 404
    # An upload token is not a download token.
    upload_token = _sign(client).json()["upload_url"].rsplit("/", 1)[1]
    assert client.get(f"/media/file/{upload_token}").status_code == 404


def test_sign_download_404s_for_an_unwritten_key(client):
    r = client.get(
        "/media/sign-download", params={"key": "media-kit/7/nope.png"}, headers=_auth(7)
    )
    assert r.status_code == 404


def test_sign_download_refuses_traversal(client):
    r = client.get(
        "/media/sign-download",
        params={"key": "../../etc/passwd"},
        headers=_auth(7),
    )
    assert r.status_code == 404


# --- the Vercel Blob store -----------------------------------------------
# Production stores bytes in Blob, because a serverless instance keeps no
# filesystem. The SDK is faked here: what's under test is that the service
# routes to the other store and that the contract clients see is unchanged.
class FakeBlob:
    """Stands in for the Blob store: path -> bytes, with public URLs."""

    BASE = "https://store123.public.blob.vercel-storage.com"

    def __init__(self):
        self.objects = {}

    def put(self, key, body):
        self.objects[key] = body
        return f"{self.BASE}/{key}"

    def list(self, prefix):
        """Prefix search, like the real store — exactness is our job."""
        return [
            {"pathname": k, "url": f"{self.BASE}/{k}"}
            for k in self.objects
            if k.startswith(prefix)
        ]


@pytest.fixture()
def blob(monkeypatch):
    from app.core.config import settings
    from app.services import media

    fake = FakeBlob()
    monkeypatch.setattr(settings, "blob_read_write_token", "vercel_blob_rw_test")
    monkeypatch.setattr(media, "_blob_put", lambda key, body: fake.put(key, body))
    monkeypatch.setattr(media, "_blob_list", fake.list)
    return fake


def test_blob_round_trip_redirects_to_the_store(client, blob):
    signed = _sign(client, user_id=12)
    assert signed.status_code == 200, signed.text
    key = signed.json()["key"]

    put = client.put(
        signed.json()["upload_url"], content=PNG, headers={"Content-Type": "image/png"}
    )
    assert put.status_code == 204, put.text
    # The bytes went to Blob, not to the local media root.
    assert blob.objects[key] == PNG
    assert not (Path(os.environ["MEDIA_ROOT"]) / key).exists()

    signed_get = client.get(
        "/media/sign-download", params={"key": key}, headers=_auth(12)
    )
    assert signed_get.status_code == 200, signed_get.text

    # Our endpoint stays the gate; Blob serves the bytes.
    got = client.get(signed_get.json()["download_url"], follow_redirects=False)
    assert got.status_code == 307
    assert got.headers["location"] == f"{FakeBlob.BASE}/{key}"


def test_blob_sign_download_404s_for_an_unwritten_key(client, blob):
    r = client.get(
        "/media/sign-download",
        params={"key": "media-kit/12/never-uploaded.png"},
        headers=_auth(12),
    )
    assert r.status_code == 404


def test_blob_still_refuses_traversal(client, blob):
    r = client.get(
        "/media/sign-download", params={"key": "../../etc/passwd"}, headers=_auth(12)
    )
    assert r.status_code == 404


def test_blob_refuses_a_prefix_of_a_real_key(client, blob):
    """A collaboration id is a small integer, so `submissions/42/` is guessable
    where the uuid4 in the full key is not. Prefix search must not resolve it."""
    signed = _sign(client, user_id=12, scope="submissions", ref_id="42")
    key = signed.json()["key"]
    client.put(
        signed.json()["upload_url"], content=PNG, headers={"Content-Type": "image/png"}
    )
    assert blob.objects[key] == PNG  # the real object is there

    for probe in ("submissions/42/", "submissions/42", key[:-6]):
        r = client.get(
            "/media/sign-download", params={"key": probe}, headers=_auth(12)
        )
        assert r.status_code == 404, f"{probe} resolved to a real object"


def test_local_store_refuses_a_prefix_of_a_real_key(client):
    signed = _sign(client, user_id=13, scope="submissions", ref_id="43")
    key = signed.json()["key"]
    client.put(
        signed.json()["upload_url"], content=PNG, headers={"Content-Type": "image/png"}
    )

    for probe in ("submissions/43/", "submissions/43", key[:-6]):
        r = client.get(
            "/media/sign-download", params={"key": probe}, headers=_auth(13)
        )
        assert r.status_code == 404, f"{probe} resolved to a real object"


# --- who may mint a download URL -------------------------------------------
def test_media_kit_key_is_readable_only_by_its_owner(client):
    """media-kit/{user_id}/… states its owner, so no lookup is needed to
    refuse someone else — even holding the whole key."""
    signed = _sign(client, user_id=70, scope="media-kit")
    key = signed.json()["key"]
    client.put(
        signed.json()["upload_url"], content=PNG, headers={"Content-Type": "image/png"}
    )

    assert (
        client.get("/media/sign-download", params={"key": key}, headers=_auth(70))
    ).status_code == 200
    stranger = client.get(
        "/media/sign-download", params={"key": key}, headers=_auth(71)
    )
    assert stranger.status_code == 403, stranger.text


def test_avatar_key_is_readable_only_by_its_owner(client):
    signed = _sign(client, user_id=72, scope="avatars")
    key = signed.json()["key"]
    client.put(
        signed.json()["upload_url"], content=PNG, headers={"Content-Type": "image/png"}
    )
    assert (
        client.get("/media/sign-download", params={"key": key}, headers=_auth(73))
    ).status_code == 403


def test_submission_key_is_still_a_capability(client):
    """Documented gap: a submission belongs to a collaboration, and deciding
    who is on it needs collaboration-service. Until then, holding the full key
    is what grants the read."""
    signed = _sign(client, user_id=74, scope="submissions", ref_id="900")
    key = signed.json()["key"]
    client.put(
        signed.json()["upload_url"], content=PNG, headers={"Content-Type": "image/png"}
    )
    other_party = client.get(
        "/media/sign-download", params={"key": key}, headers=_auth(75)
    )
    assert other_party.status_code == 200
