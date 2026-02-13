from core.utils import get_current_user
from db.session import get_session
from fastapi import APIRouter, Depends, HTTPException
from models.designation import Designation
from sqlmodel import Session, select

router = APIRouter(prefix="/designation", tags=["designation"])


@router.post("/add")
def create_designation(
    name: str, session: Session = Depends(get_session), user=Depends(get_current_user)
):
    """
    Create a new designation. Checks if a designation with the same name already exists and raises 400 if so.
    """
    existing = session.exec(
        select(Designation).where(Designation.title == name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Designation already exists")

    designation = Designation(title=name, created_by=user.id)
    session.add(designation)
    session.commit()
    session.refresh(designation)
    return designation


@router.post("/list")
def list_designations(session: Session = Depends(get_session)):
    """
    List all designations.
    """
    designations = session.exec(select(Designation)).all()
    return designations
