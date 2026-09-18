"""Retrieval half of the RAG pipeline: rank jobs by embedding similarity.

Embeddings are stored as JSON-encoded TEXT on `Job.embedding` (see
`app.models.job.Job` and the migration in `app.main`). At this project's
scale (hundreds-to-low-thousands of jobs) a full scan + in-Python cosine
similarity is simple and fast enough — no vector index needed.
"""

import json
import re

from sqlmodel import Session, select

from app.models.job import Job
from app.models.jobdesignation import JobDesignation
from app.models.userdesignation import UserDesignation


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Measure how similar two embedding vectors are in meaning.

    Input: a, b (list[float]) — two equal-length embedding vectors.

    Output: float in [-1, exit1]; 1 means identical direction (same meaning),
        0 means unrelated, -1 means opposite. Returns 0.0 if either vector
        has zero magnitude (degenerate input), to avoid a division by zero.

    Calls: none.
    Called by: `search_jobs()` (this file).

    Variables:
        dot (float): dot product of `a` and `b` — larger when the vectors
            point in a similar direction and have larger magnitudes.
        norm_a, norm_b (float): Euclidean magnitude ("length") of `a`
            and `b` respectively.

    Logic: divide the dot product by the product of the two magnitudes.
        This normalizes away vector length, so the result reflects only
        the angle between the vectors — i.e., meaning, not text length.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _job_matches_excluded_term(job: Job, term: str) -> bool:
    """Whole-word, case-insensitive check for `term` in a job's text fields.

    Input: job (Job), term (str) — a single exclude term, e.g. "remote".
    Output: bool — True if `term` appears as a whole word in the job's
        title, location, or description.
    Calls: `re.search()`.
    Called by: `search_jobs()` (this file).
    Logic: `\\b`-bounded regex so "remote" doesn't false-match inside an
        unrelated longer word, applied to title/location/description
        joined into one lowercased string.
    """
    haystack = f"{job.title} {job.location or ''} {job.description or ''}".lower()
    return re.search(rf"\b{re.escape(term.lower())}\b", haystack) is not None


def search_jobs(
    session: Session,
    user_id: int,
    query_embedding: list[float],
    top_k: int = 5,
    exclude_terms: list[str] | None = None,
) -> list[tuple[Job, float]]:
    """Return the `top_k` jobs most similar in meaning to `query_embedding`.

    Input:
        session (Session): active DB session.
        user_id (int): only jobs under this user's subscribed designations
            are searched — mirrors the `UserDesignation` join used by
            `app.services.jobs.fetch_job_records`, so RAG search respects
            the same access boundary as the normal job feed.
        query_embedding (list[float]): the embedded search query, from
            `app.services.rag.embeddings.embed_text()`.
        top_k (int): how many results to return.
        exclude_terms (list[str] | None): terms a job's title/location/
            description must NOT contain (whole-word match), from
            `app.services.llm.extract_search_filters()`. Embedding
            similarity alone can't honor negation in the query (e.g. "not
            remote" ranks *closer* to remote postings — verified
            empirically), so this is a hard post-filter applied before
            ranking, not something the vector search can express on its own.

    Output: list of (Job, similarity_score) tuples, highest score first,
        at most `top_k` entries. Jobs with no embedding yet (not
        backfilled), or matching any `exclude_terms`, are excluded.

    Calls: `session.exec()` (SQLModel), `_job_matches_excluded_term()`,
        `cosine_similarity()` (both this file).
    Called by: `app.api.v1.job.ask_jobs()`.

    Variables:
        jobs (list[Job]): every job under the user's subscribed
            designations that has a non-null `embedding`, minus any job
            matching an exclude term.
        scored (list[tuple[Job, float]]): `jobs` paired with their
            similarity score against `query_embedding`, before sorting.

    Logic:
        1. Query all `Job` rows whose id is visible to this user via any of
           their subscribed designations (through `JobDesignation` ->
           `UserDesignation`), filtered to rows with a non-null `embedding`.
           A `Job.id.in_(...)` subquery is used rather than a direct join so
           a job linked to more than one designation the user follows isn't
           double-counted (a join would fan out one row per matching
           designation, letting that job occupy two `top_k` slots).
        2. Drop any row matching an `exclude_terms` entry — done before
           scoring so excluded jobs never occupy a `top_k` slot regardless
           of how semantically similar they otherwise are.
        3. Parse each remaining row's JSON-encoded `embedding` back into a
           `list[float]` and score it against `query_embedding`.
        4. Sort by score descending and return the first `top_k`.
    """
    visible_job_ids = (
        select(JobDesignation.job_id)
        .join(UserDesignation, JobDesignation.designation_id == UserDesignation.designation_id)
        .where(UserDesignation.user_id == user_id)
    )
    jobs = session.exec(
        select(Job)
        .where(Job.id.in_(visible_job_ids))
        .where(Job.embedding.is_not(None))
    ).all()

    if exclude_terms:
        jobs = [
            job
            for job in jobs
            if not any(_job_matches_excluded_term(job, term) for term in exclude_terms)
        ]

    scored = [
        (job, cosine_similarity(query_embedding, json.loads(job.embedding)))
        for job in jobs
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
