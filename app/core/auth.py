from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_session_token
from app.models.user import User

SESSION_COOKIE_NAME = "session_token"

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Extract user from session cookie or Authorization header, or None if anonymous."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    
    # Also support Authorization: Bearer <token> for API requests
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        return None

    claims = verify_session_token(token)
    if not claims:
        return None

    user_id = claims.get("uid")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user

def get_current_user(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Ensure user is logged in (admin or guest). Redirects browser to /login if not."""
    if not user:
        if request.url.path.startswith("/api/"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Non authentifié. Veuillez vous connecter."
            )
        # For web pages, redirect to login page with return URL
        next_url = request.url.path
        if request.url.query:
            next_url += f"?{request.url.query}"
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": f"/login?next={next_url}"}
        )
    return user

def require_admin(
    request: Request,
    user: User = Depends(get_current_user)
) -> User:
    """Ensure user is logged in and has the admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé : privilèges administrateur requis."
        )
    return user
