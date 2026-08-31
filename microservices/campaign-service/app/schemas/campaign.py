"""Campaign request/response DTOs (E1)."""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class Deliverable(BaseModel):
    platform: str
    type: str
    quantity: int = 1
    usage: Optional[str] = None
    requires_approval: bool = True


class _DateOrderMixin(BaseModel):
    @model_validator(mode="after")
    def _check_date_order(self):
        starts_on = getattr(self, "starts_on", None)
        ends_on = getattr(self, "ends_on", None)
        if starts_on and ends_on and ends_on < starts_on:
            raise ValueError("ends_on must be on or after starts_on")
        return self


class CampaignCreate(_DateOrderMixin):
    title: str = Field(min_length=1, max_length=200)
    objective: Optional[str] = None
    deliverables: List[Deliverable] = []
    platforms: List[str] = []
    budget_amount: Optional[float] = None
    budget_currency: Optional[str] = None
    starts_on: Optional[date] = None
    ends_on: Optional[date] = None
    target_audience: dict = {}


class CampaignUpdate(_DateOrderMixin):
    title: Optional[str] = None
    objective: Optional[str] = None
    deliverables: Optional[List[Deliverable]] = None
    platforms: Optional[List[str]] = None
    budget_amount: Optional[float] = None
    budget_currency: Optional[str] = None
    starts_on: Optional[date] = None
    ends_on: Optional[date] = None
    target_audience: Optional[dict] = None


class CampaignResponse(BaseModel):
    id: int
    brand_id: int
    title: str
    objective: Optional[str] = None
    deliverables: List[dict] = []
    platforms: List[str] = []
    budget_amount: Optional[float] = None
    budget_currency: Optional[str] = None
    starts_on: Optional[date] = None
    ends_on: Optional[date] = None
    target_audience: dict = {}
    status: str
    published_at: Optional[datetime] = None
    funded_at: Optional[datetime] = None


class InviteRequest(BaseModel):
    creator_id: int
    message: Optional[str] = None


class InvitationResponse(BaseModel):
    id: int
    campaign_id: int
    creator_id: int
    status: str
    message: Optional[str] = None


class RespondRequest(BaseModel):
    decision: str  # "accepted" | "declined"


class ApplyRequest(BaseModel):
    proposal: Optional[str] = None
    proposed_rate: Optional[float] = None


class ApplicationResponse(BaseModel):
    id: int
    campaign_id: int
    creator_id: int
    proposal: Optional[str] = None
    proposed_rate: Optional[float] = None
    status: str


class DecideRequest(BaseModel):
    decision: str  # "accepted" | "rejected"
