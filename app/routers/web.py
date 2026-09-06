from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from slugify import slugify

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.trip import Trip, DayEntry, Media
from app.services.media_helpers import process_media_item, render_markdown, process_photo_url
from app.services.seed_data import create_demo_data

router = APIRouter(include_in_schema=False, dependencies=[Depends(get_current_user)])
templates = Jinja2Templates(directory="app/templates")

# Register custom Jinja filters
templates.env.filters["markdown"] = render_markdown
templates.env.filters["process_media"] = process_media_item

@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Trip).options(joinedload(Trip.entries))
    # Non-admin users only see public trips
    if current_user.role != "admin":
        query = query.filter(Trip.is_public == True)

    trips = query.order_by(Trip.start_date.desc().nullslast(), Trip.created_at.desc()).all()

    total_trips = len(trips)
    total_steps = sum(len(t.entries) for t in trips)
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "trips": trips,
            "total_trips": total_trips,
            "total_steps": total_steps,
            "current_user": current_user
        }
    )

# --------------------------------------------------------------------------
# User Management & Password (Admin Only)
# --------------------------------------------------------------------------
@router.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    success: Optional[int] = None,
    deleted: Optional[int] = None,
    password_changed: Optional[int] = None,
    new_username: Optional[str] = None
):
    users = db.query(User).order_by(User.role.asc(), User.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={
            "users": users,
            "current_user": current_user,
            "success": bool(success),
            "deleted": bool(deleted),
            "password_changed": bool(password_changed),
            "new_username": new_username,
            "error": None,
            "password_error": None,
            "form_username": ""
        }
    )

@router.post("/admin/password", response_class=HTMLResponse)
def admin_change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.role.asc(), User.created_at.desc()).all()

    if not verify_password(current_password, current_user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="users.html",
            context={
                "users": users,
                "current_user": current_user,
                "success": False,
                "deleted": False,
                "password_changed": False,
                "new_username": None,
                "error": None,
                "password_error": "Le mot de passe actuel saisi est incorrect.",
                "form_username": ""
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="users.html",
            context={
                "users": users,
                "current_user": current_user,
                "success": False,
                "deleted": False,
                "password_changed": False,
                "new_username": None,
                "error": None,
                "password_error": "Le nouveau mot de passe doit comporter au moins 6 caractères.",
                "form_username": ""
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="users.html",
            context={
                "users": users,
                "current_user": current_user,
                "success": False,
                "deleted": False,
                "password_changed": False,
                "new_username": None,
                "error": None,
                "password_error": "La confirmation ne correspond pas au nouveau mot de passe.",
                "form_username": ""
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    current_user.hashed_password = hash_password(new_password)
    db.commit()

    return RedirectResponse(
        url="/admin/users?password_changed=1",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/admin/users", response_class=HTMLResponse)
def admin_create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    clean_username = username.strip()
    users = db.query(User).order_by(User.role.asc(), User.created_at.desc()).all()

    # Validation
    if len(clean_username) < 3 or len(clean_username) > 50:
        return templates.TemplateResponse(
            request=request,
            name="users.html",
            context={
                "users": users,
                "current_user": current_user,
                "error": "Le nom d'utilisateur doit contenir entre 3 et 50 caractères.",
                "form_username": clean_username
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="users.html",
            context={
                "users": users,
                "current_user": current_user,
                "error": "Le mot de passe doit comporter au moins 6 caractères.",
                "form_username": clean_username
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="users.html",
            context={
                "users": users,
                "current_user": current_user,
                "error": f"Le nom d'utilisateur « {clean_username} » est déjà utilisé.",
                "form_username": clean_username
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Create new guest user
    new_user = User(
        username=clean_username,
        hashed_password=hash_password(password),
        role="guest",
        is_active=True
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(
        url=f"/admin/users?success=1&new_username={clean_username}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/admin/users/{user_id}/delete")
def admin_delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer votre propre compte administrateur."
        )

    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    db.delete(user_to_delete)
    db.commit()

    return RedirectResponse(url="/admin/users?deleted=1", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/trips/new", response_class=HTMLResponse)
def new_trip_page(
    request: Request,
    current_user: User = Depends(require_admin)
):
    return templates.TemplateResponse(
        request=request,
        name="trip_form.html",
        context={"trip": None, "is_edit": False, "current_user": current_user}
    )

@router.post("/trips/new")
def create_trip_action(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    cover_image_url: Optional[str] = Form(None),
    is_public: Optional[bool] = Form(False),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while db.query(Trip).filter(Trip.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    clean_cover_url = cover_image_url.strip() if cover_image_url and cover_image_url.strip() else None
    if clean_cover_url:
        clean_cover_url = process_photo_url(clean_cover_url)["display_url"]

    trip = Trip(
        title=title,
        slug=slug,
        description=description,
        start_date=s_date,
        end_date=e_date,
        cover_image_url=clean_cover_url,
        is_public=bool(is_public)
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return RedirectResponse(url=f"/trips/{trip.slug}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/trips/{slug}", response_class=HTMLResponse)
def trip_detail(
    request: Request,
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).options(
        joinedload(Trip.entries).joinedload(DayEntry.media)
    ).filter(Trip.slug == slug).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")

    # If trip is private and user is not admin, deny access
    if not trip.is_public and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voyage privé réservé à l'administrateur."
        )

    # Sort entries by order_index then date
    sorted_entries = sorted(trip.entries, key=lambda e: (e.order_index, e.date))

    # Process media for display
    entries_data = []
    for idx, entry in enumerate(sorted_entries, 1):
        processed_media = [process_media_item(m) for m in entry.media]
        entries_data.append({
            "entry": entry,
            "step_number": idx,
            "body_html": render_markdown(entry.body_markdown),
            "media_list": processed_media,
        })

    return templates.TemplateResponse(
        request=request,
        name="trip_detail.html",
        context={
            "trip": trip,
            "entries_data": entries_data,
            "total_entries": len(sorted_entries),
            "current_user": current_user
        }
    )

@router.get("/trips/{slug}/edit", response_class=HTMLResponse)
def edit_trip_page(
    request: Request,
    slug: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.slug == slug).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    return templates.TemplateResponse(
        request=request,
        name="trip_form.html",
        context={"trip": trip, "is_edit": True, "current_user": current_user}
    )

@router.post("/trips/{slug}/edit")
def edit_trip_action(
    request: Request,
    slug: str,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    cover_image_url: Optional[str] = Form(None),
    is_public: Optional[bool] = Form(False),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.slug == slug).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")

    trip.title = title
    trip.description = description
    trip.start_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    trip.end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    
    clean_cover_url = cover_image_url.strip() if cover_image_url and cover_image_url.strip() else None
    if clean_cover_url:
        clean_cover_url = process_photo_url(clean_cover_url)["display_url"]
    trip.cover_image_url = clean_cover_url

    trip.is_public = bool(is_public)

    db.commit()
    return RedirectResponse(url=f"/trips/{trip.slug}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/trips/{slug}/delete")
def delete_trip_action(
    slug: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.slug == slug).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    db.delete(trip)
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# Day Entries Forms
@router.get("/trips/{slug}/entries/new", response_class=HTMLResponse)
def new_entry_page(
    request: Request,
    slug: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.slug == slug).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    
    # Pre-populate default date & next order_index
    today_str = date.today().strftime("%Y-%m-%d")
    next_order = len(trip.entries) + 1

    return templates.TemplateResponse(
        request=request,
        name="entry_form.html",
        context={
            "trip": trip,
            "entry": None,
            "is_edit": False,
            "default_date": today_str,
            "next_order": next_order,
            "current_user": current_user
        }
    )

@router.post("/trips/{slug}/entries/new")
async def create_entry_action(
    request: Request,
    slug: str,
    title: str = Form(...),
    entry_date: str = Form(...),
    location_name: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    order_index: int = Form(1),
    body_markdown: Optional[str] = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.slug == slug).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")

    parsed_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
    entry = DayEntry(
        trip_id=trip.id,
        title=title,
        date=parsed_date,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        order_index=order_index,
        body_markdown=body_markdown
    )
    db.add(entry)
    db.flush()

    # Parse dynamic media fields from form data
    form_data = await request.form()
    media_types = form_data.getlist("media_type[]")
    media_urls = form_data.getlist("media_url[]")
    media_captions = form_data.getlist("media_caption[]")

    for idx in range(len(media_urls)):
        url = media_urls[idx].strip()
        if url:
            m_type = media_types[idx] if idx < len(media_types) else "photo"
            caption = media_captions[idx] if idx < len(media_captions) else None
            db.add(Media(
                day_entry_id=entry.id,
                type=m_type,
                url=url,
                caption=caption,
                order_index=idx + 1
            ))

    db.commit()
    return RedirectResponse(url=f"/trips/{trip.slug}#entry-{entry.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/trips/{slug}/entries/{entry_id}/edit", response_class=HTMLResponse)
def edit_entry_page(
    request: Request,
    slug: str,
    entry_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.slug == slug).first()
    entry = db.query(DayEntry).options(joinedload(DayEntry.media)).filter(DayEntry.id == entry_id).first()
    if not trip or not entry:
        raise HTTPException(status_code=404, detail="Étape non trouvée")

    return templates.TemplateResponse(
        request=request,
        name="entry_form.html",
        context={
            "trip": trip,
            "entry": entry,
            "is_edit": True,
            "default_date": entry.date.strftime("%Y-%m-%d") if entry.date else "",
            "next_order": entry.order_index,
            "current_user": current_user
        }
    )

@router.post("/trips/{slug}/entries/{entry_id}/edit")
async def edit_entry_action(
    request: Request,
    slug: str,
    entry_id: int,
    title: str = Form(...),
    entry_date: str = Form(...),
    location_name: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    order_index: int = Form(1),
    body_markdown: Optional[str] = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.slug == slug).first()
    entry = db.query(DayEntry).filter(DayEntry.id == entry_id).first()
    if not trip or not entry:
        raise HTTPException(status_code=404, detail="Étape non trouvée")

    entry.title = title
    entry.date = datetime.strptime(entry_date, "%Y-%m-%d").date()
    entry.location_name = location_name
    entry.latitude = latitude
    entry.longitude = longitude
    entry.order_index = order_index
    entry.body_markdown = body_markdown

    # Replace media items
    form_data = await request.form()
    media_types = form_data.getlist("media_type[]")
    media_urls = form_data.getlist("media_url[]")
    media_captions = form_data.getlist("media_caption[]")

    # Clear old media
    db.query(Media).filter(Media.day_entry_id == entry.id).delete()

    for idx in range(len(media_urls)):
        url = media_urls[idx].strip()
        if url:
            m_type = media_types[idx] if idx < len(media_types) else "photo"
            caption = media_captions[idx] if idx < len(media_captions) else None
            db.add(Media(
                day_entry_id=entry.id,
                type=m_type,
                url=url,
                caption=caption,
                order_index=idx + 1
            ))

    db.commit()
    return RedirectResponse(url=f"/trips/{trip.slug}#entry-{entry.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/trips/{slug}/entries/{entry_id}/delete")
def delete_entry_action(
    slug: str,
    entry_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    entry = db.query(DayEntry).filter(DayEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Étape non trouvée")
    db.delete(entry)
    db.commit()
    return RedirectResponse(url=f"/trips/{slug}", status_code=status.HTTP_303_SEE_OTHER)
