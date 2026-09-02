"""Tests for POST /user-jobs (create-or-update application status)."""


def test_create_user_job_sets_status(client, auth_headers, job):
    resp = client.post(
        "/api/v1/user-jobs",
        json={"job_id": job["id"], "status": "saved"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job["id"]
    assert body["status"] == "saved"


def test_posting_again_updates_status_instead_of_duplicating(client, auth_headers, job):
    first = client.post(
        "/api/v1/user-jobs",
        json={"job_id": job["id"], "status": "saved"},
        headers=auth_headers,
    ).json()

    second = client.post(
        "/api/v1/user-jobs",
        json={"job_id": job["id"], "status": "applied"},
        headers=auth_headers,
    ).json()

    assert second["id"] == first["id"]  # same UserJob row, unique on (user_id, job_id)
    assert second["status"] == "applied"


def test_invalid_status_is_rejected(client, auth_headers, job):
    resp = client.post(
        "/api/v1/user-jobs",
        json={"job_id": job["id"], "status": "ghosted"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
