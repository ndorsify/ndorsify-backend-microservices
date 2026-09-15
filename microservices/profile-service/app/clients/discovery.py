"""Client for discovery-service's creator index.

Best-effort in Phase 1: this is the stand-in for emitting a `profile.updated`
event. If the URL is unset (tests / isolated runs) the call is skipped; if it
fails, the profile save still succeeds (a production impl would enqueue a retry
rather than swallow the error).

The ingest endpoint (`PUT /internal/creator-index`) is a full replace, not a
partial merge — every field on the request overwrites the stored row. Callers
must always send the complete current picture (identity fields *and* social
stats), never just the fields that changed, or they'll silently wipe out
whatever the other side last set. `services/profiles.py`'s `_aggregate_and_push`
is the one place that assembles that full picture; nothing else should call
this function directly.
"""
import logging
from typing import List, Optional

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


async def upsert_creator_index(
    *,
    user_id: int,
    display_name: Optional[str],
    handle: Optional[str] = None,
    bio: Optional[str],
    niches: List[str],
    platforms: Optional[List[str]] = None,
    location: Optional[str],
    follower_count: int = 0,
    engagement_rate: float = 0.0,
    rate_per_post: int = 0,
    verified: bool = False,
) -> None:
    if not settings.discovery_url:
        return
    payload = {
        "user_id": user_id,
        "display_name": display_name,
        "handle": handle,
        "bio": bio,
        "niches": niches,
        "platforms": platforms or [],
        "location": location,
        "follower_count": follower_count,
        "engagement_rate": engagement_rate,
        "rate_per_post": rate_per_post,
        "verified": verified,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.put(
                f"{settings.discovery_url.rstrip('/')}/internal/creator-index",
                json=payload,
                headers={"X-Service-Token": settings.service_token},
            )
            resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - best-effort
        logger.warning(
            "Failed to sync creator %s to discovery index: %s", user_id, exc
        )
