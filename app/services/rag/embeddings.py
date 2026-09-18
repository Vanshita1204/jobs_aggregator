"""Local text embeddings for the RAG pipeline.

Uses `sentence-transformers` (default model: all-MiniLM-L6-v2, 384-dim,
runs on CPU) so semantic search works with no external API key. The model
is loaded lazily on first use and cached in `_model`, matching the
local-import-per-call idiom already used for LLM providers in
`app.services.llm` — a ~90MB model load is too slow to pay on every
`app.main` import, but should only happen once per process.
"""


from sqlalchemy import event

from app.core.config import settings
from app.core.logging import get_logger
from app.models.job import Job

logger = get_logger(__name__)

_model = None


@event.listens_for(Job, "before_insert")
def _warn_if_embedding_missing(_mapper, _connection, target: Job) -> None:
    """Safety net: flag any Job insert that skipped computing an embedding.

    Both current insert paths (`app.services.jobs.create_job_records()` and
    `app.api.v1.job.add_job_manually()`) already set `Job.embedding` before
    `session.add()`, so this is a no-op for them. It exists so a *future*
    insert path that forgets to call `embed_text()`/`embed_batch()` fails
    loudly (a log line) instead of silently producing a row invisible to
    `search_jobs()`/`POST /jobs/ask`. Deliberately does NOT compute the
    embedding itself here — doing real model inference inside a DB flush
    hook would add real latency/model-load cost to any code path (tests
    included) that constructs a `Job` without an embedding on purpose.
    """
    if target.embedding is None:
        logger.warning(
            "Job inserted without an embedding (title=%r, source_url=%r) — "
            "it will not be findable via POST /jobs/ask until backfilled",
            target.title,
            target.source_url,
        )


def _get_model():
    """Load (once) and return the shared sentence-transformers model instance.

    Input: none.

    Output: a `SentenceTransformer` instance, cached in the module-level
        `_model` global so the (slow, one-time) model load only happens
        once per process.

    Calls: `sentence_transformers.SentenceTransformer()` (external
        library), imported locally so importing this module does not by
        itself trigger the heavy `sentence_transformers`/`torch` import.
    Called by: `embed_text()`, `embed_batch()` (both in this file).

    Variables:
        _model (SentenceTransformer | None): module-level cache; `None`
            until the first call, non-`None` on every call after.

    Logic: if `_model` has not been set yet, construct it from
        `settings.EMBEDDING_MODEL` and store it in the global; otherwise
        return the already-loaded instance unchanged.
    """
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single string into a fixed-length semantic vector.

    Input: text (str) — arbitrary text, e.g. a search query or a job's
        title/company/location/description concatenated together.

    Output: list[float] — 384 numbers (for the default model) representing
        the text's meaning; texts with similar meaning produce vectors
        that are close together under cosine similarity.

    Calls: `_get_model()` (this file), then the model's `.encode()` method.
    Called by: `app.api.v1.job.ask_jobs()` (embeds the user's query);
        `app.services.jobs.create_job_records()` and
        `app.api.v1.job.add_job_manually()` use `embed_batch()` instead
        for their (possibly multi-row) inserts.

    Logic: forward `text` to the shared model's `.encode()` and convert the
        resulting numpy array to a plain Python list (so it is JSON- and
        SQLite-TEXT-serializable).
    """
    return _get_model().encode(text).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed many strings in a single model call (far faster than looping).

    Input: texts (list[str]) — e.g. the embedding-source text for every
        newly-scraped job in one batch.

    Output: list[list[float]], one vector per input string, same order as
        `texts`. Empty list in, empty list out (no model call made).

    Calls: `_get_model()` (this file), then the model's `.encode()` method.
    Called by: `app.services.jobs.create_job_records()` (embeds a whole
        scrape batch in one call); `scripts/backfill_embeddings.py`.

    Logic: guard against an empty `texts` list (encoding nothing would
        still cost a model load), otherwise forward the whole list to
        `.encode()` in one call and convert the result to plain lists.
    """
    if not texts:
        return []
    return _get_model().encode(texts).tolist()


def job_embedding_text(title: str, company: str, location: str | None, description: str) -> str:
    """Build the canonical text a Job's embedding is computed from.

    Input:
        title (str), company (str): job identifying fields.
        location (str | None): job location; falls back to a fixed phrase
            when absent so its absence doesn't shrink the embedded text.
        description (str): full job description, may be empty for
            not-yet-fetched listings.

    Output: str — a single string combining all four fields, suitable for
        `embed_text()`/`embed_batch()`.

    Calls: none.
    Called by: `app.services.jobs.create_job_records()` and
        `app.api.v1.job.add_job_manually()` — used identically at both job
        insert points so a job's embedding always reflects the same
        fields regardless of which ingestion path created it.

    Logic: string-interpolate the four fields into one fixed template.
    """
    return f"{title} at {company} in {location or 'unspecified location'}. {description}"
