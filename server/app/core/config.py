import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Workflow Copilot API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/ai_workflow"
    redis_url: str = "redis://redis:6379/0"
    task_queue_name: str = "platform_tasks"
    auth_secret_key: str = Field(default="")
    openai_api_key: str = "replace_me"
    chat_provider: str = "qwen"
    chat_api_key: str = "replace_me"
    chat_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    chat_model: str = "qwen-plus"
    eval_provider: str = "qwen"
    eval_api_key: str = "replace_me"
    eval_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    eval_model: str = "qwen-plus"
    embedding_provider: str = "qwen"
    embedding_api_key: str = "replace_me"
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v4"
    chroma_url: str = "http://chroma:8000"
    chroma_collection_name: str = "workspace_documents"
    internal_api_base_url: str = "http://server:8000/api/v1"
    vector_store_backend: str = "chroma"
    default_workspace_type: str = "research"
    public_demo_mode: bool = False
    public_demo_registration_enabled: bool = True
    public_demo_max_workspaces_per_user: int = 3
    public_demo_max_documents_per_workspace: int = 12
    public_demo_max_tasks_per_workspace: int = 30
    public_demo_max_upload_bytes: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @field_validator("auth_secret_key")
    @classmethod
    def validate_auth_secret_key(cls, value: str) -> str:
        normalized = value.strip()
        if normalized in {"", "replace_me", "phase1-dev-secret"}:
            raise ValueError("AUTH_SECRET_KEY must be set to a unique non-default value")
        return normalized


def get_database_url_from_env(*, default: str | None = None) -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    if default is not None:
        return default
    return str(Settings.model_fields["database_url"].default)


@lru_cache
def get_settings() -> Settings:
    return Settings()
