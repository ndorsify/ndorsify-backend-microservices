"""Client for collaboration-service (E3).

Called when an invitation/application is accepted. Best-effort in Phase 1: if the
URL is unset (default/tests) the call is skipped; if it fails, acceptance still
succeeds (a production impl would enqueue a retry rather than swallow the error).
"""
import logging
from typing import List

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


async def create_collaboration(
    campaign_id: int, brand_id: int, creator_id: int, deliverables: List[dict]
) -> None:
    if not settings.collaboration_url:
        return
    payload = {
        "campaign_id": campaign_id,
        "brand_id": brand_id,
        "creator_id": creator_id,
        "deliverables": deliverables,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.collaboration_url.rstrip('/')}/collaborations",
                json=payload,
                headers={"X-Service-Token": settings.service_token},
            )
            resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - best-effort
        logger.warning("Failed to create collaboration for campaign %s: %s", campaign_id, exc)
