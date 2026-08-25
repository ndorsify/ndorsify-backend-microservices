"""Profile request/response DTOs (P0). Update DTOs are all-optional for partial
upsert; response DTOs expose the public profile shape."""
from typing import List, Optional

from pydantic import BaseModel


class CreatorProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    niches: Optional[List[str]] = None
    location: Optional[str] = None
    languages: Optional[List[str]] = None
    avatar_url: Optional[str] = None


class CreatorProfileResponse(BaseModel):
    user_id: int
    display_name: Optional[str] = None
    bio: Optional[str] = None
    niches: List[str] = []
    location: Optional[str] = None
    languages: List[str] = []
    avatar_url: Optional[str] = None
    completion_pct: int = 0


class BrandProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    about: Optional[str] = None


class BrandProfileResponse(BaseModel):
    user_id: int
    company_name: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    about: Optional[str] = None
