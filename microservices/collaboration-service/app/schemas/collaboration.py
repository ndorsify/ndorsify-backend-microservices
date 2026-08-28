"""Collaboration request/response DTOs (E3)."""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DeliverableSpec(BaseModel):
    platform: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    due_on: Optional[date] = None


class CreateCollaboration(BaseModel):
    """Internal payload from campaign-service on acceptance."""

    campaign_id: int
    brand_id: int
    creator_id: int
    deliverables: List[DeliverableSpec] = []


class DeliverableResponse(BaseModel):
    id: int
    collaboration_id: int
    platform: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    due_on: Optional[date] = None
    status: str


class CollaborationResponse(BaseModel):
    id: int
    campaign_id: int
    brand_id: int
    creator_id: int
    status: str
    deliverables: List[DeliverableResponse] = []


class SubmitRequest(BaseModel):
    file_refs: List[str] = []
    note: Optional[str] = None


class ReviewRequest(BaseModel):
    decision: str = Field(pattern="^(approved|changes_requested)$")
    feedback: Optional[str] = None


class TimelineEntry(BaseModel):
    kind: str  # "submission" | "review"
    deliverable_id: Optional[int] = None
    at: datetime
    detail: dict = {}
