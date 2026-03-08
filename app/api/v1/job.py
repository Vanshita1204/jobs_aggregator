"""
Job API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.enums import JobStatus
from app.models.job import JobRead
from app.models.user import User
from app.services.jobs import fetch_job_records
from app.services.userdesignation import list_user_designations
from app.services.tasks import job_fetching_task_designation

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobRead])
def list_user_jobs(
    status: JobStatus | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """List all jobs for the current user."""
    user_id = user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="Authenticated user has no id")
    return fetch_job_records(session=session, user_id=user_id, status=status)

@router.post("/fetch-new")
def fetch_new_jobs(session: Session = Depends(get_session),
    user: User = Depends(get_current_user),):
    """fetch latest jobs"""
    user_id= user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="Authenticated user has no id")
    success, user_designations = list_user_designations(session=session, user_id=user_id)
    for user_designation in user_designations:
        job_fetching_task_designation.delay(designation_id=user_designation.designation_id)
    return success
    
    
