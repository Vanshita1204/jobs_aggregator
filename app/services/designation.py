"""
Designation service.
"""

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.designation import Designation, DesignationCreate


def create_designation(payload: DesignationCreate, session: Session, user_id: int):
    """Create a new designation.

    The check-then-insert below is still the fast path (avoids a wasted
    round-trip under normal use), but `Designation.title` now also has a
    DB-level UNIQUE constraint, so a genuine race (two requests passing the
    check at once) raises `IntegrityError` on commit instead of creating a
    duplicate — caught here and turned into the same "already exists"
    result the pre-check would have given serially.
    """
    existing = session.exec(
        select(Designation).where(Designation.title == payload.title)
    ).first()
    if existing:
        return False, "Designation already exists"

    designation = Designation(title=payload.title, created_by=user_id)
    session.add(designation)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return False, "Designation already exists"
    session.refresh(designation)
    return True, designation


def list_designations(session: Session):
    """List all designations."""
    designations = session.exec(select(Designation)).all()
    return designations
