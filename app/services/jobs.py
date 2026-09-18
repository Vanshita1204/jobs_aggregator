"""
Jobs service.
"""

import json
from datetime import datetime, timedelta

from sqlalchemy import and_, func
from sqlmodel import Session, case, select

from app.core.config import settings
from app.db.session import engine
from app.models.enums import JobStatus
from app.models.job import Job
from app.models.jobdesignation import JobDesignation
from app.models.userdesignation import UserDesignation
from app.models.userjob import UserJob
from app.models.userjobpreference import UserJobPreference
from app.services.rag.embeddings import embed_batch, job_embedding_text


def create_job_records(jobs, designation: int):
    """Batch-insert scraped job dicts, deduplicating by source_url.

    Input:
        jobs (list[dict]): raw listings as returned by the `parse_*_jobs`
            functions in `app.services.parsers` (keys: title, company,
            location, description, source, source_url).
        designation (int): id of the `Designation` these jobs belong to.

    Output:
        None. Persists new `Job` rows (plus a `JobDesignation` link for
        each) directly to the database; for a `source_url` that already
        exists under a *different* designation, links the existing job to
        `designation` instead of skipping it outright. Returns early with
        no side effect if there is nothing to do.

    Calls: `app.services.parsers.parse_*_jobs()` supply `jobs` upstream
        (not called from here); this function itself calls SQLModel's
        `session.exec()`/`session.add_all()`/`session.commit()`, plus
        `app.services.rag.embeddings.embed_batch()` and
        `job_embedding_text()` to compute each new row's RAG embedding.
    Called by: `app.services.tasks.job_fetching_task()`,
        `app.services.tasks.job_fetching_task_designation()`.

    Variables:
        to_insert (list[dict]): candidate rows after in-memory URL dedup,
            shaped to match `Job`'s constructor kwargs.
        seen_urls (set[str]): URLs already added to `to_insert` in this call,
            used to drop duplicates within the same scrape batch.
        existing_by_url (dict[str, int]): source_url -> job id, for URLs in
            this batch that already exist in the `job` table, found via one
            batched `IN` query.
        new_jobs (list[Job]): `to_insert` rows whose URL isn't in
            `existing_by_url`, instantiated as `Job` ORM objects ready to
            insert.
        embeddings (list[list[float]]): one embedding vector per entry in
            `new_jobs`, same order, from a single batched `embed_batch()`
            call (cheaper than embedding one job at a time).
        already_linked (set[int]): job ids among `existing_by_url`'s values
            that already have a `JobDesignation` row for `designation` —
            skipped so a repeat scrape under the same designation doesn't
            try to insert a duplicate link (which would violate its
            UNIQUE constraint).

    Logic:
        1. Walk `jobs`, skipping entries with no `source_url` or with a
           `source_url` already seen earlier in this same call
           (`seen_urls`) — this is the in-memory dedup pass.
        2. If nothing survived, return immediately (no DB call at all).
        3. Open a session and run a single `source_url IN (...)` query to
           find which of the surviving URLs already exist (`existing_by_url`)
           — this is the DB-level dedup pass.
        4. Build `Job` objects (with a `JobDesignation` link for
           `designation`) only for URLs not in `existing_by_url`.
        5. Batch-embed all `new_jobs` in one `embed_batch()` call and store
           each resulting vector, JSON-encoded, on `job.embedding`.
        6. Insert `new_jobs` in one `add_all()` + `commit()` batch. The
           `job.source_url` UNIQUE constraint is the final backstop if this
           function is ever invoked concurrently for overlapping URLs.
        7. For URLs that already existed: this is the actual duplicate fix
           — instead of silently skipping (the old behavior, which meant
           the same posting matching a second designation could only ever
           become visible there by inserting a second `Job` row), link the
           existing job to `designation` via `JobDesignation` if it isn't
           linked already.
    """
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
        existing_by_url: dict[str, int] = dict(
            session.exec(
                select(Job.source_url, Job.id).where(
                    Job.source_url.in_([jd["source_url"] for jd in to_insert])
                )
            ).all()
        )

        new_jobs = [
            Job(**jd) for jd in to_insert if jd["source_url"] not in existing_by_url
        ]
        if new_jobs:
            embeddings = embed_batch(
                [
                    job_embedding_text(job.title, job.company, job.location, job.description)
                    for job in new_jobs
                ]
            )
            for job, vector in zip(new_jobs, embeddings):
                job.embedding = json.dumps(vector)

            session.add_all(new_jobs)
            session.flush()  # assigns job.id without expiring attributes (unlike commit())
            for job in new_jobs:
                session.add(JobDesignation(job_id=job.id, designation_id=designation))

        existing_job_ids = set(existing_by_url.values())
        if existing_job_ids:
            already_linked = set(
                session.exec(
                    select(JobDesignation.job_id).where(
                        JobDesignation.designation_id == designation,
                        JobDesignation.job_id.in_(existing_job_ids),
                    )
                ).all()
            )
            for job_id in existing_job_ids - already_linked:
                session.add(JobDesignation(job_id=job_id, designation_id=designation))

        session.commit()


def fetch_job_records(
    session: Session,
    user_id: int,
    status: JobStatus | None = None,
    limit: int = 200,
    offset: int = 0,
):
    """Fetch the job feed for a user; backs `GET /jobs`.

    Input:
        session (Session): active SQLModel DB session.
        user_id (int): id of the requesting user.
        status (JobStatus | None): if provided, restricts results to jobs
            the user has marked with this exact status; if None, returns
            the "unseen" feed instead.
        limit (int): max rows to return (applied via SQL `LIMIT`, after the
            `ORDER BY created_at DESC` in both modes, so this bounds a full
            table scan rather than just truncating an already-fetched list).
        offset (int): rows to skip (SQL `OFFSET`), for paging past `limit`.

    Output:
        list[dict]: each dict is `Job.model_dump()` merged with either
        `is_new` (unseen mode) or `user_job_id`/`user_status` (status mode).

    Calls: SQLAlchemy Core `select()`/`join()`/`case()`/`func` query
        builders and `session.exec()`; no other project function is called.
    Called by: `app.api.v1.job.list_user_jobs()` — the `GET /jobs` route.

    Variables:
        excluded_keywords (list[str]): keywords the user has flagged
            `is_excluded=True` in `UserJobPreference`, applied only in
            unseen mode.
        threshold_time (datetime): now minus `NEW_JOB_THRESHOLD_HOURS`;
            jobs created after this are flagged `is_new`.
        is_new_col: a SQL `CASE` expression evaluating the `is_new` flag
            per row, added to the unseen-mode `SELECT` list.
        padded_title: a SQL expression producing the job title lowercased,
            hyphens replaced with spaces, and padded with a leading/
            trailing space, so a `LIKE '% keyword %'` match is whole-word.
        visible_job_ids: a `SELECT JobDesignation.job_id` subquery scoped to
            the user's subscribed designations via `UserDesignation` — a job
            is visible if *any* of its `JobDesignation` links matches a
            designation the user follows. Used as a `Job.id.in_(...)`
            filter rather than a direct join, so a job linked to more than
            one designation the user follows still yields exactly one row
            (a join would fan out one row per matching designation).
        stmt: the SQLAlchemy `Select` being built up conditionally in
            either branch before being executed.

    Logic (two independent modes, chosen by whether `status` is falsy):
        Unseen mode (status is None):
          1. Load the user's excluded keywords.
          2. Build a query filtering `Job.id` to `visible_job_ids` (only
             the user's subscribed designations, via `JobDesignation`) with
             an OUTER JOIN to `UserJob` filtered to `UserJob.id IS NULL` —
             i.e. jobs with no status record yet for this user.
          3. Attach the `is_new` CASE column based on `threshold_time`.
          4. For each excluded keyword, AND-in a `NOT LIKE` clause against
             the normalised, padded title so partial-word false positives
             (e.g. "internal" matching "intern") are avoided.
          5. Execute, then merge each `Job`'s dict with its `is_new` flag.
        Status mode (status is given):
          1. Build a query filtering `Job.id` to `visible_job_ids`
             (subscription required here too) joined to `UserJob` filtered
             to this user and this exact `status` — an INNER JOIN, so no
             matching `UserJob` means the job is excluded even if it's
             otherwise visible.
          2. Execute, then merge each `Job`'s dict with `user_job_id`/`user_status`.
    """

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
        visible_job_ids = (
            select(JobDesignation.job_id)
            .join(UserDesignation, JobDesignation.designation_id == UserDesignation.designation_id)
            .where(UserDesignation.user_id == user_id)
        )
        stmt = (
            select(Job, is_new_col)
            .outerjoin(
                UserJob,
                and_(
                    UserJob.job_id == Job.id,
                    UserJob.user_id == user_id,
                ),
            )
            .where(Job.id.in_(visible_job_ids))
            .where(UserJob.id.is_(None))
            .order_by(Job.created_at.desc())
        )

        if excluded_keywords:
            # Replace hyphens with spaces so "front-end" → "front end",
            # then pad with spaces so whole-word LIKE works:
            # " intern " won't match " internal " but will match " intern developer "
            padded_title = func.concat(
                " ",
                func.concat(
                    func.replace(func.lower(Job.title), "-", " "),
                    " ",
                ),
            )

            for keyword in excluded_keywords:
                normalized_keyword = keyword.replace("-", " ").lower().strip()
                stmt = stmt.where(~padded_title.like(f"% {normalized_keyword} %"))

        stmt = stmt.limit(limit).offset(offset)
        results = session.exec(stmt).all()
        results = [{**job.model_dump(), "is_new": is_new} for job, is_new in results]
        return results

    visible_job_ids = (
        select(JobDesignation.job_id)
        .join(UserDesignation, JobDesignation.designation_id == UserDesignation.designation_id)
        .where(UserDesignation.user_id == user_id)
    )
    stmt = (
        select(Job, UserJob.id.label("user_job_id"), UserJob.status.label("user_status"))
        .join(
            UserJob,
            and_(
                UserJob.job_id == Job.id,
                UserJob.user_id == user_id,
                UserJob.status == status,
            ),
        )
        .where(Job.id.in_(visible_job_ids))
        .order_by(Job.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return [
        {**job.model_dump(), "user_job_id": uj_id, "user_status": uj_status}
        for job, uj_id, uj_status in session.exec(stmt).all()
    ]
