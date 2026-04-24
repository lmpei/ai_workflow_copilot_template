"""Add AI hot tracker tracking state.

Revision ID: 20260421_0020
Revises: 20260421_0019
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260421_0020"
down_revision = "20260421_0019"
branch_labels = None
depends_on = None

_TABLE_NAME = "ai_hot_tracker_tracking_state"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if _TABLE_NAME in table_names:
        return

    op.create_table(
        _TABLE_NAME,
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), primary_key=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_cluster_snapshot_json", sa.JSON(), nullable=False),
        sa.Column(
            "last_saved_run_id",
            sa.String(length=36),
            sa.ForeignKey("ai_hot_tracker_tracking_runs.id"),
            nullable=True,
        ),
        sa.Column(
            "last_notified_run_id",
            sa.String(length=36),
            sa.ForeignKey("ai_hot_tracker_tracking_runs.id"),
            nullable=True,
        ),
        sa.Column("consecutive_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_hot_tracker_tracking_state_next_due_at", _TABLE_NAME, ["next_due_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_hot_tracker_tracking_state_next_due_at", table_name=_TABLE_NAME)
    op.drop_table(_TABLE_NAME)
