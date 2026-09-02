"""Celery tasks that drive the scraping pipeline.

Each task opens its own DB session (tasks run in a separate worker process
from the FastAPI app, so `Depends(get_session)` is not available) and
best-effort iterates designations: one designation's scrape failure is
caught and logged, and does not stop the others.
"""

from sqlmodel import Session

from app.core.celery import celery_app
from app.db.session import engine
from app.models.designation import Designation
from app.services.designation import list_designations
from app.services.ingestion.job_fetcher import fetch_jobs_for_designation
from app.services.jobs import create_job_records


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def job_fetching_task(self):
    """Scrape and persist new jobs for every designation in the system.

    Input: none (`self` is the bound Celery task instance, unused directly).
    Output: none — persists rows via `create_job_records()`; no return value.

    Calls: `list_designations()`, `fetch_jobs_for_designation()`,
        `create_job_records()`.
    Called by: Celery Beat, on the `"fetch-jobs-daily"` schedule in
        `app.core.celery` (`crontab(hour=0, minute=0)`, `Asia/Kolkata`).

    Variables:
        session (Session): task-local DB session (opened here since Celery
            workers run outside the FastAPI dependency-injection context).
        designations (list[Designation]): every row in the `designation` table.
        desig (Designation): the designation currently being scraped, in the loop.
        jobs (list[dict]): parsed listings for `desig`, or empty/absent on failure.

    Logic:
        1. Open a DB session and load every `Designation`.
        2. For each one, scrape (`fetch_jobs_for_designation`) and, if any
           jobs came back, persist them (`create_job_records`).
        3. Catch and log any exception per-designation so one bad designation
           does not abort the loop for the rest.
        4. The whole task additionally retries up to 3 times with backoff
           (`autoretry_for`) if an exception escapes this per-designation
           try/except — i.e. only a bug outside the loop body itself.
    """

    with Session(engine) as session:
        designations = list_designations(session)

        for desig in designations:
            try:
                jobs = fetch_jobs_for_designation(designation=desig)

                if jobs:
                    create_job_records(jobs, desig.id)

            except Exception as e:
                print(f"Failed for designation {desig.title}: {e}")


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def job_fetching_task_designation(self, designation_id):
    """Scrape and persist new jobs for a single designation.

    Input:
        designation_id (int): id of the `Designation` to scrape for.

    Output: none — persists rows via `create_job_records()`, or logs and
        returns early if `designation_id` doesn't exist.

    Calls: `session.get(Designation, ...)`, `fetch_jobs_for_designation()`,
        `create_job_records()`.
    Called by: `app.api.v1.job.fetch_new_jobs()` — the `POST /jobs/fetch-new`
        route — dispatched once per designation the requesting user follows.

    Variables:
        session (Session): task-local DB session.
        desig (Designation | None): the row fetched for `designation_id`;
            None short-circuits the task.
        jobs (list[dict]): parsed listings for `desig`, or empty/absent on failure.

    Logic:
        1. Fetch the `Designation` row fresh from the DB by id (not passed
           in directly, since Celery task arguments must be
           JSON-serialisable — only the id crosses the broker).
        2. If it no longer exists, log and return without scraping.
        3. Otherwise scrape and persist exactly as `job_fetching_task()`
           does for one designation, with the same per-call exception
           containment.
    """
    with Session(engine) as session:
        desig = session.get(Designation, designation_id)
        if not desig:
            print(f"Designation {designation_id} not found")
            return

        try:
            jobs = fetch_jobs_for_designation(designation=desig)
            if jobs:
                create_job_records(jobs, desig.id)

        except Exception as e:
            print(f"Failed for designation {desig.title}: {e}")
