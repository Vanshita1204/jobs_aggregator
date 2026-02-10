from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session

from db.session import get_session
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User)
def register(user: User, session: Session = Depends(get_session)):
    """
    Register a new user. Checks if email is already registered and raises 400 if so.
    """
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = user.password + "_not_hashed"  # Placeholder for hashing logic

    db_user = User(email=user.email, full_name=user.full_name, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get("/login")
async def login():
    return {"message": "Login Page"}

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def login():
    return {"message": "Login Page"}
