"""One-off script: compute embeddings for Job rows that predate the RAG feature.

Every job inserted going forward gets its embedding computed at insert
time (see `app.services.jobs.create_job_records` and
`app.api.v1.job.add_job_manually`). This script only needs to run once,
against the existing `jobs.db`, to backfill rows created before that code
existed.

Usage (from the project root, with the venv active):
    python -m scripts.backfill_embeddings
"""

import json

from sqlmodel import Session, select

from app.db.session import engine
from app.models.job import Job
from app.services.rag.embeddings import embed_batch, job_embedding_text

BATCH_SIZE = 32


def backfill_embeddings():
    """Compute and persist embeddings for every Job row missing one.

    Input: none — reads directly from the DB configured via
        `app.core.config.settings.DATABASE_URL`.

    Output: None. Prints a running count of rows processed; commits each
        batch to the database as it goes.

    Calls: `app.services.rag.embeddings.embed_batch()`, `job_embedding_text()`.
    Called by: run directly as a script (`python -m scripts.backfill_embeddings`),
        not imported elsewhere.

    Variables:
        pending (list[Job]): all rows with `embedding IS NULL`, fetched once
            up front.
        batch (list[Job]): a `BATCH_SIZE`-sized slice of `pending`, embedded
            and committed together so one bad row can't force re-embedding
            everything already done.

    Logic:
        1. Fetch every `Job` row where `embedding` is null.
        2. Process them in fixed-size batches: build each row's embedding
           text, embed the whole batch in one `embed_batch()` call, assign
           the JSON-encoded vector back onto each row, and commit.
        3. Print progress after each batch so a long backfill is observable.
    """
    with Session(engine) as session:
        pending = session.exec(select(Job).where(Job.embedding.is_(None))).all()
        print(f"{len(pending)} job(s) missing an embedding.")

        for start in range(0, len(pending), BATCH_SIZE):
            batch = pending[start : start + BATCH_SIZE]
            texts = [job_embedding_text(job.title, job.company, job.location, job.description) for job in batch]
            vectors = embed_batch(texts)

            for job, vector in zip(batch, vectors):
                job.embedding = json.dumps(vector)
                session.add(job)

            session.commit()
            print(f"  embedded {min(start + BATCH_SIZE, len(pending))}/{len(pending)}")

    print("Done.")


if __name__ == "__main__":
    backfill_embeddings()
