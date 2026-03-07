from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.userdesignation import UserDesignationCreate, UserDesignationRead
from app.services.userdesignation import (
    create_user_designation,
    delete_user_designation,
)
from app.services.userdesignation import (
    list_user_designations as list_user_designations_service,
)

router = APIRouter(prefix="/user-designation", tags=["user-designation"])


@router.post("/add", response_model=UserDesignationRead)
def create_user_designation(
    payload: UserDesignationCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Create a new user-designation association (body contains designation_id)."""
    success, result = create_user_designation(payload, session, user.id)
    if not success:
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post("/delete")
def delete_user_designation(
    user_designation_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Delete a user-designation association."""
    succcess, result = delete_user_designation(user_designation_id, session, user.id)
    if not succcess:
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post("/list", response_model=list[UserDesignationRead])
def list_user_designations(
    session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    """List all user-designation associations for the current user."""
    success, user_designations = list_user_designations_service(session, user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not fetch user designations")
    return user_designations
