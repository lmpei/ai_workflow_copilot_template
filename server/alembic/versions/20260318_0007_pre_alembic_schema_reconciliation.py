"""Reconcile legacy pre-Alembic schema drift."""

import sqlalchemy as sa

from alembic import op

revision = "20260318_0007"
down_revision = "20260316_0006"
branch_labels = None
depends_on = None

_RESEARCH_CONFIG = (
    '{"entry_task_types": ["research_summary", "workspace_report"], '
    '"result_type": "research_report", '
    '"features": ["documents", "grounded_chat", "tasks", "evals"]}'
)
_SUPPORT_CONFIG = (
    '{"entry_task_types": ["ticket_summary", "reply_draft"], '
    '"result_type": "support_case_summary", '
    '"features": ["knowledge_base", "reply_drafts", "tasks", "evals"]}'
)
_JOB_CONFIG = (
    '{"entry_task_types": ["jd_summary", "resume_match"], '
    '"result_type": "job_match_summary", '
    '"features": ["document_intake", "structured_extraction", "tasks", "evals"]}'
)


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _ensure_trace_columns() -> None:
    with op.batch_alter_table("traces") as batch_op:
        if not _has_column("traces", "parent_trace_id"):
            batch_op.add_column(sa.Column("parent_trace_id", sa.String(length=36), nullable=True))
        if not _has_column("traces", "task_id"):
            batch_op.add_column(sa.Column("task_id", sa.String(length=36), nullable=True))
        if not _has_column("traces", "agent_run_id"):
            batch_op.add_column(sa.Column("agent_run_id", sa.String(length=36), nullable=True))
        if not _has_column("traces", "tool_call_id"):
            batch_op.add_column(sa.Column("tool_call_id", sa.String(length=36), nullable=True))
        if not _has_column("traces", "eval_run_id"):
            batch_op.add_column(sa.Column("eval_run_id", sa.String(length=36), nullable=True))
        if not _has_column("traces", "metadata_json"):
            batch_op.add_column(
                sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'"))
            )
        if not _has_column("traces", "error_message"):
            batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))

    op.execute("UPDATE traces SET metadata_json = '{}' WHERE metadata_json IS NULL")

    with op.batch_alter_table("traces") as batch_op:
        if _has_column("traces", "metadata_json"):
            batch_op.alter_column("metadata_json", nullable=False, server_default=None)
        if not _has_index("traces", "ix_traces_parent_trace_id"):
            batch_op.create_index("ix_traces_parent_trace_id", ["parent_trace_id"], unique=False)
        if not _has_index("traces", "ix_traces_task_id"):
            batch_op.create_index("ix_traces_task_id", ["task_id"], unique=False)
        if not _has_index("traces", "ix_traces_agent_run_id"):
            batch_op.create_index("ix_traces_agent_run_id", ["agent_run_id"], unique=False)
        if not _has_index("traces", "ix_traces_tool_call_id"):
            batch_op.create_index("ix_traces_tool_call_id", ["tool_call_id"], unique=False)
        if not _has_index("traces", "ix_traces_eval_run_id"):
            batch_op.create_index("ix_traces_eval_run_id", ["eval_run_id"], unique=False)


def _ensure_workspace_module_columns() -> None:
    with op.batch_alter_table("workspaces") as batch_op:
        if not _has_column("workspaces", "module_type"):
            batch_op.add_column(
                sa.Column(
                    "module_type",
                    sa.String(length=50),
                    nullable=True,
                    server_default=sa.text("'research'"),
                )
            )
        if not _has_column("workspaces", "module_config_json"):
            batch_op.add_column(
                sa.Column(
                    "module_config_json",
                    sa.JSON(),
                    nullable=False,
                    server_default=sa.text("'{}'"),
                )
            )

    op.execute(
        """
        UPDATE workspaces
        SET module_type = CASE
            WHEN type IN ('research', 'support', 'job') THEN type
            ELSE 'research'
        END
        WHERE module_type IS NULL OR module_type = ''
        """
    )
    op.execute(
        "UPDATE workspaces "
        f"SET module_config_json = '{_RESEARCH_CONFIG}' "
        "WHERE module_type = 'research' AND (module_config_json IS NULL OR CAST(module_config_json AS text) = '{}')"
    )
    op.execute(
        "UPDATE workspaces "
        f"SET module_config_json = '{_SUPPORT_CONFIG}' "
        "WHERE module_type = 'support' AND (module_config_json IS NULL OR CAST(module_config_json AS text) = '{}')"
    )
    op.execute(
        "UPDATE workspaces "
        f"SET module_config_json = '{_JOB_CONFIG}' "
        "WHERE module_type = 'job' AND (module_config_json IS NULL OR CAST(module_config_json AS text) = '{}')"
    )

    with op.batch_alter_table("workspaces") as batch_op:
        if _has_column("workspaces", "module_type"):
            batch_op.alter_column("module_type", nullable=False, server_default=None)
        if _has_column("workspaces", "module_config_json"):
            batch_op.alter_column("module_config_json", nullable=False, server_default=None)
        if not _has_index("workspaces", "ix_workspaces_module_type"):
            batch_op.create_index("ix_workspaces_module_type", ["module_type"], unique=False)


def upgrade() -> None:
    _ensure_trace_columns()
    _ensure_workspace_module_columns()


def downgrade() -> None:
    pass

