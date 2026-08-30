"""Client for discovery-service's creator index.

Best-effort in Phase 1: this is the stand-in for emitting a `profile.updated`
event. If the URL is unset (tests / isolated runs) the call is skipped; if it
fails, the profile save still succeeds (a production impl would enqueue a retry
rather than swallow the error).

Note: audience metrics (followers, engagement, rating) are not on the creator
profile yet — they arrive with connected-platform stats (E6). Until then the
index carries the identity/niche fields and leaves metrics at their defaults,
so a freshly-onboarded creator is discoverable by name and niche.
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
    bio: Optional[str],
    niches: List[str],
    location: Optional[str],
) -> None:
    if not settings.discovery_url:
        return
    payload = {
        "user_id": user_id,
        "display_name": display_name,
        "bio": bio,
        "niches": niches,
        "location": location,
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
