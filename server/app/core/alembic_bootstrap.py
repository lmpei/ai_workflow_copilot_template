from __future__ import annotations

from collections.abc import Iterable, Mapping

from sqlalchemy import inspect

from app.core.database import get_engine

PHASE1_MARKER_TABLES = {
    "users",
    "workspaces",
    "workspace_members",
    "documents",
    "conversations",
    "messages",
    "traces",
}
PHASE2_MARKER_TABLES = {
    "document_chunks",
    "embeddings",
}
PHASE3_MARKER_TABLES = {
    "tasks",
    "agent_runs",
    "tool_calls",
}
PHASE4_EVAL_MARKER_TABLES = {
    "eval_datasets",
    "eval_cases",
    "eval_runs",
    "eval_results",
}
PHASE4_TRACE_MARKER_COLUMNS = {
    "parent_trace_id",
    "task_id",
    "agent_run_id",
    "tool_call_id",
    "eval_run_id",
    "metadata_json",
    "error_message",
}
PHASE5_WORKSPACE_MARKER_COLUMNS = {
    "module_type",
    "module_config_json",
}


def infer_legacy_revision(
    existing_tables: Iterable[str],
    existing_columns_by_table: Mapping[str, set[str]] | None = None,
) -> str | None:
    tables = set(existing_tables)
    columns_by_table = existing_columns_by_table or {}
    if "alembic_version" in tables:
        return None
    if PHASE5_WORKSPACE_MARKER_COLUMNS & columns_by_table.get("workspaces", set()):
        return "20260316_0006"
    if PHASE4_EVAL_MARKER_TABLES.issubset(tables):
        return "20260314_0005"
    if PHASE4_TRACE_MARKER_COLUMNS & columns_by_table.get("traces", set()):
        return "20260314_0004"
    if PHASE3_MARKER_TABLES.issubset(tables):
        return "20260314_0003"
    if PHASE2_MARKER_TABLES.issubset(tables):
        return "20260311_0002"
    if PHASE1_MARKER_TABLES.issubset(tables):
        return "20260308_0001"
    return None


def get_legacy_stamp_revision() -> str | None:
    inspector = inspect(get_engine())
    table_names = inspector.get_table_names()
    columns_by_table = {
        table_name: {column["name"] for column in inspector.get_columns(table_name)}
        for table_name in table_names
    }
    return infer_legacy_revision(table_names, columns_by_table)


def main() -> None:
    revision = get_legacy_stamp_revision()
    if revision is not None:
        print(revision)


if __name__ == "__main__":
    main()
