"""
Auth service.
"""

from sqlmodel import Session, select

from app.core.auth import create_access_token, hash_password, verify_password
from app.models.designation import Designation
from app.models.user import User
from app.models.userdesignation import UserDesignation


def register_user(session: Session, email: str, password: str, full_name: str):
    """Register a new user and auto-assign all existing designations.

    Input:
        session (Session): active DB session.
        email (str), password (str), full_name (str): new account fields.

    Output: User — the freshly-committed row, safe to serialize.

    Calls: `app.core.auth.hash_password()`, `session.add()`/`commit()`/`refresh()`.
    Called by: `app.api.v1.auth.register()` — `POST /auth/register`.

    Variables:
        user (User): the row being created; refreshed twice (see logic).
        designations (list[Designation]): every designation that exists at
            the moment of registration — a designation created afterward is
            not retroactively subscribed.

    Logic:
        1. Hash the password and insert the `User` row; commit and refresh
           so `user.id` is available.
        2. Insert one `UserDesignation` per existing `Designation`, auto-
           subscribing the new user to everything that currently exists.
        3. Commit again, then refresh `user` a second time: this second
           `commit()` expires the `user` instance's attributes under
           SQLAlchemy's default `expire_on_commit` behaviour, so without
           this refresh the returned object would serialize as `{}` — this
           is exactly the bug found and fixed via the pytest suite in `tests/`.
    """
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    designations = session.exec(select(Designation)).all()
    for designation in designations:
        session.add(UserDesignation(user_id=user.id, designation_id=designation.id))
    session.commit()
    session.refresh(user)

    return user


def login_user(session: Session, email: str, password: str):
    """Verify credentials and issue a JWT for a user.

    Input: session (Session), email (str), password (str).
    Output: str | None — a signed JWT on success, None on any failure
        (unknown email, wrong password, or a user row with no id).

    Calls: `app.core.auth.verify_password()`, `app.core.auth.create_access_token()`.
    Called by: `app.api.v1.auth.login()` — `POST /auth/login`.

    Variables:
        user (User | None): the row matching `email`, or None if not found.
        user_id (int | None): `user.id`, re-checked for None as a
            defensive guard (a persisted row should always have one).

    Logic: look up the user by email; return None immediately if not
        found or the password hash doesn't verify — this single early
        return is why login failures are indistinguishable to the caller
        (no separate "no such user" vs "wrong password" signal). Otherwise
        mint and return a token for `user_id`.
    """
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        return None

    user_id = user.id
    if user_id is None:
        return None

    token = create_access_token(user_id)
    return token
