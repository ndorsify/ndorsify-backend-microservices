"""Internal HTTP layer (P0) — /internal.

Service-to-service only (X-Service-Token). The creator-index ingest is the
stand-in for consuming `profile.updated` events until E5 exists; profile-service
(or an event worker) calls it whenever a creator profile changes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import require_service_token
from ..db.session import get_session
from ..schemas.discovery import CreatorIndexUpsert, CreatorResult
from ..services import discovery as service

router = APIRouter(prefix="/internal", tags=["internal"])


@router.put(
    "/creator-index",
    response_model=CreatorResult,
    dependencies=[Depends(require_service_token)],
)
async def upsert_creator_index(
    body: CreatorIndexUpsert,
    session: AsyncSession = Depends(get_session),
) -> CreatorResult:
    return await service.upsert_creator_index(session, body)
