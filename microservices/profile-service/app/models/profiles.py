"""Profile ORM models (P0, E6 §1).

Two shapes keyed by ``user_id`` (the users-service ``users.id`` — an integer, so
the cross-service reference is stored as an int, matching the existing schema).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class CreatorProfile(Base):
    __tablename__ = "creator_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    niches: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    languages: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    completion_pct: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SocialAccount(Base):
    """A creator's connected social platform, with the stats last pulled from
    it. Tokens live with the provider (Phyllo/Modash/etc, not built yet) — we
    only ever store the normalized stats and a reference id, never a platform
    access token. See docs/plans/technical-specifications/e6-profiles-discovery.md §1.
    """

    __tablename__ = "social_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "platform", name="uq_social_account_platform"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    external_account_id: Mapped[str] = mapped_column(String, nullable=False)
    handle: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    follower_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    engagement_rate: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )
    connected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    company_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    about: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
