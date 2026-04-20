import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings


def test_enter_registers_new_account_and_returns_session(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/enter",
        json={
            "account": "owner-account",
            "password": "super-secret",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "owner-account"
    assert payload["user"]["name"] == "owner-account"


def test_enter_logs_in_existing_account(client: TestClient) -> None:
    first_response = client.post(
        "/api/v1/auth/enter",
        json={
            "account": "owner-account",
            "password": "super-secret",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/auth/enter",
        json={
            "account": "owner-account",
            "password": "super-secret",
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["user"]["email"] == "owner-account"


def test_enter_rejects_wrong_password_for_existing_account(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/enter",
        json={
            "account": "owner-account",
            "password": "super-secret",
        },
    )

    response = client.post(
        "/api/v1/auth/enter",
        json={
            "account": "owner-account",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "账号或密码不正确"


def test_register_login_and_me(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "super-secret",
            "name": "Owner",
        },
    )
    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["email"] == "owner@example.com"
    assert registered_user["role"] == "owner"

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@example.com",
            "password": "super-secret",
        },
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["token_type"] == "bearer"

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "owner@example.com"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "duplicate@example.com",
        "password": "super-secret",
        "name": "Owner",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    assert first_response.status_code == 201

    duplicate_response = client.post("/api/v1/auth/register", json=payload)
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "该账号已被注册"


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "super-secret",
            "name": "Owner",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "账号或密码不正确"


def test_me_rejects_invalid_or_missing_token(client: TestClient) -> None:
    missing_token_response = client.get("/api/v1/auth/me")
    assert missing_token_response.status_code == 401

    invalid_token_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert invalid_token_response.status_code == 401


@pytest.mark.parametrize("secret", ["phase1-dev-secret", "replace_me", "   "])
def test_settings_rejects_insecure_auth_secret_key(secret: str) -> None:
    with pytest.raises(
        ValidationError,
        match="AUTH_SECRET_KEY must be set to a unique non-default value",
    ):
        Settings(auth_secret_key=secret, _env_file=None)
