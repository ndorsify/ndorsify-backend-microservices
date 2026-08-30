"""Discovery ORM models (P0).

`creator_index` is a local, denormalized copy of searchable creator data,
maintained via the internal ingest endpoint (fed by profile updates — the
stand-in for `profile.updated` events until E5 exists). Keeping it local keeps
discovery decoupled from profile-service's database.

`niches_text` is a lowercased, space-joined mirror of `niches`, so niche
filtering is a portable ``LIKE`` (works on both Postgres and SQLite) rather than
JSON containment. Postgres full-text search is a later optimization (E7).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class CreatorIndex(Base):
    __tablename__ = "creator_index"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    handle: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    niches: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    niches_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    platforms: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    platforms_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    follower_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    engagement_rate: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )
    avg_rating: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )
    rate_per_post: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Shortlist(Base):
    __tablename__ = "shortlists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class ShortlistItem(Base):
    __tablename__ = "shortlist_items"
    __table_args__ = (
        UniqueConstraint("shortlist_id", "creator_id", name="uq_shortlist_creator"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shortlist_id: Mapped[int] = mapped_column(
        ForeignKey("shortlists.id"), index=True, nullable=False
    )
    creator_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
