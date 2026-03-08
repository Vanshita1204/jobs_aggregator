from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.enums import JobStatus
from app.models.userjob import UserJob
from sqlalchemy import and_, func
from sqlmodel import Session, select

from app.models.enums import JobStatus  # assuming you have this
from app.models.job import Job
from app.models.userdesignation import UserDesignation
from app.models.userjob import UserJob
from app.models.userjobpreference import UserJobPreference


def upsert_user_job(
    session: Session, user_id: int, job_id: int, status: JobStatus
) -> UserJob:
    """Upsert a user job."""
    user_job = session.exec(
        select(UserJob)
        .where(UserJob.user_id == user_id)
        .where(UserJob.job_id == job_id)
    ).first()

    if user_job:
        user_job.status = status
        user_job.updated_at = datetime.now(timezone.utc)
    else:
        user_job = UserJob(user_id=user_id, job_id=job_id, status=status)
        session.add(user_job)

    session.commit()
    session.refresh(user_job)
    return user_job


def fetch_job_records(
    session: Session,
    user_id: int,
    status: JobStatus | None = None,
):
    """
    If status is None:
        return jobs for user's designations
        EXCLUDING jobs already marked in UserJob (any status)
    If status is provided:
        return jobs explicitly marked with that status
    """
    if status is None:
        excluded_keywords = session.exec(
            select(UserJobPreference.keyword).where(
                UserJobPreference.user_id == user_id,
                UserJobPreference.is_excluded.is_(True),
            )
        ).all()
        stmt = (
            select(Job)
            .join(
                UserDesignation,
                Job.designation_id == UserDesignation.designation_id,
            )
            .outerjoin(
                UserJob,
                and_(
                    UserJob.job_id == Job.id,
                    UserJob.user_id == user_id,
                ),
            )
            .where(UserDesignation.user_id == user_id)
            .where(UserJob.id.is_(None))
            .order_by(Job.created_at.desc())
        )
        for keyword in excluded_keywords:
            normalized_keyword = keyword.replace(" ", "").replace("-", "").lower()
            normalized_title = func.replace(
                func.replace(func.lower(Job.title), " ", ""), "-", ""
            )
            stmt = stmt.where(~normalized_title.like(f"%{normalized_keyword}%"))
    else:
        stmt = (
            select(Job)
            .join(
                UserJob,
                and_(
                    UserJob.job_id == Job.id,
                    UserJob.user_id == user_id,
                    UserJob.status == status,
                ),
            )
            .order_by(Job.created_at.desc())
        )

    return session.exec(stmt).all()
