"""Rate-card ORM models (Phase 3).

A creator has at most one `rate_cards` row (holding the public-visibility flag)
and any number of `rate_card_packages`. A package carries its contents as a JSON
list of {platform, type, quantity} — the same shape campaign-service's
Deliverable uses — because items are always read and written with their package
and are never queried on their own.

No ORM relationship is declared on purpose: the repository loads packages with
an explicit ordered query, so every access is eager and async lazy-loading can
never bite.
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class RateCard(Base):
    __tablename__ = "rate_cards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    hidden: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class RateCardPackage(Base):
    __tablename__ = "rate_card_packages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rate_card_id: Mapped[int] = mapped_column(
        ForeignKey("rate_cards.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(
        Text, default="", server_default="", nullable=False
    )
    turnaround_days: Mapped[int] = mapped_column(Integer, nullable=False)
    visible: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False
    )
    items: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
