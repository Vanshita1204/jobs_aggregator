from core.utils import get_current_user
from db.session import get_session
from fastapi import APIRouter, Depends
from models.job import Job
from models.userdesignation import UserDesignation
from sqlmodel import Session, select

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/list")
def list_jobs(session: Session = Depends(get_session), user=Depends(get_current_user)):
    """
    List all jobs.
    """
    jobs = (
        session.exec(select(Job))
        .where(
            Job.designation_id.in_(
                select(UserDesignation.designation_id).where(
                    UserDesignation.user_id == user.id
                )
            )
        )
        .all()
    )
    return jobs
