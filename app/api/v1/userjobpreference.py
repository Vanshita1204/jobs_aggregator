from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.userjobpreference import UserJobPreferenceCreate
from app.services.userjobpreference import create_user_job_preference as create_user_job_preference_service

router = APIRouter(prefix="/user-job-preferences", tags=["User Job Preferences"])

@router.post("", status_code=201)
def create_user_job_preference(
    payload: UserJobPreferenceCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Create a new user job preference."""
    user_id = user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="Authenticated user has no id")
    success, result = create_user_job_preference_service(session, user_id, payload.keyword, payload.is_excluded)
    if not success:
        raise HTTPException(status_code=400, detail=result)
    return result