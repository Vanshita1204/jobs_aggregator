from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.enums import JobStatus
from app.models.job import Job, JobRead
from app.models.user import User
from app.models.userjob import UserJobResponse
from app.services.jobs import fetch_job_records

router = APIRouter(prefix="/jobs", tags=["jobs"])




@router.get("", response_model=list[JobRead])
def list_user_jobs(
    status: JobStatus | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return fetch_job_records(session=session, user_id=user.id, status=status)
