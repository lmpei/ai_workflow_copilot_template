import pytest

from app.core.config import Settings


def test_settings_accept_app_env_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("AUTH_SECRET_KEY", "stage-d-secret")

    settings = Settings(_env_file=None)

    assert settings.environment == "staging"


def test_settings_accept_comma_delimited_cors_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_SECRET_KEY", "stage-d-secret")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.example.com, https://preview.example.com",
    )

    settings = Settings(_env_file=None)

    assert settings.cors_origins == [
        "https://app.example.com",
        "https://preview.example.com",
    ]
