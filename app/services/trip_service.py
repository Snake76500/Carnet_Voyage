from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from slugify import slugify

from app.models.trip import Trip, DayEntry, Media

def generate_unique_slug(db: Session, base_text: str) -> str:
    """Generate a unique slug for a trip, resolving any collisions with a numerical suffix."""
    base_slug = slugify(base_text)
    if not base_slug:
        base_slug = "copie-voyage"
    slug = base_slug
    counter = 1
    while db.query(Trip).filter(Trip.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

def duplicate_trip(
    db: Session,
    original_trip: Trip,
    new_title: Optional[str] = None,
    is_public: Optional[bool] = None
) -> Trip:
    """
    Duplicate an existing trip including all its day entries and media items.
    Strictly intended for administrative operations.
    """
    # Determine title
    if new_title and new_title.strip():
        title = new_title.strip()[:255]
    else:
        title = f"Copie de {original_trip.title}"[:255]

    # Generate unique slug
    slug = generate_unique_slug(db, title)

    # Determine visibility: default to private (False) if unspecified
    effective_is_public = is_public if is_public is not None else False

    # Create new Trip
    new_trip = Trip(
        title=title,
        slug=slug,
        description=original_trip.description,
        start_date=original_trip.start_date,
        end_date=original_trip.end_date,
        cover_image_url=original_trip.cover_image_url,
        is_public=effective_is_public,
        created_at=datetime.utcnow()
    )
    db.add(new_trip)
    db.flush()

    # Sort entries by order_index and date to maintain sequence
    sorted_entries = sorted(original_trip.entries, key=lambda e: (e.order_index, e.date))

    for entry in sorted_entries:
        new_entry = DayEntry(
            trip_id=new_trip.id,
            date=entry.date,
            title=entry.title,
            body_markdown=entry.body_markdown,
            location_name=entry.location_name,
            latitude=entry.latitude,
            longitude=entry.longitude,
            order_index=entry.order_index,
            created_at=datetime.utcnow()
        )
        db.add(new_entry)
        db.flush()

        sorted_media = sorted(entry.media, key=lambda m: m.order_index)
        for media_item in sorted_media:
            new_media = Media(
                day_entry_id=new_entry.id,
                type=media_item.type,
                url=media_item.url,
                caption=media_item.caption,
                order_index=media_item.order_index
            )
            db.add(new_media)

    db.commit()
    db.refresh(new_trip)
    return new_trip
