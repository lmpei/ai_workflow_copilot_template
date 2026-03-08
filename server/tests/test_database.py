from sqlalchemy import inspect

from app.core.database import ensure_database_ready, get_engine


def test_database_foundation_creates_phase_one_tables() -> None:
    ensure_database_ready()

    tables = set(inspect(get_engine()).get_table_names())

    assert {
        "users",
        "workspaces",
        "workspace_members",
        "documents",
        "conversations",
        "messages",
        "traces",
    }.issubset(tables)
