"""Add Phase 5 workspace module contract columns."""

import sqlalchemy as sa

from alembic import op

revision = "20260316_0006"
down_revision = "20260314_0005"
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


def upgrade() -> None:
    with op.batch_alter_table("workspaces") as batch_op:
        batch_op.add_column(
            sa.Column(
                "module_type",
                sa.String(length=50),
                nullable=True,
                server_default=sa.text("'research'"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "module_config_json",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            )
        )
        batch_op.create_index("ix_workspaces_module_type", ["module_type"], unique=False)

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
        "WHERE module_type = 'research'"
    )
    op.execute(
        "UPDATE workspaces "
        f"SET module_config_json = '{_SUPPORT_CONFIG}' "
        "WHERE module_type = 'support'"
    )
    op.execute(
        "UPDATE workspaces "
        f"SET module_config_json = '{_JOB_CONFIG}' "
        "WHERE module_type = 'job'"
    )

    with op.batch_alter_table("workspaces") as batch_op:
        batch_op.alter_column("module_type", nullable=False, server_default=None)
        batch_op.alter_column("module_config_json", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("workspaces") as batch_op:
        batch_op.drop_index("ix_workspaces_module_type")
        batch_op.drop_column("module_config_json")
        batch_op.drop_column("module_type")
