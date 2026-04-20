import json
import os
import shlex
from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Workflow Copilot API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
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
    research_external_mcp_enabled: bool = False
    research_external_mcp_command: Annotated[list[str], NoDecode] = []
    research_external_mcp_working_directory: str = ""
    research_external_mcp_auth_required: bool = False
    research_external_mcp_auth_token: str = ""
    research_external_mcp_expected_auth_token: str = ""
    research_external_mcp_resource_id: str = "ai.frontier.digest"
    research_external_mcp_resource_uri: str = "ai-frontier://digest"
    research_external_mcp_server_id: str = "ai_frontier_external"
    research_external_mcp_server_display_name: str = "AI 前沿研究外部 MCP 服务"
    research_external_mcp_server_summary: str = "通过一个仓库外的 MCP 端点读取 AI 前沿研究所需的高可信外部上下文。"
    research_external_mcp_resource_display_name: str = "AI 前沿摘要"
    research_external_mcp_resource_summary: str = "来自独立 MCP 服务端的 AI 前沿摘要资源。"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if normalized == "":
            return []

        if normalized.startswith("["):
            try:
                parsed = json.loads(normalized)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]

        return [item.strip() for item in normalized.split(",") if item.strip()]

    @field_validator("research_external_mcp_command", mode="before")
    @classmethod
    def parse_research_external_mcp_command(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if normalized == "":
            return []

        if normalized.startswith("["):
            try:
                parsed = json.loads(normalized)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]

        return [item.strip() for item in shlex.split(normalized) if item.strip()]

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
