from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.utils import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.session import get_session
from app.models.user import User, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
def register(user: UserCreate, session: Session = Depends(get_session)):
    """Register a new user using JSON body (UserCreate). Returns UserRead."""

    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    db_user = User(
        email=user.email, full_name=user.full_name, hashed_password=hashed_password
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == form_data.username)).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token({"sub": str(user.id)})

    user.last_login = datetime.now()
    session.add(user)
    session.commit()

    return {"access_token": token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user
