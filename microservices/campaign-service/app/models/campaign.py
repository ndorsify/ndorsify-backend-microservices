"""Campaign ORM models (E1): campaigns, invitations, applications.

Cross-service references (brand_id, creator_id) are the integer users.id, stored
as bare integers — matching the rest of the codebase; no cross-database FKs.
Budget is a Float here for portability/simplicity; production should use a
fixed-precision type or minor units.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
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


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deliverables: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    platforms: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    budget_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    budget_currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    starts_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ends_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_audience: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # draft -> open -> closed / archived
    status: Mapped[str] = mapped_column(
        String, default="draft", server_default="draft", index=True, nullable=False
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (
        UniqueConstraint("campaign_id", "creator_id", name="uq_invitation_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id"), index=True, nullable=False
    )
    creator_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    # pending -> accepted / declined / withdrawn
    status: Mapped[str] = mapped_column(
        String, default="pending", server_default="pending", nullable=False
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("campaign_id", "creator_id", name="uq_application_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id"), index=True, nullable=False
    )
    creator_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    proposal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # submitted -> accepted / rejected / withdrawn
    status: Mapped[str] = mapped_column(
        String, default="submitted", server_default="submitted", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
