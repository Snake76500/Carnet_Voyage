from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from slugify import slugify

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.core.security import hash_password
from app.models.user import User
from app.models.trip import Trip, DayEntry, Media
from app.schemas.trip import (
    TripCreate, TripUpdate, TripResponse,
    DayEntryCreate, DayEntryUpdate, DayEntryResponse,
    MediaCreate, MediaResponse
)
from app.schemas.user import UserCreate, UserResponse
from app.services.media_helpers import process_media_item, render_markdown
from app.services.seed_data import create_demo_data

router = APIRouter(prefix="/api", tags=["API"], dependencies=[Depends(get_current_user)])

@router.get("/trips", response_model=List[TripResponse])
def list_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Trip)
    # Non-admin users only see public trips
    if current_user.role != "admin":
        query = query.filter(Trip.is_public == True)

    trips = query.order_by(Trip.start_date.desc().nullslast(), Trip.created_at.desc()).all()
    return trips

@router.get("/trips/{identifier}", response_model=TripResponse)
def get_trip(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if identifier.isdigit():
        trip = db.query(Trip).filter(Trip.id == int(identifier)).first()
    else:
        trip = db.query(Trip).filter(Trip.slug == identifier).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")

    if not trip.is_public and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voyage privé réservé à l'administrateur.")

    return trip

@router.post("/trips", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    base_slug = payload.slug or slugify(payload.title)
    slug = base_slug
    counter = 1
    while db.query(Trip).filter(Trip.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    trip = Trip(
        title=payload.title,
        slug=slug,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        cover_image_url=payload.cover_image_url,
        is_public=payload.is_public
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip

@router.put("/trips/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: int,
    payload: TripUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    
    update_data = payload.model_dump(exclude_unset=True)
    if "title" in update_data and "slug" not in update_data and not trip.slug:
        update_data["slug"] = slugify(update_data["title"])
    
    for key, value in update_data.items():
        setattr(trip, key, value)
    
    db.commit()
    db.refresh(trip)
    return trip

@router.delete("/trips/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    db.delete(trip)
    db.commit()
    return None

# Day Entries CRUD
@router.post("/trips/{trip_id}/entries", response_model=DayEntryResponse, status_code=status.HTTP_201_CREATED)
def create_day_entry(
    trip_id: int,
    payload: DayEntryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    
    # Calculate default order_index if not supplied
    if not payload.order_index:
        last_entry = db.query(DayEntry).filter(DayEntry.trip_id == trip_id).order_by(DayEntry.order_index.desc()).first()
        order_index = (last_entry.order_index + 1) if last_entry else 1
    else:
        order_index = payload.order_index

    entry = DayEntry(
        trip_id=trip_id,
        date=payload.date,
        title=payload.title,
        body_markdown=payload.body_markdown,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        order_index=order_index
    )
    db.add(entry)
    db.flush()

    # Add media items if any
    if payload.media:
        for idx, m in enumerate(payload.media):
            media_item = Media(
                day_entry_id=entry.id,
                type=m.type,
                url=m.url,
                caption=m.caption,
                order_index=m.order_index or (idx + 1)
            )
            db.add(media_item)

    db.commit()
    db.refresh(entry)
    return entry

@router.put("/entries/{entry_id}", response_model=DayEntryResponse)
def update_day_entry(
    entry_id: int,
    payload: DayEntryUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    entry = db.query(DayEntry).filter(DayEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Étape non trouvée")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)
    
    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_day_entry(
    entry_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    entry = db.query(DayEntry).filter(DayEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Étape non trouvée")
    db.delete(entry)
    db.commit()
    return None

# Media CRUD
@router.post("/entries/{entry_id}/media", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
def add_media_to_entry(
    entry_id: int,
    payload: MediaCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    entry = db.query(DayEntry).filter(DayEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Étape non trouvée")
    
    media = Media(
        day_entry_id=entry_id,
        type=payload.type,
        url=payload.url,
        caption=payload.caption,
        order_index=payload.order_index or len(entry.media) + 1
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media

@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Média non trouvé")
    db.delete(media)
    db.commit()
    return None

# GeoJSON for Leaflet Map
@router.get("/trips/{identifier}/geojson")
def get_trip_geojson(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if identifier.isdigit():
        trip = db.query(Trip).options(
            joinedload(Trip.entries).joinedload(DayEntry.media)
        ).filter(Trip.id == int(identifier)).first()
    else:
        trip = db.query(Trip).options(
            joinedload(Trip.entries).joinedload(DayEntry.media)
        ).filter(Trip.slug == identifier).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")

    if not trip.is_public and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voyage privé réservé à l'administrateur.")

    features = []
    coordinates = []

    # Sort entries by order_index, then date
    sorted_entries = sorted(trip.entries, key=lambda e: (e.order_index, e.date))

    for idx, entry in enumerate(sorted_entries, 1):
        coord = [entry.longitude, entry.latitude]
        coordinates.append(coord)

        # Get first photo thumbnail if available
        first_media = next((m for m in entry.media if m.type == "photo"), None)
        thumb_info = process_media_item(first_media) if first_media else None

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coord
            },
            "properties": {
                "id": entry.id,
                "step_number": idx,
                "title": entry.title,
                "date": entry.date.strftime("%d/%m/%Y") if entry.date else "",
                "location_name": entry.location_name,
                "thumbnail_url": thumb_info["display_url"] if thumb_info else None,
                "media_count": len(entry.media),
            }
        })

    # Add Route LineString if we have at least 2 points
    if len(coordinates) >= 2:
        features.insert(0, {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "type": "route",
                "point_count": len(coordinates)
            }
        })

    return {
        "type": "FeatureCollection",
        "trip": {
            "id": trip.id,
            "title": trip.title,
            "slug": trip.slug,
            "total_steps": len(sorted_entries)
        },
        "features": features
    }

@router.post("/seed")
def seed_database(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = create_demo_data(db)
    return {"message": "Données de démonstration initialisées avec succès", "trip_slug": trip.slug}

# --------------------------------------------------------------------------
# User Management (Admin Only)
# --------------------------------------------------------------------------
@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return db.query(User).order_by(User.role.asc(), User.created_at.desc()).all()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_api(
    payload: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    clean_username = payload.username.strip()
    if len(clean_username) < 3:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur trop court (min. 3 caractères).")
    
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (min. 6 caractères).")

    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Le nom d'utilisateur « {clean_username} » est déjà utilisé.")

    new_user = User(
        username=clean_username,
        hashed_password=hash_password(payload.password),
        role=payload.role if payload.role in ("admin", "guest") else "guest",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Impossible de supprimer votre propre compte administrateur.")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    db.delete(user)
    db.commit()
    return None
