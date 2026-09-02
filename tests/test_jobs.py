"""Tests for GET /jobs, POST /jobs/fetch-new, POST /jobs/add, GET /jobs/{id}/description."""

from sqlmodel import Session

from app.models.job import Job


def subscribe(client, headers, designation_id):
    resp = client.post("/api/v1/user-designation", json={"designation_id": designation_id}, headers=headers)
    assert resp.status_code == 200, resp.text


def test_unseen_feed_requires_subscription(client, auth_headers, job):
    """Jobs under a designation the user never subscribed to must not appear."""
    resp = client.get("/api/v1/jobs", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_unseen_feed_returns_subscribed_jobs(client, auth_headers, designation, job):
    subscribe(client, auth_headers, designation["id"])
    resp = client.get("/api/v1/jobs", headers=auth_headers)
    assert resp.status_code == 200
    titles = [j["title"] for j in resp.json()]
    assert job["title"] in titles


def test_actioned_jobs_are_excluded_from_unseen_feed(client, auth_headers, designation, job):
    subscribe(client, auth_headers, designation["id"])
    client.post("/api/v1/user-jobs", json={"job_id": job["id"], "status": "saved"}, headers=auth_headers)

    resp = client.get("/api/v1/jobs", headers=auth_headers)
    titles = [j["title"] for j in resp.json()]
    assert job["title"] not in titles


def test_status_filtered_feed_returns_actioned_job(client, auth_headers, designation, job):
    subscribe(client, auth_headers, designation["id"])
    client.post("/api/v1/user-jobs", json={"job_id": job["id"], "status": "applied"}, headers=auth_headers)

    resp = client.get("/api/v1/jobs?status=applied", headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["user_status"] == "applied"
    assert results[0]["user_job_id"] is not None

    resp = client.get("/api/v1/jobs?status=saved", headers=auth_headers)
    assert resp.json() == []


def test_excluded_keyword_hides_matching_titles(client, auth_headers, designation, engine):
    subscribe(client, auth_headers, designation["id"])
    with Session(engine) as session:
        session.add(
            Job(
                title="Backend Intern",
                company="Acme",
                location="Remote",
                description="",
                source="indeed",
                source_url="https://in.indeed.com/viewjob?jk=intern1",
                designation_id=designation["id"],
            )
        )
        session.add(
            Job(
                title="Backend Engineer",
                company="Acme",
                location="Remote",
                description="",
                source="indeed",
                source_url="https://in.indeed.com/viewjob?jk=eng1",
                designation_id=designation["id"],
            )
        )
        session.commit()

    client.post(
        "/api/v1/user-job-preferences",
        json={"keyword": "intern", "is_excluded": True},
        headers=auth_headers,
    )

    resp = client.get("/api/v1/jobs", headers=auth_headers)
    titles = [j["title"] for j in resp.json()]
    assert "Backend Engineer" in titles
    assert "Backend Intern" not in titles


def test_fetch_new_dispatches_celery_task_per_designation(client, auth_headers, designation, monkeypatch):
    subscribe(client, auth_headers, designation["id"])

    calls = []
    from app.api.v1 import job as job_module

    monkeypatch.setattr(
        job_module.job_fetching_task_designation,
        "delay",
        lambda designation_id: calls.append(designation_id),
    )

    resp = client.post("/api/v1/jobs/fetch-new", headers=auth_headers)
    assert resp.status_code == 200
    assert calls == [designation["id"]]


def test_add_job_manually_creates_external_job(client, auth_headers, designation, monkeypatch):
    from app.api.v1 import job as job_module

    monkeypatch.setattr(
        job_module,
        "ingest_job_from_url",
        lambda url, provider, api_key: {
            "title": "Staff Engineer",
            "company": "Beta Inc",
            "location": "Remote",
            "description": "Great role.",
            "source": "Beta",
            "source_url": url,
        },
    )

    resp = client.post(
        "/api/v1/jobs/add",
        json={"url": "https://beta.example.com/jobs/1", "designation_id": designation["id"], "status": "saved"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_external"] is True
    assert body["is_new"] is True
    assert body["user_status"] == "saved"
    assert body["user_job_id"] is not None


def test_add_job_manually_returns_existing_on_duplicate_url(client, auth_headers, designation, monkeypatch):
    from app.api.v1 import job as job_module

    call_count = {"n": 0}

    def fake_ingest(url, provider, api_key):
        call_count["n"] += 1
        return {
            "title": "Staff Engineer",
            "company": "Beta Inc",
            "location": "Remote",
            "description": "",
            "source": "Beta",
            "source_url": url,
        }

    monkeypatch.setattr(job_module, "ingest_job_from_url", fake_ingest)

    payload = {"url": "https://beta.example.com/jobs/2", "designation_id": designation["id"]}
    first = client.post("/api/v1/jobs/add", json=payload, headers=auth_headers)
    assert first.json()["is_new"] is True

    second = client.post("/api/v1/jobs/add", json=payload, headers=auth_headers)
    assert second.status_code == 200
    assert second.json()["is_new"] is False
    assert call_count["n"] == 1  # second call short-circuits before hitting the LLM/scraper


def test_add_job_manually_rejects_untitled_extraction(client, auth_headers, designation, monkeypatch):
    from app.api.v1 import job as job_module

    monkeypatch.setattr(
        job_module,
        "ingest_job_from_url",
        lambda url, provider, api_key: {"title": "", "company": "", "location": "", "description": "", "source": "X", "source_url": url},
    )

    resp = client.post(
        "/api/v1/jobs/add",
        json={"url": "https://x.example.com/jobs/3", "designation_id": designation["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_job_description_is_fetched_and_cached(client, auth_headers, job, monkeypatch):
    from app.api.v1 import job as job_module

    calls = []

    def fake_fetch(source, source_url):
        calls.append((source, source_url))
        return "Full job description text."

    monkeypatch.setattr(job_module, "fetch_job_description", fake_fetch)

    resp = client.get(f"/api/v1/jobs/{job['id']}/description", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Full job description text."
    assert len(calls) == 1

    # Second call must be served from the DB — no second fetch.
    resp = client.get(f"/api/v1/jobs/{job['id']}/description", headers=auth_headers)
    assert resp.json()["description"] == "Full job description text."
    assert len(calls) == 1


def test_job_description_404_for_unknown_job(client, auth_headers):
    resp = client.get("/api/v1/jobs/999999/description", headers=auth_headers)
    assert resp.status_code == 404
