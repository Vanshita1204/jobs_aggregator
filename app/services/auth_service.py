from sqlmodel import Session, select

from app.core.auth import create_access_token, hash_password, verify_password
from app.models.user import User


def register_user(session: Session, email: str, password: str, full_name: str):
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_user(session: Session, email: str, password: str):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        return None

    token = create_access_token(user.id)
    return token
