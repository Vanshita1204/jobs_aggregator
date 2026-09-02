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
    """Return the current user's job feed.

    Input:
        status (JobStatus | None): if omitted, returns the "unseen" feed
            (jobs under the user's subscribed designations with no status
            yet, keyword filters applied, newest first). If given, returns
            only jobs the user has explicitly marked with that status.

    Output: list[JobRead] — see `app.services.jobs.fetch_job_records` for
        the exact fields populated in each mode.

    Calls: `app.services.jobs.fetch_job_records()`.
    Called by: the frontend's `Jobs.jsx` page (route handler itself is the
        entry point, not called by other backend code).
    """
    user_id = user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="Authenticated user has no id")
    return fetch_job_records(session=session, user_id=user_id, status=status)


@router.post("/fetch-new")
def fetch_new_jobs(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Queue an on-demand scrape for every designation the user follows.

    Input: none beyond the authenticated `user`.
    Output: the (truthy) result of `list_user_designations`, not the scrape
        results themselves — scraping happens out-of-band in the worker.

    Calls: `list_user_designations()`,
        `job_fetching_task_designation.delay()` (Celery, async dispatch —
        not a direct function call, enqueues a message on Redis).
    Called by: the frontend's "Fetch new jobs" button in `Jobs.jsx`.

    Variables:
        user_designations (list[UserDesignation]): the caller's subscriptions,
            iterated to dispatch one scrape task per designation.

    Logic: load the user's subscriptions, then fire one
        `job_fetching_task_designation` Celery task per subscription and
        return immediately — this endpoint never waits for the scrape to
        finish; new jobs appear on a later `GET /jobs` poll.
    """
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
    """Ingest a single job from a pasted URL and mark it `is_external`.

    Input:
        body (AddJobRequest): target url, designation_id to file the job
            under, and an optional status (if given, a `UserJob` is also
            created for the requesting user at that status).
        x_llm_provider, x_llm_key: LLM credentials, used only if the URL
            doesn't match a natively-parsed portal.

    Output: JobRead-shaped dict. `is_new` is False if the URL already
        existed (in which case no new row or LLM call was made).

    Raises: HTTPException 502 if the page could not be fetched/parsed, 422
        if no title could be extracted from it.

    Calls: `_extract_jk()`, `ingest_job_from_url()`.
    Called by: the frontend's "Add Job" modal in `Jobs.jsx`.

    Variables:
        check_url (str): `body.url` normalised to Indeed's canonical
            `viewjob?jk=` form when applicable, used for the duplicate check.
        job_data (dict): `job.model_dump()` captured immediately after the
            first commit/refresh, before the optional second commit for
            `UserJob` — see the inline comment below for why this ordering
            matters (SQLAlchemy `expire_on_commit`).
        user_job_id (int | None): id of the `UserJob` created for the
            caller, if `body.status` was supplied.

    Logic:
        1. Normalise Indeed URLs and check for an existing `Job` with that
           `source_url`; if found, return it immediately with `is_new=False`
           and skip ingestion entirely (no LLM/network call on a duplicate).
        2. Otherwise ingest via `ingest_job_from_url()`; 502 on failure,
           422 if no title came back.
        3. Insert the new `Job` (flagged `is_external=True`), commit,
           refresh, and snapshot its fields into `job_data`.
        4. If a status was requested, also create a `UserJob` for the
           caller — this second commit is why `job_data` had to be
           captured beforehand rather than re-calling `job.model_dump()`
           in the return statement.
    """
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
    job_data = job.model_dump()

    user_job_id = None
    if body.status:
        from app.models.userjob import UserJob
        uj = UserJob(user_id=user.id, job_id=job.id, status=body.status)
        session.add(uj)
        session.commit()  # expires `job` under expire_on_commit; job_data was captured above
        session.refresh(uj)
        user_job_id = uj.id

    return {**job_data, "is_new": True, "user_job_id": user_job_id, "user_status": body.status}


@router.get("/{job_id}/description")
def get_job_description(
    job_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Return a job's description, fetching and caching it on first request.

    `Job.description` starts empty for scraped listings (the search-results
    page never contains the full description). This endpoint lazily fetches
    it from the source portal on first access and writes it back to the row
    so subsequent requests are served from the DB.

    Input: job_id (int) — id of the job to fetch the description for.
    Output: {"description": str} — empty string if the source fetch failed.
    Raises: HTTPException 404 if no job with `job_id` exists.

    Calls: `app.services.description.fetch_job_description()`.
    Called by: the frontend's job-detail expansion in `Jobs.jsx`.

    Logic: look up the job; if its `description` is already populated,
        return it as-is (cache hit, no network call). Otherwise fetch it
        from the source portal, and if non-empty, write it back to the row
        and commit before returning — so every call after the first is a
        cache hit.
    """
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
