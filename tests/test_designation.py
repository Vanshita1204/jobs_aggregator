"""Tests for POST /designation and GET /designation."""

from tests.conftest import register_and_login


def test_create_designation_requires_auth(client):
    resp = client.post("/api/v1/designation", json={"title": "Data Engineer"})
    assert resp.status_code == 401


def test_create_and_list_designation(client, auth_headers):
    resp = client.post("/api/v1/designation", json={"title": "Data Engineer"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Data Engineer"
    assert body["created_by"] is not None

    resp = client.get("/api/v1/designation")
    assert resp.status_code == 200
    titles = [d["title"] for d in resp.json()]
    assert "Data Engineer" in titles


def test_duplicate_title_is_rejected(client, auth_headers):
    client.post("/api/v1/designation", json={"title": "SRE"}, headers=auth_headers)
    resp = client.post("/api/v1/designation", json={"title": "SRE"}, headers=auth_headers)
    assert resp.status_code == 400


def test_list_designation_is_public(client):
    """GET /designation has no auth dependency — documented as a public endpoint."""
    resp = client.get("/api/v1/designation")
    assert resp.status_code == 200


def test_new_user_is_auto_subscribed_to_existing_designations(client, auth_headers):
    """register_user() auto-assigns every designation that exists at signup time."""
    client.post("/api/v1/designation", json={"title": "Platform Engineer"}, headers=auth_headers)

    _, other_headers = register_and_login(client, "second@example.com")
    resp = client.get("/api/v1/user-designation", headers=other_headers)
    assert resp.status_code == 200
    titles_via_designation_id = {d["designation_id"] for d in resp.json()}
    assert len(titles_via_designation_id) >= 1
