"""
Designation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.designation import DesignationCreate, DesignationRead
from app.models.user import User
from app.services.designation import create_designation as create_designation_service
from app.services.designation import list_designations as list_designations_service

router = APIRouter(prefix="/designation", tags=["designation"])


@router.post("", response_model=DesignationRead)
def create_designation(
    payload: DesignationCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Create a new designation (request body)."""
    user_id = user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="Authenticated user has no id")

    success, designation = create_designation_service(payload, session, user_id)
    if not success:
        raise HTTPException(status_code=400, detail=designation)
    return designation


@router.get("", response_model=list[DesignationRead])
def list_designations(session: Session = Depends(get_session)):
    """List all designations."""
    designations = list_designations_service(session)
    return designations
