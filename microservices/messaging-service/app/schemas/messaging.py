"""Messaging request/response DTOs (P0)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    recipient_id: int


class CreateMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class ConversationResponse(BaseModel):
    id: int
    participant_a: int
    participant_b: int
    last_message_at: Optional[datetime] = None
    created_at: datetime


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    body: str
    read_at: Optional[datetime] = None
    created_at: datetime
