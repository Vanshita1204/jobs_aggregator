"""
Job API endpoints.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.enums import JobStatus
from app.models.job import Job, JobRead
from app.models.user import User
from app.services.description import fetch_job_description
from app.services.external_ingestion import _extract_jk, ingest_job_from_url
from app.services.jobs import fetch_job_records
from app.services.tasks import job_fetching_task_designation
from app.services.userdesignation import list_user_designations

router = APIRouter(prefix="/jobs", tags=["jobs"])


class AddJobRequest(BaseModel):
    url: str
    designation_id: int
    status: str | None = None  # if set, a UserJob is created for the adding user


@router.get("", response_model=list[JobRead])
def list_user_jobs(
    status: JobStatus | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """List all jobs for the current user."""
    user_id = user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="Authenticated user has no id")
    return fetch_job_records(session=session, user_id=user_id, status=status)


@router.post("/fetch-new")
def fetch_new_jobs(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """fetch latest jobs"""
    user_id = user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="Authenticated user has no id")
    success, user_designations = list_user_designations(
        session=session, user_id=user_id
    )
    for user_designation in user_designations:
        job_fetching_task_designation.delay(
            designation_id=user_designation.designation_id
        )
    return success


@router.post("/add", response_model=JobRead)
def add_job_manually(
    body: AddJobRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
    x_llm_provider: str = Header(default="groq"),
    x_llm_key: str = Header(default=""),
):
    """Ingest a single job from a URL. Visible to all users under the chosen designation."""
    # Normalise Indeed URLs before duplicate check
    check_url = body.url
    jk = _extract_jk(body.url)
    if jk and "indeed.com" in body.url:
        check_url = f"https://in.indeed.com/viewjob?jk={jk}"

    existing = session.exec(select(Job).where(Job.source_url == check_url)).first()
    if existing:
        return {**existing.model_dump(), "is_new": False}

    try:
        data = ingest_job_from_url(body.url, provider=x_llm_provider, api_key=x_llm_key or None)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch/parse job: {e}")

    if not data.get("title"):
        raise HTTPException(status_code=422, detail="Could not extract job title from the page.")

    job = Job(
        title=data["title"],
        company=data.get("company", ""),
        location=data.get("location") or None,
        description=data.get("description", ""),
        source=data["source"],
        source_url=data["source_url"],
        designation_id=body.designation_id,
        is_external=True,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    user_job_id = None
    if body.status:
        from app.models.userjob import UserJob
        uj = UserJob(user_id=user.id, job_id=job.id, status=body.status)
        session.add(uj)
        session.commit()
        session.refresh(uj)
        user_job_id = uj.id

    return {**job.model_dump(), "is_new": True, "user_job_id": user_job_id, "user_status": body.status}


@router.get("/{job_id}/description")
def get_job_description(
    job_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Return the job description, fetching from source and saving if not yet stored."""
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.description:
        desc = fetch_job_description(job.source, job.source_url)
        if desc:
            job.description = desc
            session.add(job)
            session.commit()

    return {"description": job.description}
