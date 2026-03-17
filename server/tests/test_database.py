import pytest
from pydantic import ValidationError
from sqlalchemy import inspect, text

from app.core.config import Settings, get_database_url_from_env
from app.core.database import ensure_database_ready, get_engine, reset_database_for_tests


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()


def test_database_foundation_creates_phase_one_tables() -> None:
    ensure_database_ready()

    inspector = inspect(get_engine())
    tables = set(inspector.get_table_names())

    assert {
        "users",
        "workspaces",
        "workspace_members",
        "documents",
        "document_chunks",
        "embeddings",
        "conversations",
        "messages",
        "traces",
        "tasks",
        "agent_runs",
        "tool_calls",
        "eval_datasets",
        "eval_cases",
        "eval_runs",
        "eval_results",
    }.issubset(tables)

    trace_columns = {column["name"] for column in inspector.get_columns("traces")}
    assert {
        "parent_trace_id",
        "task_id",
        "agent_run_id",
        "tool_call_id",
        "eval_run_id",
        "metadata_json",
        "error_message",
    }.issubset(trace_columns)

    workspace_columns = {column["name"] for column in inspector.get_columns("workspaces")}
    assert {
        "module_type",
        "module_config_json",
    }.issubset(workspace_columns)


def test_database_ready_rejects_outdated_schema() -> None:
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS workspaces"))
        connection.execute(
            text(
                """
                CREATE TABLE workspaces (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    owner_id VARCHAR(36) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    description TEXT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        ensure_database_ready()


def test_database_url_helper_reads_database_url_without_auth_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///alembic-test.db")
    monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)

    assert get_database_url_from_env() == "sqlite:///alembic-test.db"

    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_database_url_from_env(default="sqlite:///fallback.db") == "sqlite:///fallback.db"

