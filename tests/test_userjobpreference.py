"""Tests for POST /user-job-preferences."""


def test_create_preference(client, auth_headers):
    resp = client.post(
        "/api/v1/user-job-preferences",
        json={"keyword": "intern", "is_excluded": True},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["keyword"] == "intern"
    assert body["is_excluded"] is True


def test_create_preference_requires_auth(client):
    resp = client.post(
        "/api/v1/user-job-preferences",
        json={"keyword": "intern", "is_excluded": True},
    )
    assert resp.status_code == 401
