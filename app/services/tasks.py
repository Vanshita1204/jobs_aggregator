"""Celery tasks that drive the scraping pipeline.

Each task opens its own DB session (tasks run in a separate worker process
from the FastAPI app, so `Depends(get_session)` is not available) and
best-effort iterates designations: one designation's scrape failure is
caught and logged, and does not stop the others.
"""

import json

from sqlmodel import Session, select

from app.core.celery import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import engine
from app.models.designation import Designation
from app.models.job import Job
from app.services.description import fetch_job_description
from app.services.designation import list_designations
from app.services.ingestion.job_fetcher import fetch_jobs_for_designation
from app.services.jobs import create_job_records
from app.services.rag.embeddings import embed_text, job_embedding_text

logger = get_logger(__name__)


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

            except Exception:
                logger.exception("Failed for designation %s", desig.title)


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
            logger.warning("Designation %s not found", designation_id)
            return

        try:
            jobs = fetch_jobs_for_designation(designation=desig)
            if jobs:
                create_job_records(jobs, desig.id)

        except Exception:
            logger.exception("Failed for designation %s", desig.title)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def backfill_job_descriptions_task(self, limit: int | None = None):
    """Fetch and persist descriptions for every job that's still missing one.

    `Job.description` starts empty for scraped listings (the search-results
    page never contains the full description) and is otherwise only ever
    filled lazily, one job at a time, when a user opens `GET
    /jobs/{id}/description` (CV Tips modal). This task proactively backfills
    every such row daily, so descriptions — and the RAG embeddings that
    depend on them — aren't stuck waiting on a user to click into a job.

    Input:
        limit (int | None): max rows to process this run. Defaults to
            `settings.DESCRIPTION_BACKFILL_DAILY_LIMIT` (the scheduled daily
            call passes nothing). Pass an explicit number at least as large
            as the current backlog via `.delay(limit=...)` for a one-off
            catch-up run that ignores the daily cap. `self` is the bound
            Celery task instance, unused directly.
    Output: none — persists rows directly; no return value.

    Calls: `app.services.description.fetch_job_description()`,
        `app.services.rag.embeddings.embed_text()`/`job_embedding_text()`.
    Called by: Celery Beat, on the `"backfill-descriptions-daily"` schedule
        in `app.core.celery` (`crontab(hour=1, minute=0)`, `Asia/Kolkata` —
        an hour after `job_fetching_task`, so jobs scraped that same run
        are picked up too).

    Variables:
        session (Session): task-local DB session.
        jobs (list[Job]): up to `settings.DESCRIPTION_BACKFILL_DAILY_LIMIT`
            rows with an empty `description`, oldest first.
        job (Job): the row currently being backfilled, in the loop.
        desc (str): the fetched description, or "" on failure/unsupported source.

    Logic:
        1. Open a DB session and load `Job` rows with `description == ""`,
           oldest `created_at` first, capped at `limit` (defaulting to
           `settings.DESCRIPTION_BACKFILL_DAILY_LIMIT`, 200) — a large
           backlog on the scheduled daily call would otherwise turn into an
           hours-long run and burst-hammer Indeed/LinkedIn/Hirist with
           back-to-back requests, risking a block. Any backlog beyond the
           cap is simply picked up on the next day's run, oldest-first,
           until it's fully caught up (or immediately, via an explicit
           `limit` override for a one-off run).
        2. For each one, fetch its description via `fetch_job_description()`.
           A source fetch failure returns "" (already logged inside that
           function), in which case the row is left as-is and retried on
           the next day's run.
        3. On a non-empty result, also recompute the job's embedding
           (`job_embedding_text()` + `embed_text()`) — the embedding
           computed at insert time was built from an empty description, so
           leaving it stale would mean RAG search never actually reflects
           the description text for these rows.
        4. Commit after each job (not batched) so one job's failure never
           rolls back progress already made on the others, and a job that
           throws mid-fetch (network error, parser bug) is caught, logged,
           and skipped without aborting the rest of the run.
    """
    effective_limit = limit if limit is not None else settings.DESCRIPTION_BACKFILL_DAILY_LIMIT
    with Session(engine) as session:
        jobs = session.exec(
            select(Job)
            .where(Job.description == "")
            .order_by(Job.created_at.asc())
            .limit(effective_limit)
        ).all()
        logger.info("%d job(s) missing a description this run (cap: %d).", len(jobs), effective_limit)

        for job in jobs:
            try:
                desc = fetch_job_description(job.source, job.source_url)
                if not desc:
                    continue

                job.description = desc
                job.embedding = json.dumps(
                    embed_text(job_embedding_text(job.title, job.company, job.location, desc))
                )
                session.add(job)
                session.commit()

            except Exception:
                session.rollback()
                logger.exception("Failed to backfill description for job %s (%s)", job.id, job.source_url)
