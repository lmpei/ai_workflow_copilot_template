"""Add Stage E Support case workbench tables."""

import sqlalchemy as sa

from alembic import op

revision = "20260328_0010"
down_revision = "20260318_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_cases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("latest_task_id", sa.String(length=36), nullable=True),
        sa.Column("latest_task_type", sa.String(length=100), nullable=False),
        sa.Column("latest_input_json", sa.JSON(), nullable=False),
        sa.Column("latest_result_json", sa.JSON(), nullable=False),
        sa.Column("latest_summary", sa.Text(), nullable=False),
        sa.Column("latest_recommended_owner", sa.String(length=100), nullable=True),
        sa.Column("latest_evidence_status", sa.String(length=50), nullable=True),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["latest_task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_support_cases_workspace_id"), "support_cases", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_support_cases_created_by"), "support_cases", ["created_by"], unique=False)
    op.create_index(op.f("ix_support_cases_status"), "support_cases", ["status"], unique=False)
    op.create_index(op.f("ix_support_cases_latest_task_id"), "support_cases", ["latest_task_id"], unique=False)

    op.create_table(
        "support_case_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("support_case_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("event_kind", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("case_status", sa.String(length=50), nullable=False),
        sa.Column("recommended_owner", sa.String(length=100), nullable=True),
        sa.Column("evidence_status", sa.String(length=50), nullable=True),
        sa.Column("should_escalate", sa.Boolean(), nullable=False),
        sa.Column("needs_manual_review", sa.Boolean(), nullable=False),
        sa.Column("follow_up_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["support_case_id"], ["support_cases.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", name="uq_support_case_event_task_id"),
    )
    op.create_index(op.f("ix_support_case_events_support_case_id"), "support_case_events", ["support_case_id"], unique=False)
    op.create_index(op.f("ix_support_case_events_task_id"), "support_case_events", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_support_case_events_task_id"), table_name="support_case_events")
    op.drop_index(op.f("ix_support_case_events_support_case_id"), table_name="support_case_events")
    op.drop_table("support_case_events")

    op.drop_index(op.f("ix_support_cases_latest_task_id"), table_name="support_cases")
    op.drop_index(op.f("ix_support_cases_status"), table_name="support_cases")
    op.drop_index(op.f("ix_support_cases_created_by"), table_name="support_cases")
    op.drop_index(op.f("ix_support_cases_workspace_id"), table_name="support_cases")
    op.drop_table("support_cases")
