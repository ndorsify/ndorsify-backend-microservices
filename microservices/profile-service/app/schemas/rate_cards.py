"""Rate-card DTOs (Phase 3).

`RateCardUpdate` is a whole-card replace, not a partial patch: whatever it
carries becomes the card. The public DTOs deliberately drop `visible` and
`hidden` so a brand can never tell the difference between "no card" and
"card hidden".
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Platform = Literal["instagram", "tiktok", "youtube", "twitter"]
ItemType = Literal["post", "reel", "story", "video", "short", "live"]


class RateCardItem(BaseModel):
    platform: Platform
    type: ItemType
    quantity: int = Field(1, ge=1, le=50)


class RateCardPackageIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    price: int = Field(..., ge=1, le=1_000_000)
    description: str = Field("", max_length=500)
    turnaround_days: int = Field(..., ge=1, le=90)
    visible: bool = True
    items: List[RateCardItem] = Field(..., min_length=1, max_length=10)

    @field_validator("name")
    @classmethod
    def _trim_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("name must not be blank")
        return trimmed


class RateCardUpdate(BaseModel):
    hidden: bool = False
    packages: List[RateCardPackageIn] = Field(default_factory=list, max_length=10)


class RateCardResponse(BaseModel):
    hidden: bool = False
    packages: List[RateCardPackageIn] = []
    updated_at: Optional[datetime] = None


class PublicRateCardPackage(BaseModel):
    name: str
    price: int
    description: str = ""
    turnaround_days: int
    items: List[RateCardItem] = []


class PublicRateCardResponse(BaseModel):
    packages: List[PublicRateCardPackage] = []
