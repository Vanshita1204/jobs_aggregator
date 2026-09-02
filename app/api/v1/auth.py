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


@router.post("/register", response_model=UserRead)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    """Register a new user, auto-subscribed to every existing designation.

    Input: payload (UserCreate) — email, password, full_name.
    Output: UserRead (excludes hashed_password).
    Calls: `app.services.auth_service.register_user()`.
    Called by: the frontend's `Register.jsx` page.
    """
    return register_user(session, payload.email, payload.password, payload.full_name)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """Authenticate a user and issue a JWT.

    Input: form_data (OAuth2PasswordRequestForm) — username (email) and password.
    Output: {"access_token": str, "token_type": "bearer"}.
    Raises: HTTPException 401 for either an unknown email or a wrong
        password — the two cases are indistinguishable in the response, by design.

    Calls: `app.services.auth_service.login_user()`.
    Called by: the frontend's `Login.jsx` page.

    Variables:
        token (str | None): the signed JWT from `login_user()`, or None on
            any authentication failure.

    Logic: delegate credential verification entirely to `login_user()`;
        a falsy return (covers both "no such user" and "wrong password")
        maps to a single 401 here.
    """
    token = login_user(session, form_data.username, form_data.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserRead)
def get_current_user_me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user.

    Input: none — `user` is resolved entirely by the `get_current_user`
        dependency from the request's bearer token.
    Output: UserRead.
    Calls: none directly (`get_current_user` does the JWT decode + DB lookup).
    Called by: the frontend on app load, to restore session state.
    """
    return user
