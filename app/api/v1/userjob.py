from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import get_current_user, get_session
from app.models.enums import JobStatus
from app.models.user import User
from app.models.userjob import UserJobCreateUpdate, UserJobResponse
from app.services.user_job import fetch_job_records, upsert_user_job

router = APIRouter(prefix="/user-jobs", tags=["User Jobs"])


@router.post("", response_model=UserJobResponse)
def create_or_update_user_job(
    payload: UserJobCreateUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    user_job = upsert_user_job(
        session=session, user_id=user.id, job_id=payload.job_id, status=payload.status
    )
    return user_job

