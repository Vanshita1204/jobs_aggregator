"""Tests for the CV endpoints: upload-url, create, list, download, delete, tips.

GCS, text extraction, and the LLM are always mocked here — none of these
tests make real network calls to Google Cloud Storage or an LLM provider.
"""

from app.api.v1 import cv as cv_module


def test_upload_url_rejects_unsupported_extension(client, auth_headers):
    resp = client.get("/api/v1/cvs/upload-url?filename=resume.exe", headers=auth_headers)
    assert resp.status_code == 400


def test_upload_url_returns_signed_url_for_pdf(client, auth_headers, monkeypatch):
    monkeypatch.setattr(cv_module, "generate_upload_url", lambda gcs_path, content_type: f"https://signed.example/{gcs_path}")

    resp = client.get("/api/v1/cvs/upload-url?filename=resume.pdf", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["gcs_path"].startswith("cvs/user_")
    assert body["gcs_path"].endswith(".pdf")
    assert body["upload_url"] == f"https://signed.example/{body['gcs_path']}"


def _mock_storage(monkeypatch, extracted_text="Experienced backend engineer."):
    monkeypatch.setattr(cv_module, "download_bytes", lambda gcs_path: b"%PDF-fake-bytes%")
    monkeypatch.setattr(cv_module, "extract_text", lambda file_bytes, filename: extracted_text)


def test_create_cv_registers_record_with_extracted_text(client, auth_headers, monkeypatch):
    _mock_storage(monkeypatch)

    resp = client.post(
        "/api/v1/cvs",
        json={"name": "My Resume", "gcs_path": "cvs/user_1/abc.pdf"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "My Resume"
    assert body["gcs_path"] == "cvs/user_1/abc.pdf"
    assert "extracted_text" not in body  # UserCVRead does not expose raw CV text


def test_create_cv_rejects_unsupported_extension(client, auth_headers):
    resp = client.post(
        "/api/v1/cvs",
        json={"name": "My Resume", "gcs_path": "cvs/user_1/abc.exe"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_create_cv_502_when_gcs_download_fails(client, auth_headers, monkeypatch):
    def boom(gcs_path):
        raise RuntimeError("bucket unreachable")

    monkeypatch.setattr(cv_module, "download_bytes", boom)

    resp = client.post(
        "/api/v1/cvs",
        json={"name": "My Resume", "gcs_path": "cvs/user_1/abc.pdf"},
        headers=auth_headers,
    )
    assert resp.status_code == 502


def test_list_cvs_includes_linked_job_title(client, auth_headers, monkeypatch, job):
    _mock_storage(monkeypatch)

    # The status-filtered job feed joins through UserDesignation, so the
    # user must be subscribed to the job's designation for it to show up
    # under a status tab even though POST /user-jobs itself has no such check.
    client.post("/api/v1/user-designation", json={"designation_id": job["designation_id"]}, headers=auth_headers)
    client.post("/api/v1/user-jobs", json={"job_id": job["id"], "status": "applied"}, headers=auth_headers)
    user_jobs = client.get("/api/v1/jobs?status=applied", headers=auth_headers).json()
    user_job_id = user_jobs[0]["user_job_id"]

    client.post(
        "/api/v1/cvs",
        json={"name": "Tailored Resume", "gcs_path": "cvs/user_1/tailored.pdf", "user_job_id": user_job_id},
        headers=auth_headers,
    )

    resp = client.get("/api/v1/cvs", headers=auth_headers)
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["job_title"] == job["title"]
    assert rows[0]["job_company"] == job["company"]


def test_download_cv_returns_signed_url(client, auth_headers, monkeypatch):
    _mock_storage(monkeypatch)
    created = client.post(
        "/api/v1/cvs",
        json={"name": "My Resume", "gcs_path": "cvs/user_1/abc.pdf"},
        headers=auth_headers,
    ).json()

    monkeypatch.setattr(cv_module, "generate_download_url", lambda gcs_path: f"https://signed.example/{gcs_path}")

    resp = client.get(f"/api/v1/cvs/{created['id']}/download", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"download_url": "https://signed.example/cvs/user_1/abc.pdf"}


def test_download_cv_404_for_other_users_cv(client, auth_headers, monkeypatch):
    from tests.conftest import register_and_login

    _mock_storage(monkeypatch)
    created = client.post(
        "/api/v1/cvs",
        json={"name": "My Resume", "gcs_path": "cvs/user_1/abc.pdf"},
        headers=auth_headers,
    ).json()

    _, other_headers = register_and_login(client, "other@example.com")
    resp = client.get(f"/api/v1/cvs/{created['id']}/download", headers=other_headers)
    assert resp.status_code == 404


def test_delete_cv_removes_record(client, auth_headers, monkeypatch):
    _mock_storage(monkeypatch)
    monkeypatch.setattr(cv_module, "delete_file", lambda gcs_path: None)

    created = client.post(
        "/api/v1/cvs",
        json={"name": "My Resume", "gcs_path": "cvs/user_1/abc.pdf"},
        headers=auth_headers,
    ).json()

    resp = client.delete(f"/api/v1/cvs/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200

    resp = client.get("/api/v1/cvs", headers=auth_headers)
    assert resp.json() == []


def test_cv_tips_returns_llm_output(client, auth_headers, monkeypatch, job):
    _mock_storage(monkeypatch, extracted_text="5 years of Python experience.")
    created = client.post(
        "/api/v1/cvs",
        json={"name": "My Resume", "gcs_path": "cvs/user_1/abc.pdf"},
        headers=auth_headers,
    ).json()

    monkeypatch.setattr(
        cv_module,
        "get_cv_tips",
        lambda job_title, company, location, description, cv_text, provider, api_key: "1. Do X.\n2. Do Y.",
    )

    resp = client.post(f"/api/v1/cvs/{created['id']}/tips/{job['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["tips"] == "1. Do X.\n2. Do Y."


def test_cv_tips_404_for_unknown_job(client, auth_headers, monkeypatch):
    _mock_storage(monkeypatch)
    created = client.post(
        "/api/v1/cvs",
        json={"name": "My Resume", "gcs_path": "cvs/user_1/abc.pdf"},
        headers=auth_headers,
    ).json()

    resp = client.post(f"/api/v1/cvs/{created['id']}/tips/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_cv_tips_422_when_cv_has_no_extracted_text(client, auth_headers, monkeypatch, job):
    _mock_storage(monkeypatch, extracted_text="")
    created = client.post(
        "/api/v1/cvs",
        json={"name": "Empty CV", "gcs_path": "cvs/user_1/empty.txt"},
        headers=auth_headers,
    ).json()

    resp = client.post(f"/api/v1/cvs/{created['id']}/tips/{job['id']}", headers=auth_headers)
    assert resp.status_code == 422
