from sqlalchemy import inspect

from app.core.database import ensure_database_ready, get_engine


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
