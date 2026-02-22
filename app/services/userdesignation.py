from sqlmodel import Session, select

from app.models import user
from app.models.designation import Designation
from app.models.user import User
from app.models.userdesignation import UserDesignation, UserDesignationCreate


def create_user_designation(
    payload: UserDesignationCreate, session: Session, user_id: int
):
    """Create a new user-designation association (body contains designation_id)."""
    user_obj = session.exec(select(User).where(User.id == user_id)).first()
    if not user_obj:
        return False, "User not found"

    designation = session.exec(
        select(Designation).where(Designation.id == payload.designation_id)
    ).first()
    if not designation:
        return False, "Designation not found"

    # Check if the user already has this designation
    existing = session.exec(
        select(UserDesignation).where(
            UserDesignation.user_id == user_id,
            UserDesignation.designation_id == payload.designation_id,
        )
    ).first()
    if existing:
        return False, "User already has this designation"

    user_designation = UserDesignation(
        user_id=user_id, designation_id=payload.designation_id
    )
    session.add(user_designation)
    session.commit()
    session.refresh(user_designation)
    return True, user_designation


def delete_user_designation(user_designation_id: int, session: Session, user_id: int):
    """Delete a user-designation association."""
    user_designation = session.exec(
        select(UserDesignation).where(
            UserDesignation.id == user_designation_id,
            UserDesignation.user_id == user.id,
        )
    ).first()
    if not user_designation:
        return False, "User-Designation association not found"

    session.delete(user_designation)
    session.commit()
    return True, {"detail": "User-Designation association deleted"}


def list_user_designations(session: Session, user_id: int):
    """List all user-designation associations for the current user."""
    user_designations = session.exec(
        select(UserDesignation).where(UserDesignation.user_id == user_id)
    ).all()
    return True, user_designations
