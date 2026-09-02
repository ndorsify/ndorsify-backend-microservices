"""Connected-social-accounts HTTP layer (E6 §1) — /social.

The callback route is deliberately unauthenticated: a real provider redirects
the browser back from its own domain, so no Authorization header survives the
trip. The signed `state` param (minted in `/connect`) is what recovers which
user/platform the callback belongs to — see services/social.py.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import Principal, require_role
from ..db.session import get_session
from ..schemas.profiles import ConnectResponse, SocialAccountResponse
from ..services import social as service

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/mine", response_model=list[SocialAccountResponse])
async def list_my_social_accounts(
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> list[SocialAccountResponse]:
    return await service.list_accounts(session, principal.user_id)


@router.get("/{platform}/connect", response_model=ConnectResponse)
async def connect(
    platform: str,
    principal: Principal = Depends(require_role("creator")),
) -> ConnectResponse:
    return await service.start_connect(principal.user_id, platform)


@router.get("/{platform}/callback", response_model=SocialAccountResponse)
async def callback(
    platform: str,
    state: str = Query(...),
    external_account_id: str = Query(
        ..., description="Reference id the provider returns for the connected account"
    ),
    session: AsyncSession = Depends(get_session),
) -> SocialAccountResponse:
    return await service.complete_connect(
        session, state=state, external_account_id=external_account_id
    )


@router.post("/{platform}/sync", response_model=SocialAccountResponse)
async def sync(
    platform: str,
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> SocialAccountResponse:
    return await service.sync_account(session, principal.user_id, platform)


@router.delete("/{platform}", status_code=204)
async def disconnect(
    platform: str,
    principal: Principal = Depends(require_role("creator")),
    session: AsyncSession = Depends(get_session),
) -> None:
    await service.disconnect(session, principal.user_id, platform)
