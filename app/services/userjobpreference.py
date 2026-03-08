"""
UserJobPreference service.
"""
from sqlmodel import Session

from app.models.userjobpreference import UserJobPreference


def create_user_job_preference(session: Session, user_id: int, keyword: str, is_excluded: bool):
    """Create a new user job preference."""
    user_job_preference = UserJobPreference(user_id=user_id, keyword=keyword, is_excluded=is_excluded)
    session.add(user_job_preference)
    session.commit()
    session.refresh(user_job_preference)
    return True, user_job_preference