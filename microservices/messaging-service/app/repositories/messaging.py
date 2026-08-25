"""Data-access for messaging."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.messaging import Conversation, Message


async def get_conversation(
    session: AsyncSession, conversation_id: int
) -> Optional[Conversation]:
    return await session.get(Conversation, conversation_id)


async def get_conversation_by_pair(
    session: AsyncSession, low: int, high: int
) -> Optional[Conversation]:
    result = await session.execute(
        select(Conversation).where(
            Conversation.participant_a == low, Conversation.participant_b == high
        )
    )
    return result.scalar_one_or_none()


async def list_conversations_for_user(
    session: AsyncSession, user_id: int, *, offset: int, limit: int
) -> List[Conversation]:
    result = await session.execute(
        select(Conversation)
        .where(
            or_(
                Conversation.participant_a == user_id,
                Conversation.participant_b == user_id,
            )
        )
        .order_by(Conversation.last_message_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_messages(
    session: AsyncSession, conversation_id: int, *, offset: int, limit: int
) -> List[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_messages_read(
    session: AsyncSession, conversation_id: int, reader_id: int, at: datetime
) -> None:
    await session.execute(
        update(Message)
        .where(
            and_(
                Message.conversation_id == conversation_id,
                Message.sender_id != reader_id,
                Message.read_at.is_(None),
            )
        )
        .values(read_at=at)
    )


async def save(session: AsyncSession, obj):
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj
