from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.job import Job, JobRead
from app.services.jobs import fetch_job_records

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/list", response_model=list[JobRead])
def list_jobs(session: Session = Depends(get_session), user=Depends(get_current_user)):
    """List all jobs for the current user's designations."""
    jobs = fetch_job_records(session, user.id)
    return jobs
