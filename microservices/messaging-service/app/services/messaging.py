"""Messaging business logic (P0): find-or-create conversations, post/read
messages, with participant-only access enforced in this layer.

Timestamps are naive UTC to match the DateTime columns.
"""
from datetime import datetime, timezone
from typing import List, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.messaging import Conversation, Message
from ..repositories import messaging as repo


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _pair(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)


def _is_participant(conv: Conversation, user_id: int) -> bool:
    return user_id in (conv.participant_a, conv.participant_b)


async def get_or_create_conversation(
    session: AsyncSession, me: int, recipient_id: int
) -> Conversation:
    if recipient_id == me:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Cannot start a conversation with yourself"
        )
    low, high = _pair(me, recipient_id)
    existing = await repo.get_conversation_by_pair(session, low, high)
    if existing is not None:
        return existing
    return await repo.save(
        session, Conversation(participant_a=low, participant_b=high)
    )


async def list_conversations(
    session: AsyncSession, me: int, *, page: int, size: int
) -> List[Conversation]:
    return await repo.list_conversations_for_user(
        session, me, offset=page * size, limit=size
    )


async def _load_participant_conversation(
    session: AsyncSession, me: int, conversation_id: int
) -> Conversation:
    conv = await repo.get_conversation(session, conversation_id)
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    if not _is_participant(conv, me):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a participant")
    return conv


async def list_messages(
    session: AsyncSession, me: int, conversation_id: int, *, page: int, size: int
) -> List[Message]:
    await _load_participant_conversation(session, me, conversation_id)
    return await repo.list_messages(
        session, conversation_id, offset=page * size, limit=size
    )


async def post_message(
    session: AsyncSession, me: int, conversation_id: int, body: str
) -> Message:
    conv = await _load_participant_conversation(session, me, conversation_id)
    message = Message(conversation_id=conv.id, sender_id=me, body=body)
    session.add(message)
    conv.last_message_at = _now()
    await session.commit()
    await session.refresh(message)
    # TODO(E5): emit `message.created` to notification-service once it exists.
    return message


async def mark_read(session: AsyncSession, me: int, conversation_id: int) -> None:
    await _load_participant_conversation(session, me, conversation_id)
    await repo.mark_messages_read(session, conversation_id, me, _now())
    await session.commit()
