"""Discovery request/response DTOs (P0)."""
from typing import List, Optional

from pydantic import BaseModel, Field


# --- creator index (internal ingest) ---
class CreatorIndexUpsert(BaseModel):
    user_id: int
    display_name: Optional[str] = None
    handle: Optional[str] = None
    bio: Optional[str] = None
    niches: List[str] = []
    platforms: List[str] = []
    location: Optional[str] = None
    follower_count: int = 0
    engagement_rate: float = 0.0
    avg_rating: float = 0.0
    rate_per_post: int = 0
    verified: bool = False


class CreatorResult(BaseModel):
    user_id: int
    display_name: Optional[str] = None
    handle: Optional[str] = None
    niches: List[str] = []
    platforms: List[str] = []
    location: Optional[str] = None
    follower_count: int = 0
    engagement_rate: float = 0.0
    avg_rating: float = 0.0
    rate_per_post: int = 0
    verified: bool = False


# --- shortlists ---
class CreateShortlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ShortlistResponse(BaseModel):
    id: int
    brand_id: int
    name: str


class AddShortlistItemRequest(BaseModel):
    creator_id: int


class ShortlistDetailResponse(BaseModel):
    id: int
    brand_id: int
    name: str
    creator_ids: List[int] = []
