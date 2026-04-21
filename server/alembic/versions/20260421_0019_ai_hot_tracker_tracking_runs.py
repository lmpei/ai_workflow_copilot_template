"""Add AI hot tracker tracking runs.

Revision ID: 20260421_0019
Revises: 20260417_0018
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260421_0019"
down_revision = "20260417_0018"
branch_labels = None
depends_on = None

_TABLE_NAME = "ai_hot_tracker_tracking_runs"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if _TABLE_NAME in table_names:
        return

    op.create_table(
        _TABLE_NAME,
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column(
            "previous_run_id",
            sa.String(length=36),
            sa.ForeignKey("ai_hot_tracker_tracking_runs.id"),
            nullable=True,
        ),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("trigger_kind", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("profile_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("output_json", sa.JSON(), nullable=False),
        sa.Column("source_catalog_json", sa.JSON(), nullable=False),
        sa.Column("source_items_json", sa.JSON(), nullable=False),
        sa.Column("source_failures_json", sa.JSON(), nullable=False),
        sa.Column("source_set_json", sa.JSON(), nullable=False),
        sa.Column("delta_json", sa.JSON(), nullable=False),
        sa.Column("follow_ups_json", sa.JSON(), nullable=False),
        sa.Column("degraded_reason", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_hot_tracker_runs_workspace_id", _TABLE_NAME, ["workspace_id"])
    op.create_index("ix_ai_hot_tracker_runs_previous_run_id", _TABLE_NAME, ["previous_run_id"])
    op.create_index("ix_ai_hot_tracker_runs_created_by", _TABLE_NAME, ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_ai_hot_tracker_runs_created_by", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_hot_tracker_runs_previous_run_id", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_hot_tracker_runs_workspace_id", table_name=_TABLE_NAME)
    op.drop_table(_TABLE_NAME)
