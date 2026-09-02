"""Tests for POST/GET/DELETE /user-designation."""


def test_create_list_delete_user_designation(client, auth_headers, designation):
    # register_and_login already auto-subscribes the user to every designation
    # that existed at signup time; `designation` fixture is created afterwards,
    # so it must be subscribed to explicitly here.
    resp = client.post(
        "/api/v1/user-designation",
        json={"designation_id": designation["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    ud = resp.json()
    assert ud["designation_id"] == designation["id"]

    resp = client.get("/api/v1/user-designation", headers=auth_headers)
    assert resp.status_code == 200
    ids = [row["id"] for row in resp.json()]
    assert ud["id"] in ids

    resp = client.delete(f"/api/v1/user-designation?user_designation_id={ud['id']}", headers=auth_headers)
    assert resp.status_code == 200

    resp = client.get("/api/v1/user-designation", headers=auth_headers)
    ids = [row["id"] for row in resp.json()]
    assert ud["id"] not in ids


def test_duplicate_subscription_is_rejected(client, auth_headers, designation):
    client.post("/api/v1/user-designation", json={"designation_id": designation["id"]}, headers=auth_headers)
    resp = client.post("/api/v1/user-designation", json={"designation_id": designation["id"]}, headers=auth_headers)
    assert resp.status_code == 400


def test_subscribing_to_unknown_designation_is_rejected(client, auth_headers):
    resp = client.post("/api/v1/user-designation", json={"designation_id": 999999}, headers=auth_headers)
    assert resp.status_code == 400


def test_cannot_delete_another_users_subscription(client, auth_headers, designation):
    from tests.conftest import register_and_login

    resp = client.post(
        "/api/v1/user-designation",
        json={"designation_id": designation["id"]},
        headers=auth_headers,
    )
    ud_id = resp.json()["id"]

    _, other_headers = register_and_login(client, "intruder@example.com")
    resp = client.delete(f"/api/v1/user-designation?user_designation_id={ud_id}", headers=other_headers)
    assert resp.status_code == 400
