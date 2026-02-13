from core.utils import get_current_user
from db.session import get_session
from fastapi import APIRouter, Depends, HTTPException
from models.designation import Designation
from models.user import User
from models.userdesignation import UserDesignation
from sqlmodel import Session, select

router = APIRouter(prefix="/user-designation", tags=["user-designation"])


@router.post("/add")
def create_user_designation(
    designation_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """
    Create a new user-designation association. Checks if the user and designation exist and raises 400 if not.
    """
    user = session.exec(select(User).where(User.id == user.id)).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    designation = session.exec(
        select(Designation).where(Designation.id == designation_id)
    ).first()
    if not designation:
        raise HTTPException(status_code=400, detail="Designation not found")

    # Check if the user already has this designation
    existing = session.exec(
        select(UserDesignation).where(
            UserDesignation.user_id == user.id,
            UserDesignation.designation_id == designation_id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has this designation")

    user_designation = UserDesignation(user_id=user.id, designation_id=designation_id)
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
    """
    Delete a user-designation association. Checks if the user and designation exist and raises 400 if not.
    """
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


@router.post("/list")
def list_user_designations(
    session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    """
    List all user-designation associations.
    """
    user_designations = session.exec(
        select(UserDesignation).where(UserDesignation.user_id == user.id)
    ).all()
    return user_designations
