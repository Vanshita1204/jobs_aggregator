"""Unit tests: individual functions in isolation, not through the HTTP API.

Distinct from the other files in this directory, which exercise full
request/response cycles through FastAPI's TestClient (system/integration
level). These tests call service-layer functions directly, mocking or
constructing only the minimal inputs each function needs.
"""

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
