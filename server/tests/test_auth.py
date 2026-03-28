import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings


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
    assert duplicate_response.json()["detail"] == "该邮箱已被注册"


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
    assert response.json()["detail"] == "邮箱或密码不正确"


def test_me_rejects_invalid_or_missing_token(client: TestClient) -> None:
    missing_token_response = client.get("/api/v1/auth/me")
    assert missing_token_response.status_code == 401

    invalid_token_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert invalid_token_response.status_code == 401


def test_public_demo_registration_can_be_disabled(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "public_demo_mode", True)
    monkeypatch.setattr(settings, "public_demo_registration_enabled", False)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "outside-user@example.com",
            "password": "super-secret",
            "name": "Outside User",
        },
    )

    assert response.status_code == 403
    assert "当前已关闭 public demo 自助注册" in response.json()["detail"]


def test_public_demo_settings_endpoint_exposes_limits(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "public_demo_mode", True)
    monkeypatch.setattr(settings, "public_demo_registration_enabled", False)
    monkeypatch.setattr(settings, "public_demo_max_workspaces_per_user", 2)
    monkeypatch.setattr(settings, "public_demo_max_documents_per_workspace", 7)
    monkeypatch.setattr(settings, "public_demo_max_tasks_per_workspace", 11)
    monkeypatch.setattr(settings, "public_demo_max_upload_bytes", 3 * 1024 * 1024)

    response = client.get("/api/v1/public-demo")

    assert response.status_code == 200
    assert response.json() == {
        "public_demo_mode": True,
        "registration_enabled": False,
        "max_workspaces_per_user": 2,
        "max_documents_per_workspace": 7,
        "max_tasks_per_workspace": 11,
        "max_upload_bytes": 3145728,
    }


@pytest.mark.parametrize("secret", ["phase1-dev-secret", "replace_me", "   "])
def test_settings_rejects_insecure_auth_secret_key(secret: str) -> None:
    with pytest.raises(
        ValidationError,
        match="AUTH_SECRET_KEY must be set to a unique non-default value",
    ):
        Settings(auth_secret_key=secret, _env_file=None)
