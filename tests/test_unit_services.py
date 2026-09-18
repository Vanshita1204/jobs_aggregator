"""Unit tests: individual functions in isolation, not through the HTTP API.

Distinct from the other files in this directory, which exercise full
request/response cycles through FastAPI's TestClient (system/integration
level). These tests call service-layer functions directly, mocking or
constructing only the minimal inputs each function needs.
"""

import json

from sqlmodel import Session, SQLModel, create_engine

from app.core.auth import create_access_token, hash_password, verify_password
from app.models.designation import Designation
from app.models.job import Job
from app.services.external_ingestion import _extract_jk, detect_source
from app.services.jobs import create_job_records


def test_hash_password_produces_a_verifiable_but_different_string():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("right-password")
    assert not verify_password("wrong-password", hashed)


def test_create_access_token_encodes_the_user_id_as_subject():
    from jose import jwt

    from app.core.config import settings

    token = create_access_token(42)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == "42"
    assert "exp" in payload


def test_detect_source_matches_each_supported_portal():
    assert detect_source("https://in.indeed.com/viewjob?jk=abc123") == "indeed"
    assert detect_source("https://www.linkedin.com/jobs/view/123456") == "linkedin"
    assert detect_source("https://www.hirist.tech/j/some-job-title-123") == "hirist"


def test_detect_source_returns_none_for_unsupported_portal():
    assert detect_source("https://www.naukri.com/job-listings-backend-engineer") is None


def test_extract_jk_pulls_id_from_query_string():
    assert _extract_jk("https://in.indeed.com/viewjob?jk=abc123") == "abc123"
    assert _extract_jk("https://in.indeed.com/rc/clk?jk=xyz789&other=1") == "xyz789"


def test_extract_jk_returns_none_when_absent():
    assert _extract_jk("https://in.indeed.com/jobs?q=backend") is None


def _make_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


def test_create_job_records_deduplicates_within_one_batch(monkeypatch):
    """Two scraped dicts with the same source_url in one call must yield one row."""
    engine = _make_engine()
    monkeypatch.setattr("app.services.jobs.engine", engine)

    with Session(engine) as session:
        designation = Designation(title="Backend Engineer")
        session.add(designation)
        session.commit()
        session.refresh(designation)
        designation_id = designation.id

    jobs = [
        {"title": "Engineer", "company": "Acme", "location": "Remote",
         "description": "", "source": "Indeed", "source_url": "https://x/1"},
        {"title": "Engineer (dup)", "company": "Acme", "location": "Remote",
         "description": "", "source": "Indeed", "source_url": "https://x/1"},
    ]
    create_job_records(jobs, designation_id)

    with Session(engine) as session:
        from sqlmodel import select
        rows = session.exec(select(Job).where(Job.source_url == "https://x/1")).all()
        assert len(rows) == 1
        assert rows[0].title == "Engineer"  # first occurrence wins, not the duplicate


def test_create_job_records_skips_urls_already_in_db(monkeypatch):
    """A source_url already persisted must not be re-inserted on a later call."""
    engine = _make_engine()
    monkeypatch.setattr("app.services.jobs.engine", engine)

    with Session(engine) as session:
        designation = Designation(title="Data Engineer")
        session.add(designation)
        session.commit()
        session.refresh(designation)
        designation_id = designation.id

    create_job_records(
        [{"title": "First", "company": "Acme", "location": "Remote",
          "description": "", "source": "Indeed", "source_url": "https://x/2"}],
        designation_id,
    )
    create_job_records(
        [{"title": "Second (should be ignored)", "company": "Acme", "location": "Remote",
          "description": "", "source": "Indeed", "source_url": "https://x/2"}],
        designation_id,
    )

    with Session(engine) as session:
        from sqlmodel import select
        rows = session.exec(select(Job).where(Job.source_url == "https://x/2")).all()
        assert len(rows) == 1
        assert rows[0].title == "First"


def test_create_job_records_links_existing_job_to_a_second_designation(monkeypatch):
    """The actual duplicate-row fix: the same posting matching a second
    designation's search must link the existing Job via JobDesignation
    instead of silently no-op'ing (the old behavior — which meant a
    second, separately-tracking-URL'd row was the only way to make it
    visible under that designation)."""
    from sqlmodel import select

    from app.models.jobdesignation import JobDesignation

    engine = _make_engine()
    monkeypatch.setattr("app.services.jobs.engine", engine)

    with Session(engine) as session:
        d1 = Designation(title="Software Engineer")
        d2 = Designation(title="Software Developer")
        session.add_all([d1, d2])
        session.commit()
        session.refresh(d1)
        session.refresh(d2)
        d1_id, d2_id = d1.id, d2.id

    job_dict = {"title": "Backend role", "company": "Acme", "location": "Remote",
                "description": "", "source": "LinkedIn", "source_url": "https://x/shared"}

    create_job_records([job_dict], d1_id)
    create_job_records([job_dict], d2_id)  # same posting, different designation

    with Session(engine) as session:
        rows = session.exec(select(Job).where(Job.source_url == "https://x/shared")).all()
        assert len(rows) == 1  # still exactly one Job row, not two

        links = session.exec(
            select(JobDesignation.designation_id).where(JobDesignation.job_id == rows[0].id)
        ).all()
        assert set(links) == {d1_id, d2_id}  # linked to both designations


def test_create_job_records_same_designation_twice_does_not_duplicate_link(monkeypatch):
    """Re-scraping the same posting under the same designation it's already
    linked to must stay idempotent (no duplicate JobDesignation row, which
    would violate its UNIQUE constraint)."""
    from sqlmodel import select

    from app.models.jobdesignation import JobDesignation

    engine = _make_engine()
    monkeypatch.setattr("app.services.jobs.engine", engine)

    with Session(engine) as session:
        designation = Designation(title="Backend Engineer")
        session.add(designation)
        session.commit()
        session.refresh(designation)
        designation_id = designation.id

    job_dict = {"title": "Backend role", "company": "Acme", "location": "Remote",
                "description": "", "source": "LinkedIn", "source_url": "https://x/repeat"}

    create_job_records([job_dict], designation_id)
    create_job_records([job_dict], designation_id)  # same posting, same designation, again

    with Session(engine) as session:
        job = session.exec(select(Job).where(Job.source_url == "https://x/repeat")).one()
        links = session.exec(
            select(JobDesignation).where(JobDesignation.job_id == job.id)
        ).all()
        assert len(links) == 1


def test_create_job_records_skips_entries_with_no_source_url():
    engine = _make_engine()
    import app.services.jobs as jobs_module
    jobs_module.engine = engine

    create_job_records(
        [{"title": "No URL", "company": "Acme", "location": "Remote",
          "description": "", "source": "Indeed", "source_url": None}],
        1,
    )
    with Session(engine) as session:
        from sqlmodel import select
        assert session.exec(select(Job)).all() == []


def test_backfill_job_descriptions_task_fills_empty_descriptions_and_reembeds(monkeypatch):
    """A job with no description gets one fetched, persisted, and re-embedded;
    a job that already has one is left untouched (no redundant fetch)."""
    from sqlmodel import select

    from app.services.tasks import backfill_job_descriptions_task

    engine = _make_engine()
    monkeypatch.setattr("app.services.tasks.engine", engine)

    with Session(engine) as session:
        designation = Designation(title="Backend Engineer")
        session.add(designation)
        session.commit()
        session.refresh(designation)

        empty = Job(
            title="Engineer", company="Acme", location="Remote", description="",
            source="indeed", source_url="https://x/empty", designation_id=designation.id,
        )
        already_has_one = Job(
            title="Manager", company="Acme", location="Remote", description="Already fetched.",
            source="indeed", source_url="https://x/filled", designation_id=designation.id,
        )
        session.add_all([empty, already_has_one])
        session.commit()

    calls = []

    def fake_fetch(source, source_url):
        calls.append(source_url)
        return "Fetched description text."

    monkeypatch.setattr("app.services.tasks.fetch_job_description", fake_fetch)
    monkeypatch.setattr("app.services.tasks.embed_text", lambda text: [1.0, 0.0])

    backfill_job_descriptions_task()

    assert calls == ["https://x/empty"]  # the already-filled job was never re-fetched

    with Session(engine) as session:
        empty_row = session.exec(select(Job).where(Job.source_url == "https://x/empty")).one()
        assert empty_row.description == "Fetched description text."
        assert empty_row.embedding == json.dumps([1.0, 0.0])

        filled_row = session.exec(select(Job).where(Job.source_url == "https://x/filled")).one()
        assert filled_row.description == "Already fetched."
        assert filled_row.embedding is None  # untouched — it was never a candidate


def test_backfill_job_descriptions_task_caps_per_run_oldest_first(monkeypatch):
    """A backlog larger than the daily cap only processes the oldest rows;
    the rest are left for the next day's run instead of one long batch."""
    from datetime import datetime, timedelta

    from sqlmodel import select

    from app.services.tasks import backfill_job_descriptions_task

    engine = _make_engine()
    monkeypatch.setattr("app.services.tasks.engine", engine)
    monkeypatch.setattr("app.core.config.settings.DESCRIPTION_BACKFILL_DAILY_LIMIT", 2)

    with Session(engine) as session:
        designation = Designation(title="Backend Engineer")
        session.add(designation)
        session.commit()
        session.refresh(designation)

        base_time = datetime.now()
        for i in range(4):
            session.add(Job(
                title=f"Engineer {i}", company="Acme", location="Remote", description="",
                source="indeed", source_url=f"https://x/job{i}", designation_id=designation.id,
                created_at=base_time - timedelta(days=4 - i),  # job0 oldest, job3 newest
            ))
        session.commit()

    calls = []
    monkeypatch.setattr(
        "app.services.tasks.fetch_job_description",
        lambda source, source_url: calls.append(source_url) or "Fetched.",
    )
    monkeypatch.setattr("app.services.tasks.embed_text", lambda text: [1.0, 0.0])

    backfill_job_descriptions_task()

    assert calls == ["https://x/job0", "https://x/job1"]  # only the 2 oldest, capped

    with Session(engine) as session:
        untouched = session.exec(select(Job).where(Job.source_url == "https://x/job3")).one()
        assert untouched.description == ""


def test_backfill_job_descriptions_task_limit_override_ignores_daily_cap(monkeypatch):
    """An explicit `limit` argument (used for a one-off catch-up run) takes
    priority over `settings.DESCRIPTION_BACKFILL_DAILY_LIMIT`."""
    from sqlmodel import select

    from app.services.tasks import backfill_job_descriptions_task

    engine = _make_engine()
    monkeypatch.setattr("app.services.tasks.engine", engine)
    monkeypatch.setattr("app.core.config.settings.DESCRIPTION_BACKFILL_DAILY_LIMIT", 1)

    with Session(engine) as session:
        designation = Designation(title="Backend Engineer")
        session.add(designation)
        session.commit()
        session.refresh(designation)

        for i in range(3):
            session.add(Job(
                title=f"Engineer {i}", company="Acme", location="Remote", description="",
                source="indeed", source_url=f"https://x/override{i}", designation_id=designation.id,
            ))
        session.commit()

    calls = []
    monkeypatch.setattr(
        "app.services.tasks.fetch_job_description",
        lambda source, source_url: calls.append(source_url) or "Fetched.",
    )
    monkeypatch.setattr("app.services.tasks.embed_text", lambda text: [1.0, 0.0])

    backfill_job_descriptions_task(limit=10)  # larger than both the cap and the backlog

    assert len(calls) == 3  # all 3, not capped at the daily limit of 1


def test_backfill_job_descriptions_task_leaves_row_unfetched_on_failed_fetch(monkeypatch):
    """A source fetch that returns "" (failure) must not overwrite the row,
    so it's retried on the next day's run instead of being marked as done."""
    from sqlmodel import select

    from app.services.tasks import backfill_job_descriptions_task

    engine = _make_engine()
    monkeypatch.setattr("app.services.tasks.engine", engine)

    with Session(engine) as session:
        designation = Designation(title="Backend Engineer")
        session.add(designation)
        session.commit()
        session.refresh(designation)

        session.add(Job(
            title="Engineer", company="Acme", location="Remote", description="",
            source="linkedin", source_url="https://x/blocked", designation_id=designation.id,
        ))
        session.commit()

    monkeypatch.setattr("app.services.tasks.fetch_job_description", lambda source, source_url: "")

    backfill_job_descriptions_task()

    with Session(engine) as session:
        row = session.exec(select(Job).where(Job.source_url == "https://x/blocked")).one()
        assert row.description == ""
        assert row.embedding is None
