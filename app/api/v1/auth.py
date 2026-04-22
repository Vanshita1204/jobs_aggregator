"""
Auth API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.user import User, UserCreate, UserRead
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: UserCreate, session: Session = Depends(get_session)):
    """Register a new user."""
    return register_user(session, payload.email, payload.password, payload.full_name)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """Login a user."""
    token = login_user(session, form_data.username, form_data.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserRead)
def get_current_user_me(user: User = Depends(get_current_user)):
    """Get the current authenticated user."""
    return user
