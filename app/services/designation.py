"""
Designation service.
"""
from sqlmodel import Session, select

from app.models.designation import Designation, DesignationCreate


def create_designation(payload: DesignationCreate, session: Session, user_id: int):
    """Create a new designation ."""
    existing = session.exec(
        select(Designation).where(Designation.title == payload.title)
    ).first()
    if existing:
        return False, "Designation already exists"

    designation = Designation(title=payload.title, created_by=user_id)
    session.add(designation)
    session.commit()
    session.refresh(designation)
    return True, designation


def list_designations(session: Session):
    """List all designations."""
    designations = session.exec(select(Designation)).all()
    return designations
