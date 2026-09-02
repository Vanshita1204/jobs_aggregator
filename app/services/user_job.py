"""Per-user job status mutation.

`fetch_job_records` in this module is not currently wired to any API route —
`app.services.jobs.fetch_job_records` (a separate, near-duplicate
implementation) is what `GET /jobs` actually calls. Both exist in the
codebase; only the one in `jobs.py` is live.
"""

from datetime import datetime, timezone

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


def fetch_job_records(
    session: Session,
    user_id: int,
    status: JobStatus | None = None,
):
    """Dead code: superseded by `app.services.jobs.fetch_job_records`.

    Not called from any route. Kept for reference; see module docstring.

    If status is None: return jobs for the user's designations, excluding
    jobs already marked in UserJob (any status).
    If status is provided: return jobs explicitly marked with that status.
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
