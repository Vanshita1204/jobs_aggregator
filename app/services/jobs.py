"""
Jobs service.
"""

from datetime import datetime, timedelta

from sqlalchemy import and_, func
from sqlmodel import Session, case, select

from app.core.config import settings
from app.db.session import engine
from app.models.enums import JobStatus
from app.models.job import Job
from app.models.userdesignation import UserDesignation
from app.models.userjob import UserJob
from app.models.userjobpreference import UserJobPreference


def create_job_records(jobs, designation: int):
    """Create job records, skipping duplicates by source_url."""
    to_insert: list[dict] = []
    seen_urls: set[str] = set()

    for j in jobs:
        url = j.get("source_url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        to_insert.append(
            {
                "title": j.get("title", ""),
                "company": j.get("company", ""),
                "location": j.get("location"),
                "description": j.get("description", ""),
                "source": j.get("source", "N/A"),
                "source_url": url,
                "designation_id": designation,
            }
        )

    if not to_insert:
        return

    with Session(engine) as session:
        # Single query to find all already-existing URLs in this batch
        existing_urls: set[str] = set(
            session.exec(
                select(Job.source_url).where(
                    Job.source_url.in_([jd["source_url"] for jd in to_insert])
                )
            ).all()
        )

        new_jobs = [
            Job(**jd) for jd in to_insert if jd["source_url"] not in existing_urls
        ]
        if new_jobs:
            session.add_all(new_jobs)
            session.commit()


def fetch_job_records(session: Session, user_id: int, status: JobStatus | None = None):
    """Fetch job records."""

    if not status:
        excluded_keywords = session.exec(
            select(UserJobPreference.keyword).where(
                UserJobPreference.user_id == user_id,
                UserJobPreference.is_excluded.is_(True),
            )
        ).all()

        threshold_time = datetime.now() - timedelta(
            hours=settings.NEW_JOB_THRESHOLD_HOURS
        )
        is_new_col = case(
            (Job.created_at > threshold_time, True),
            else_=False,
        ).label("is_new")
        stmt = (
            select(Job, is_new_col)
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

        if excluded_keywords:
            normalized_title = func.replace(
                func.replace(func.lower(Job.title), " ", ""),
                "-",
                "",
            )

            for keyword in excluded_keywords:
                normalized_keyword = keyword.replace(" ", "").replace("-", "").lower()
                stmt = stmt.where(~normalized_title.like(f"%{normalized_keyword}%"))

        results = session.exec(stmt).all()
        results = [{**job.model_dump(), "is_new": is_new} for job, is_new in results]
        return results

    stmt = (
        select(Job, UserJob.id.label("user_job_id"), UserJob.status.label("user_status"))
        .join(
            UserDesignation,
            Job.designation_id == UserDesignation.designation_id,
        )
        .join(
            UserJob,
            and_(
                UserJob.job_id == Job.id,
                UserJob.user_id == user_id,
                UserJob.status == status,
            ),
        )
        .where(UserDesignation.user_id == user_id)
        .order_by(Job.created_at.desc())
    )

    return [
        {**job.model_dump(), "user_job_id": uj_id, "user_status": uj_status}
        for job, uj_id, uj_status in session.exec(stmt).all()
    ]
