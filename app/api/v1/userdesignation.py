from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.utils import get_current_user
from app.db.session import get_session
from app.models.designation import Designation
from app.models.user import User
from app.models.userdesignation import (
    UserDesignation,
    UserDesignationCreate,
    UserDesignationRead,
)

router = APIRouter(prefix="/user-designation", tags=["user-designation"])


@router.post("/add", response_model=UserDesignationRead)
def create_user_designation(
    payload: UserDesignationCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Create a new user-designation association (body contains designation_id)."""
    user_obj = session.exec(select(User).where(User.id == user.id)).first()
    if not user_obj:
        raise HTTPException(status_code=400, detail="User not found")

    designation = session.exec(
        select(Designation).where(Designation.id == payload.designation_id)
    ).first()
    if not designation:
        raise HTTPException(status_code=400, detail="Designation not found")

    # Check if the user already has this designation
    existing = session.exec(
        select(UserDesignation).where(
            UserDesignation.user_id == user.id,
            UserDesignation.designation_id == payload.designation_id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has this designation")

    user_designation = UserDesignation(
        user_id=user.id, designation_id=payload.designation_id
    )
    session.add(user_designation)
    session.commit()
    session.refresh(user_designation)
    return user_designation


@router.post("/delete")
def delete_user_designation(
    user_designation_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Delete a user-designation association."""
    user_designation = session.exec(
        select(UserDesignation).where(
            UserDesignation.id == user_designation_id,
            UserDesignation.user_id == user.id,
        )
    ).first()
    if not user_designation:
        raise HTTPException(
            status_code=400, detail="User-Designation association not found"
        )

    session.delete(user_designation)
    session.commit()
    return {"detail": "User-Designation association deleted"}


@router.post("/list", response_model=list[UserDesignationRead])
def list_user_designations(
    session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    """List all user-designation associations for the current user."""
    user_designations = session.exec(
        select(UserDesignation).where(UserDesignation.user_id == user.id)
    ).all()
    return user_designations
