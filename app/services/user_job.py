"""Per-user job status mutation."""

from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.enums import JobStatus
from app.models.userjob import UserJob


def upsert_user_job(
    session: Session, user_id: int, job_id: int, status: JobStatus
) -> UserJob:
    """Create or update the (user, job) status record.

    Input:
        session (Session): active DB session.
        user_id (int): owning user's id.
        job_id (int): target job's id.
        status (JobStatus): new application status to set.

    Output:
        UserJob: the created or updated row, refreshed from the DB.

    Calls: `session.exec()`/`session.add()`/`session.commit()`/`session.refresh()`.
    Called by: `app.api.v1.userjob.create_or_update_user_job()` — the
        `POST /user-jobs` route.

    Variables:
        user_job (UserJob | None): the existing row for this
            `(user_id, job_id)` pair, or None if this is the first time.

    Logic:
        1. Look up an existing `UserJob` for `(user_id, job_id)` — the
           table's `UniqueConstraint` guarantees at most one such row.
        2. If found, mutate its `status`/`updated_at` in place (update path).
        3. If not found, construct and `add()` a new row (insert path).
        4. Commit and refresh either way, then return the row — this makes
           the function an upsert: calling it twice for the same pair
           never creates a duplicate.
    """
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
