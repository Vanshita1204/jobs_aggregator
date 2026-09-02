"""Tests for POST /auth/register, POST /auth/login, GET /auth/users/me."""


def test_register_creates_user(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "s3cret!", "full_name": "Alice"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["full_name"] == "Alice"
    assert body["is_active"] is True
    assert "hashed_password" not in body


def test_login_with_correct_credentials_returns_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "correct-horse", "full_name": "Bob"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "bob@example.com", "password": "correct-horse"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_is_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "carol@example.com", "password": "right-password", "full_name": "Carol"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "carol@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_login_with_unknown_email_is_rejected(client):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401


def test_users_me_requires_token(client):
    resp = client.get("/api/v1/auth/users/me")
    assert resp.status_code == 401


def test_users_me_returns_current_user(client, auth_headers):
    resp = client.get("/api/v1/auth/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"
