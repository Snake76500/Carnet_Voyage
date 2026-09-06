from datetime import date, datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl

class MediaBase(BaseModel):
    type: Literal["photo", "video"]
    url: str
    caption: Optional[str] = None
    order_index: int = 0

class MediaCreate(MediaBase):
    pass

class MediaResponse(MediaBase):
    id: int
    day_entry_id: int
    
    # Processed fields for UI rendering
    display_url: Optional[str] = None
    fallback_url: Optional[str] = None
    embed_url: Optional[str] = None

    class Config:
        from_attributes = True


class DayEntryBase(BaseModel):
    date: date
    title: str
    body_markdown: Optional[str] = None
    location_name: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    order_index: int = 0

class DayEntryCreate(DayEntryBase):
    media: Optional[List[MediaCreate]] = []

class DayEntryUpdate(BaseModel):
    date: Optional[date] = None
    title: Optional[str] = None
    body_markdown: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    order_index: Optional[int] = None

class DayEntryResponse(DayEntryBase):
    id: int
    trip_id: int
    created_at: datetime
    media: List[MediaResponse] = []
    body_html: Optional[str] = None

    class Config:
        from_attributes = True


class TripBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cover_image_url: Optional[str] = None
    is_public: bool = False

class TripCreate(TripBase):
    slug: Optional[str] = None

class TripUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cover_image_url: Optional[str] = None
    is_public: Optional[bool] = None

class TripResponse(TripBase):
    id: int
    slug: str
    created_at: datetime
    entries: List[DayEntryResponse] = []

    class Config:
        from_attributes = True
