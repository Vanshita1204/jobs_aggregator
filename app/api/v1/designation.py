from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.designation import DesignationCreate, DesignationRead
from app.services.designation import create_designation as create_designation_service
from app.services.designation import list_designations as list_designations_service

router = APIRouter(prefix="/designation", tags=["designation"])


@router.post("/add", response_model=DesignationRead)
def create_designation(
    payload: DesignationCreate,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """Create a new designation (request body)."""
    success, designation = create_designation_service(payload, session, user.id)
    if not success:
        raise HTTPException(status_code=400, detail=designation)
    return designation


@router.post("/list", response_model=list[DesignationRead])
def list_designations(session: Session = Depends(get_session)):
    """List all designations."""
    designations = list_designations_service(session)
    return designations
