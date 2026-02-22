from sqlmodel import Session, select

from app.db.session import engine
from app.models.job import Job
from app.models.userdesignation import UserDesignation


from sqlmodel import select
from sqlalchemy import and_

from app.models.job import Job
from app.models.userdesignation import UserDesignation
from app.models.userjob import UserJob


def create_job_records(jobs, designation: int):
    # Prepare jobs for insertion: attach designation_id and ensure required fields
    to_insert = []
    for j in jobs:
        job_data = {
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location"),
            "description": j.get("description", ""),
            "source": j.get("source", "N/A"),
            "source_url": j.get("source_url"),
            "designation_id": designation,
        }
        if not job_data["source_url"]:
            continue
        to_insert.append(job_data)

    # Insert new jobs into DB, skipping duplicates (by source_url)
    if to_insert:
        with Session(engine) as session:
            for jd in to_insert:
                exists = session.exec(
                    select(Job).where(Job.source_url == jd["source_url"])
                ).first()
                if exists:
                    continue
                job_obj = Job(**jd)
                session.add(job_obj)
            session.commit()


def fetch_job_records(session: Session, user_id: int):
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

    return session.exec(stmt).all()