from datetime import datetime, timezone
from sqlmodel import Session, select

from app.models.userjob import UserJob
from app.models.enums import JobStatus


def upsert_user_job(
    session: Session,
    user_id: int,
    job_id: int,
    status: JobStatus
) -> UserJob:
    user_job = session.exec(
        select(UserJob)
        .where(UserJob.user_id == user_id)
        .where(UserJob.job_id == job_id)
    ).first()

    if user_job:
        user_job.status = status
        user_job.updated_at = datetime.now(timezone.utc)
    else:
        user_job = UserJob(
            user_id=user_id,
            job_id=job_id,
            status=status
        )
        session.add(user_job)

    session.commit()
    session.refresh(user_job)
    return user_job


def get_user_jobs(
    session: Session,
    user_id: int,
    status: JobStatus | None = None
):
    stmt = select(UserJob).where(UserJob.user_id == user_id)
    if status:
        stmt = stmt.where(UserJob.status == status)
    return session.exec(stmt).all()