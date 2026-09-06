from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_session_token
from app.core.auth import SESSION_COOKIE_NAME, get_current_user_optional
from app.models.user import User

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    next: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # If already logged in, redirect to home or destination
    if current_user:
        return RedirectResponse(url=next or "/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "next": next or "/",
            "error": None,
            "current_user": None
        }
    )

@router.post("/login", response_class=HTMLResponse)
def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = Form("/"),
    db: Session = Depends(get_db)
):
    username_clean = username.strip()
    user = db.query(User).filter(User.username == username_clean, User.is_active == True).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "next": next or "/",
                "error": "Identifiant ou mot de passe incorrect.",
                "username": username_clean,
                "current_user": None
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Valid credentials: create session token
    token = create_session_token(user_id=user.id, username=user.username, role=user.role)

    # Validate redirect target (prevent open redirect vulnerabilities)
    redirect_target = next if next and next.startswith("/") and not next.startswith("//") else "/"
    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=30 * 86400,
        samesite="lax",
        secure=False  # Allow local HTTP development
    )
    return response

@router.get("/logout")
def logout_action():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response
