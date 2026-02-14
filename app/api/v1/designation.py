from app.core.utils import get_current_user
from app.db.session import get_session
from fastapi import APIRouter, Depends, HTTPException
from app.models.designation import Designation, DesignationCreate, DesignationRead
from sqlmodel import Session, select

router = APIRouter(prefix="/designation", tags=["designation"])


@router.post("/add", response_model=DesignationRead)
def create_designation(
    payload: DesignationCreate, session: Session = Depends(get_session), user=Depends(get_current_user)
):
    """Create a new designation (request body)."""
    existing = session.exec(select(Designation).where(Designation.title == payload.title)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Designation already exists")

    designation = Designation(title=payload.title, created_by=user.id)
    session.add(designation)
    session.commit()
    session.refresh(designation)
    return designation


@router.post("/list", response_model=list[DesignationRead])
def list_designations(session: Session = Depends(get_session)):
    """List all designations."""
    designations = session.exec(select(Designation)).all()
    return designations
