"""Messaging ORM models (P0): 1:1 conversations and their messages.

Participants are users-service ``users.id`` (integers). A conversation is stored
with the pair normalized (``participant_a`` < ``participant_b``) and made unique,
so a DM between two users resolves to exactly one row regardless of who started.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("participant_a", "participant_b", name="uq_conversation_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    participant_a: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    participant_b: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), index=True, nullable=False
    )
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
