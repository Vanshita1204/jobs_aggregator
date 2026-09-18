"""Shared pytest fixtures for the API test suite.

Each test gets its own throwaway SQLite file (never the real `jobs.db`),
wired into the app via a `get_session` dependency override. External
services that would otherwise make real network calls (GCS, Playwright,
curl_cffi, LLM providers) are never exercised directly by these tests —
individual test modules monkeypatch the specific functions they need.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("ENV", "test")

from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def engine(tmp_path):
    """A fresh SQLite file per test, with all tables created."""
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    test_engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture()
def client(engine):
    """TestClient wired to the per-test database via a dependency override."""

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register_and_login(client: TestClient, email: str, password: str = "password123", full_name: str = "Test User"):
    """Register a user then log in, returning (user_id, auth_headers)."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert resp.status_code == 200, resp.text
    user_id = resp.json()["id"]

    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers(client):
    """Auth headers for a single freshly-registered user."""
    _, headers = register_and_login(client, "user@example.com")
    return headers


@pytest.fixture()
def designation(client, auth_headers):
    """A designation created by the authenticated test user."""
    resp = client.post(
        "/api/v1/designation",
        json={"title": "Backend Engineer"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture()
def job(engine, designation):
    """A job row inserted directly, as the scraper pipeline would create one.

    There is no API endpoint for inserting a plain scraped job (only
    `POST /jobs/add`, which ingests from a live URL) — this mirrors what
    `app.services.jobs.create_job_records` does after a real scrape,
    including its `JobDesignation` link (feed visibility joins through that
    table, not `Job.designation_id`, directly — see `app.services.jobs`).
    """
    from app.models.job import Job
    from app.models.jobdesignation import JobDesignation

    with Session(engine) as session:
        row = Job(
            title="Senior Backend Engineer",
            company="Acme Corp",
            location="Bengaluru",
            description="",
            source="indeed",
            source_url="https://in.indeed.com/viewjob?jk=abc123",
            designation_id=designation["id"],
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        row_data = row.model_dump()  # capture before the next commit expires `row`

        session.add(JobDesignation(job_id=row.id, designation_id=designation["id"]))
        session.commit()
        return row_data
