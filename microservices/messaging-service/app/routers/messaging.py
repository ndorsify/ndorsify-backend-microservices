"""Messaging HTTP layer (P0) — /conversations.

All endpoints require an authenticated user; participant checks live in the
service layer.
"""
from typing import List

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import Principal, require_auth
from ..db.session import get_session
from ..schemas.messaging import (
    ConversationResponse,
    CreateConversationRequest,
    CreateMessageRequest,
    MessageResponse,
)
from ..services import messaging as service

router = APIRouter(prefix="/conversations", tags=["messaging"])


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> List[ConversationResponse]:
    return await service.list_conversations(
        session, principal.user_id, page=page, size=size
    )


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    body: CreateConversationRequest,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> ConversationResponse:
    return await service.get_or_create_conversation(
        session, principal.user_id, body.recipient_id
    )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: int,
    page: int = Query(0, ge=0),
    size: int = Query(30, ge=1, le=100),
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> List[MessageResponse]:
    return await service.list_messages(
        session, principal.user_id, conversation_id, page=page, size=size
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def post_message(
    conversation_id: int,
    body: CreateMessageRequest,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    return await service.post_message(
        session, principal.user_id, conversation_id, body.body
    )


@router.post("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    conversation_id: int,
    principal: Principal = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.mark_read(session, principal.user_id, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
