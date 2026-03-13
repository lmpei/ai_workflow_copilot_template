from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Workflow Copilot API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/ai_workflow"
    redis_url: str = "redis://redis:6379/0"
    openai_api_key: str = "replace_me"
    chat_provider: str = "qwen"
    chat_api_key: str = "replace_me"
    chat_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    chat_model: str = "qwen-plus"
    embedding_provider: str = "qwen"
    embedding_api_key: str = "replace_me"
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v4"
    chroma_url: str = "http://chroma:8000"
    chroma_collection_name: str = "workspace_documents"
    internal_api_base_url: str = "http://server:8000/api/v1"
    vector_store_backend: str = "chroma"
    default_workspace_type: str = "research"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
