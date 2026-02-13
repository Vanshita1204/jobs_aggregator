from datetime import datetime

from db.session import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from models.user import User
from sqlmodel import Session, select

from core.utils import create_access_token, verify_password
from db.session import get_session
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
def register(
    email: str, full_name: str, password: str, session: Session = Depends(get_session)
):
    """
    Register a new user. Checks if email is already registered and raises 400 if so.
    """
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = password + "_not_hashed"  # Placeholder for hashing logic

    db_user = User(email=email, full_name=full_name, hashed_password=hashed_password)
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
