"""Collaboration ORM models (E3): collaborations, deliverables, submissions,
reviews.

brand_id / creator_id are the integer users.id (no cross-database FKs). File
contents live in object storage (E7); submissions store only the storage keys.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class Collaboration(Base):
    __tablename__ = "collaborations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    brand_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    creator_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    # accepted -> in_progress -> submitted -> approved -> live (+ cancelled)
    status: Mapped[str] = mapped_column(
        String, default="accepted", server_default="accepted", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Deliverable(Base):
    __tablename__ = "deliverables"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    collaboration_id: Mapped[int] = mapped_column(
        ForeignKey("collaborations.id"), index=True, nullable=False
    )
    platform: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # todo -> submitted -> (approved | changes_requested); approved -> live
    status: Mapped[str] = mapped_column(
        String, default="todo", server_default="todo", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    deliverable_id: Mapped[int] = mapped_column(
        ForeignKey("deliverables.id"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    file_refs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id"), index=True, nullable=False
    )
    decision: Mapped[str] = mapped_column(String, nullable=False)  # approved | changes_requested
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
