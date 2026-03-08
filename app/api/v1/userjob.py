"""
UserJob API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.auth import get_current_user, get_session
from app.models.user import User
from app.models.userjob import UserJobCreateUpdate, UserJobResponse
from app.services.user_job import upsert_user_job

router = APIRouter(prefix="/user-jobs", tags=["User Jobs"])


@router.post("", response_model=UserJobResponse)
def create_or_update_user_job(
    payload: UserJobCreateUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Create or update a user job."""
    user_id = user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="Authenticated user has no id")
    user_job = upsert_user_job(
        session=session, user_id=user_id, job_id=payload.job_id, status=payload.status
    )
    return user_job
