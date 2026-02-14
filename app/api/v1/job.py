from app.core.utils import get_current_user
from app.db.session import get_session
from fastapi import APIRouter, Depends
from app.models.job import Job, JobRead
from app.models.userdesignation import UserDesignation
from sqlmodel import Session, select

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/list", response_model=list[JobRead])
def list_jobs(session: Session = Depends(get_session), user=Depends(get_current_user)):
    """List all jobs for the current user's designations."""
    stmt = select(Job).where(
        Job.designation_id.in_(
            select(UserDesignation.designation_id).where(UserDesignation.user_id == user.id)
        )
    )
    jobs = session.exec(stmt).all()
    return jobs
