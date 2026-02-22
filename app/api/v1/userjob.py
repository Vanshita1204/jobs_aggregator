from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import get_session, get_current_user
from app.models.user import User
from app.models.userjob import (
    UserJobCreateUpdate,
    UserJobResponse
)
from app.models.enums import JobStatus
from app.services.user_job import (
    upsert_user_job,
    get_user_jobs
)

router = APIRouter(prefix="/user-jobs", tags=["User Jobs"])


@router.post("", response_model=UserJobResponse)
def create_or_update_user_job(
    payload: UserJobCreateUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    user_job = upsert_user_job(
        session=session,
        user_id=user.id,
        job_id=payload.job_id,
        status=payload.status
    )
    return user_job


@router.get("", response_model=list[UserJobResponse])
def list_user_jobs(
    status: JobStatus | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return get_user_jobs(
        session=session,
        user_id=user.id,
        status=status
    )