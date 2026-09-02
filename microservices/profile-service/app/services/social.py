"""Connected-social-account business logic (E6 §1) — connect, sync, and
disconnect a creator's platform accounts, keeping discovery-service's index in
sync via `services.profiles.aggregate_and_push` after every change.

Real platform OAuth (Instagram Graph, TikTok, YouTube Data — or a vendor
aggregator like Phyllo/Modash that wraps all of them) is not wired yet; every
call goes through `clients.social_provider.get_provider()`, currently a stub
that fabricates plausible stats. See that module's docstring for how a real
provider slots in.
"""
from datetime import datetime, timedelta, timezone
from typing import List

import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..clients.social_provider import get_provider
from ..core.config import settings
from ..models.profiles import SocialAccount
from ..repositories import profiles as repo
from ..schemas.profiles import ConnectResponse, SocialAccountResponse
from .profiles import aggregate_and_push

VALID_PLATFORMS = frozenset({"instagram", "youtube", "tiktok", "twitter"})
_STATE_TTL_MINUTES = 15


def _require_valid_platform(platform: str) -> None:
    if platform not in VALID_PLATFORMS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown platform '{platform}' — expected one of {sorted(VALID_PLATFORMS)}",
        )


def _to_response(a: SocialAccount) -> SocialAccountResponse:
    return SocialAccountResponse(
        platform=a.platform,
        handle=a.handle,
        follower_count=a.follower_count,
        engagement_rate=a.engagement_rate,
        connected_at=a.connected_at,
        last_synced_at=a.last_synced_at,
    )


def _make_state(user_id: int, platform: str) -> str:
    """Short-lived, signed token correlating a connect callback back to the
    user/platform that started it — the OAuth "state" param, without needing
    a table to track pending connect attempts. Reuses the same JWT secret
    every service already verifies access tokens with."""
    payload = {
        "user_id": user_id,
        "platform": platform,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=_STATE_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _read_state(state: str) -> tuple:
    try:
        payload = jwt.decode(
            state, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Connect session expired")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid connect state")
    return int(payload["user_id"]), payload["platform"]


async def start_connect(user_id: int, platform: str) -> ConnectResponse:
    _require_valid_platform(platform)
    state = _make_state(user_id, platform)
    session_info = await get_provider().create_connect_session(
        user_id=user_id, platform=platform, state=state
    )
    return ConnectResponse(connect_url=session_info.connect_url)


async def complete_connect(
    session: AsyncSession, *, state: str, external_account_id: str
) -> SocialAccountResponse:
    user_id, platform = _read_state(state)
    stats = await get_provider().fetch_account_stats(
        platform=platform, external_account_id=external_account_id
    )
    account = await repo.get_social_account(session, user_id, platform)
    if account is None:
        account = SocialAccount(user_id=user_id, platform=platform, external_account_id=stats.external_account_id)
    account.external_account_id = stats.external_account_id
    account.handle = stats.handle
    account.follower_count = stats.follower_count
    account.engagement_rate = stats.engagement_rate
    saved = await repo.save(session, account)
    await aggregate_and_push(session, user_id)
    return _to_response(saved)


async def sync_account(session: AsyncSession, user_id: int, platform: str) -> SocialAccountResponse:
    _require_valid_platform(platform)
    account = await repo.get_social_account(session, user_id, platform)
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{platform} is not connected")
    stats = await get_provider().fetch_account_stats(
        platform=platform, external_account_id=account.external_account_id
    )
    account.handle = stats.handle
    account.follower_count = stats.follower_count
    account.engagement_rate = stats.engagement_rate
    saved = await repo.save(session, account)
    await aggregate_and_push(session, user_id)
    return _to_response(saved)


async def disconnect(session: AsyncSession, user_id: int, platform: str) -> None:
    _require_valid_platform(platform)
    await repo.delete_social_account(session, user_id, platform)
    await aggregate_and_push(session, user_id)


async def list_accounts(session: AsyncSession, user_id: int) -> List[SocialAccountResponse]:
    accounts = await repo.list_social_accounts(session, user_id)
    return [_to_response(a) for a in accounts]
