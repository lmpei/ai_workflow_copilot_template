"""Add Phase 4 trace linkage and metadata columns."""

import sqlalchemy as sa

from alembic import op

revision = "20260314_0004"
down_revision = "20260314_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("traces") as batch_op:
        batch_op.add_column(sa.Column("parent_trace_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("task_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("agent_run_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("tool_call_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("eval_run_id", sa.String(length=36), nullable=True))
        batch_op.add_column(
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'"))
        )
        batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))
        batch_op.create_index("ix_traces_parent_trace_id", ["parent_trace_id"], unique=False)
        batch_op.create_index("ix_traces_task_id", ["task_id"], unique=False)
        batch_op.create_index("ix_traces_agent_run_id", ["agent_run_id"], unique=False)
        batch_op.create_index("ix_traces_tool_call_id", ["tool_call_id"], unique=False)
        batch_op.create_index("ix_traces_eval_run_id", ["eval_run_id"], unique=False)

    op.execute("UPDATE traces SET metadata_json = '{}' WHERE metadata_json IS NULL")

    with op.batch_alter_table("traces") as batch_op:
        batch_op.alter_column("metadata_json", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("traces") as batch_op:
        batch_op.drop_index("ix_traces_eval_run_id")
        batch_op.drop_index("ix_traces_tool_call_id")
        batch_op.drop_index("ix_traces_agent_run_id")
        batch_op.drop_index("ix_traces_task_id")
        batch_op.drop_index("ix_traces_parent_trace_id")
        batch_op.drop_column("error_message")
        batch_op.drop_column("metadata_json")
        batch_op.drop_column("eval_run_id")
        batch_op.drop_column("tool_call_id")
        batch_op.drop_column("agent_run_id")
        batch_op.drop_column("task_id")
        batch_op.drop_column("parent_trace_id")
