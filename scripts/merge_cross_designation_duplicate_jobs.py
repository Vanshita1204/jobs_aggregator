"""One-off script: collapse duplicate Job rows created before Job<->Designation
became many-to-many.

Before `app.models.jobdesignation.JobDesignation` existed, the only way to
make a posting visible under a second designation search was to store it as
a second `Job` row (since `Job.designation_id` was a single FK) — so the
same real posting matching several designations (e.g. "software engineer"
and "software developer" both matching one LinkedIn job) ended up as
several rows. `app.services.jobs.create_job_records()` and
`app.api.v1.job.add_job_manually()` now link an already-existing posting to
a new designation instead of duplicating it, so this backlog won't grow
further — this script cleans up what's already there.

Usage (from the project root, with the venv active, and after starting the
app at least once so the `JobDesignation` table exists):
    python -m scripts.merge_cross_designation_duplicate_jobs
"""

from collections import defaultdict
from urllib.parse import urlsplit

from sqlmodel import Session, select

from app.db.session import engine
from app.models.cv import UserCV
from app.models.job import Job
from app.models.jobdesignation import JobDesignation
from app.models.userjob import UserJob
from app.services.external_ingestion import _extract_jk


def _canonical_key(source: str, url: str):
    """Group jobs by underlying posting, independent of per-scrape tracking
    noise in the URL — same logic used by the parser fix in
    `app.services.parsers` (Indeed: `jk` query param; LinkedIn/Hirist: the
    URL path, query string stripped)."""
    source = (source or "").lower()
    if source == "indeed":
        jk = _extract_jk(url)
        return ("indeed", jk) if jk else ("indeed", url)
    if source in ("linkedin", "hirist"):
        return (source, urlsplit(url)._replace(query="", fragment="").geturl())
    return (source, url)


def merge_cross_designation_duplicate_jobs():
    """Collapse each group of duplicate Job rows into one, preserving every
    designation link, UserJob, and UserCV involved.

    Input: none — reads/writes the DB configured via
        `app.core.config.settings.DATABASE_URL`.

    Output: None. Prints counts of jobs removed, designation links added,
        and UserJob rows repointed/merged.

    Calls: `_canonical_key()` (this file), `app.services.external_ingestion._extract_jk()`.
    Called by: run directly as a script, not imported elsewhere.

    Variables:
        groups (dict[tuple, list[Job]]): every `Job` row grouped by
            `_canonical_key()`.
        dup_groups (list[list[Job]]): groups with more than one row — the
            actual duplicates to collapse.
        winner (Job): the row kept per group — prefers one with a non-empty
            `description` (more complete data), tie-broken by oldest
            `created_at` (same rule used for the earlier same-designation
            cleanup, for consistency).
        losers (list[Job]): every other row in the group, to be merged into
            `winner` and deleted.

    Logic, per duplicate group:
        1. Pick `winner` (see above).
        2. For each loser: copy any `JobDesignation` link it has onto
           `winner` (skip if `winner` already has that link) — this is the
           actual visibility fix, since a loser's designation is otherwise
           lost when it's deleted.
        3. For each `UserJob` pointing at the loser: if `winner` already has
           a `UserJob` for that same user, move any `UserCV` off the
           loser's `UserJob` onto the existing one, then drop the loser's
           `UserJob`; otherwise just repoint it at `winner` in place.
        4. Delete the loser `Job` row.
        Each loser is committed in its own transaction (mirroring the
        earlier same-designation cleanup) so one bad row can't roll back
        progress already made on the rest of the run.
    """
    removed_jobs = 0
    designation_links_added = 0
    reassigned_userjobs = 0
    merged_userjobs = 0
    reassigned_usercvs = 0

    with Session(engine) as session:
        jobs = session.exec(select(Job)).all()
        groups = defaultdict(list)
        for job in jobs:
            groups[_canonical_key(job.source, job.source_url)].append(job)

        dup_groups = [group for group in groups.values() if len(group) > 1]
        print(f"{len(dup_groups)} duplicate group(s) found ({sum(len(g) for g in dup_groups)} rows involved).")

        for group in dup_groups:
            group_sorted = sorted(group, key=lambda j: (j.description == "", j.created_at))
            winner = group_sorted[0]
            losers = group_sorted[1:]

            for loser in losers:
                loser_designations = session.exec(
                    select(JobDesignation).where(JobDesignation.job_id == loser.id)
                ).all()
                for ld in loser_designations:
                    already_on_winner = session.exec(
                        select(JobDesignation).where(
                            JobDesignation.job_id == winner.id,
                            JobDesignation.designation_id == ld.designation_id,
                        )
                    ).first()
                    if already_on_winner:
                        session.delete(ld)
                    else:
                        ld.job_id = winner.id
                        session.add(ld)
                        designation_links_added += 1

                loser_userjobs = session.exec(select(UserJob).where(UserJob.job_id == loser.id)).all()
                for uj in loser_userjobs:
                    existing_winner_uj = session.exec(
                        select(UserJob).where(UserJob.job_id == winner.id, UserJob.user_id == uj.user_id)
                    ).first()
                    if existing_winner_uj:
                        cvs = session.exec(select(UserCV).where(UserCV.user_job_id == uj.id)).all()
                        for cv in cvs:
                            cv.user_job_id = existing_winner_uj.id
                            session.add(cv)
                            reassigned_usercvs += 1
                        session.delete(uj)
                        merged_userjobs += 1
                    else:
                        uj.job_id = winner.id
                        session.add(uj)
                        reassigned_userjobs += 1
                session.commit()

                session.delete(loser)
                session.commit()
                removed_jobs += 1

    print(f"removed duplicate jobs: {removed_jobs}")
    print(f"designation links added to winners: {designation_links_added}")
    print(f"userjobs repointed to winner: {reassigned_userjobs}")
    print(f"userjobs merged/deleted (winner already had one): {merged_userjobs}")
    print(f"usercvs reassigned during merge: {reassigned_usercvs}")
    print("Done.")


if __name__ == "__main__":
    merge_cross_designation_duplicate_jobs()
