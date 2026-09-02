"""Abstraction over the creator-data vendor (Phyllo/Modash/HypeAuditor — not
selected yet). Nothing in profile-service should import a vendor SDK directly;
everything goes through this interface, so wiring a real vendor later is a
matter of writing one new class and pointing `get_provider()` at it — no
caller in services/social.py or routers/social.py changes.

`StubSocialProvider` is the only implementation today. It fabricates
deterministic (same user+platform always yields the same numbers), plausible
stats so the connect/sync/disconnect flow is fully testable without a vendor
account. It is not random per-call — a real provider wouldn't be either.
"""
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConnectSession:
    """Returned when starting a connect flow — `connect_url` is where the
    frontend redirects the browser (a vendor-hosted consent screen in a real
    provider; a placeholder URL here)."""

    connect_url: str


@dataclass
class AccountStats:
    external_account_id: str
    handle: Optional[str]
    follower_count: int
    engagement_rate: float


class SocialProvider(ABC):
    @abstractmethod
    async def create_connect_session(
        self, *, user_id: int, platform: str, state: str
    ) -> ConnectSession:
        """Start a connect flow for one platform. `state` is an opaque,
        already-signed token the provider should echo back on its own
        callback (or that we pass through our own callback URL) — it's how
        the callback recovers which user/platform this connection is for."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_account_stats(
        self, *, platform: str, external_account_id: str
    ) -> AccountStats:
        """Pull current stats for an already-connected account (used on
        initial connect and on every manual/periodic re-sync)."""
        raise NotImplementedError


def _stable_int(*parts: str, low: int, high: int) -> int:
    """A deterministic pseudo-random int in [low, high], derived from the
    given parts — so the same user+platform always fabricates the same
    numbers instead of a new random value every call."""
    digest = hashlib.sha256(":".join(parts).encode()).hexdigest()
    return low + (int(digest[:8], 16) % (high - low + 1))


class StubSocialProvider(SocialProvider):
    async def create_connect_session(
        self, *, user_id: int, platform: str, state: str
    ) -> ConnectSession:
        # A real provider returns its own hosted-consent-screen URL here.
        return ConnectSession(
            connect_url=f"https://stub-provider.invalid/connect/{platform}?state={state}"
        )

    async def fetch_account_stats(
        self, *, platform: str, external_account_id: str
    ) -> AccountStats:
        followers = _stable_int(
            external_account_id, platform, "followers", low=800, high=250000
        )
        engagement = (
            _stable_int(external_account_id, platform, "engagement", low=10, high=90)
            / 10.0
        )
        return AccountStats(
            external_account_id=external_account_id,
            handle=f"{platform}_{external_account_id}",
            follower_count=followers,
            engagement_rate=round(engagement, 1),
        )


def get_provider() -> SocialProvider:
    """Single seam to swap in a real vendor client later — e.g. branch on a
    `settings.social_provider` env var once one exists. Everything upstream
    of this function only ever talks to the `SocialProvider` interface."""
    return StubSocialProvider()
