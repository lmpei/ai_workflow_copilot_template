from app.core.alembic_bootstrap import infer_legacy_revision


def test_infer_legacy_revision_returns_none_when_alembic_version_exists() -> None:
    assert infer_legacy_revision({"users", "alembic_version"}) is None


def test_infer_legacy_revision_detects_phase4_eval_schema() -> None:
    revision = infer_legacy_revision(
        {
            "users",
            "workspaces",
            "workspace_members",
            "documents",
            "conversations",
            "messages",
            "traces",
            "document_chunks",
            "embeddings",
            "tasks",
            "agent_runs",
            "tool_calls",
            "eval_datasets",
            "eval_cases",
            "eval_runs",
            "eval_results",
        }
    )

    assert revision == "20260314_0005"


def test_infer_legacy_revision_detects_phase5_workspace_columns() -> None:
    revision = infer_legacy_revision(
        {"users", "workspaces"},
        {"workspaces": {"id", "type", "module_type", "module_config_json"}},
    )

    assert revision == "20260316_0006"


def test_infer_legacy_revision_detects_phase4_trace_columns() -> None:
    revision = infer_legacy_revision(
        {
            "users",
            "workspaces",
            "workspace_members",
            "documents",
            "conversations",
            "messages",
            "traces",
            "document_chunks",
            "embeddings",
            "tasks",
            "agent_runs",
            "tool_calls",
        },
        {"traces": {"id", "workspace_id", "parent_trace_id", "metadata_json"}},
    )

    assert revision == "20260314_0004"


def test_infer_legacy_revision_detects_phase3_schema() -> None:
    revision = infer_legacy_revision(
        {
            "users",
            "workspaces",
            "workspace_members",
            "documents",
            "conversations",
            "messages",
            "traces",
            "document_chunks",
            "embeddings",
            "tasks",
            "agent_runs",
            "tool_calls",
        }
    )

    assert revision == "20260314_0003"


def test_infer_legacy_revision_detects_phase2_schema() -> None:
    revision = infer_legacy_revision(
        {
            "users",
            "workspaces",
            "workspace_members",
            "documents",
            "conversations",
            "messages",
            "traces",
            "document_chunks",
            "embeddings",
        }
    )

    assert revision == "20260311_0002"


def test_infer_legacy_revision_detects_phase1_schema() -> None:
    revision = infer_legacy_revision(
        {
            "users",
            "workspaces",
            "workspace_members",
            "documents",
            "conversations",
            "messages",
            "traces",
        }
    )

    assert revision == "20260308_0001"
