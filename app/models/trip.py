from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    entries = relationship(
        "DayEntry",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="DayEntry.order_index, DayEntry.date"
    )

    @property
    def cover_image_display_url(self) -> Optional[str]:
        if not self.cover_image_url or not self.cover_image_url.strip():
            return None
        from app.services.media_helpers import process_photo_url
        return process_photo_url(self.cover_image_url.strip())["display_url"]

    def __repr__(self):
        return f"<Trip id={self.id} title='{self.title}'>"


class DayEntry(Base):
    __tablename__ = "day_entries"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    title = Column(String(255), nullable=False)
    body_markdown = Column(Text, nullable=True)
    location_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    trip = relationship("Trip", back_populates="entries")
    media = relationship(
        "Media",
        back_populates="day_entry",
        cascade="all, delete-orphan",
        order_by="Media.order_index"
    )

    def __repr__(self):
        return f"<DayEntry id={self.id} title='{self.title}' location='{self.location_name}'>"


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    day_entry_id = Column(Integer, ForeignKey("day_entries.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)  # 'photo' or 'video'
    url = Column(String(500), nullable=False)
    caption = Column(String(255), nullable=True)
    order_index = Column(Integer, default=0, nullable=False)

    day_entry = relationship("DayEntry", back_populates="media")

    def __repr__(self):
        return f"<Media id={self.id} type='{self.type}' url='{self.url}'>"
