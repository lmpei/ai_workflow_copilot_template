"""Add AI hot tracker background run fields.

Revision ID: 20260426_0023
Revises: 20260424_0022
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260426_0023"
down_revision = "20260424_0022"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = _column_names("ai_hot_tracker_tracking_runs")
    if "started_at" not in columns:
        op.add_column(
            "ai_hot_tracker_tracking_runs",
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "completed_at" not in columns:
        op.add_column(
            "ai_hot_tracker_tracking_runs",
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "failed_at" not in columns:
        op.add_column(
            "ai_hot_tracker_tracking_runs",
            sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "failure_stage" not in columns:
        op.add_column(
            "ai_hot_tracker_tracking_runs",
            sa.Column("failure_stage", sa.String(length=40), nullable=True),
        )
    if "trace_events_json" not in columns:
        op.add_column(
            "ai_hot_tracker_tracking_runs",
            sa.Column("trace_events_json", sa.JSON(), nullable=False, server_default="[]"),
        )


def downgrade() -> None:
    columns = _column_names("ai_hot_tracker_tracking_runs")
    if "trace_events_json" in columns:
        op.drop_column("ai_hot_tracker_tracking_runs", "trace_events_json")
    if "failure_stage" in columns:
        op.drop_column("ai_hot_tracker_tracking_runs", "failure_stage")
    if "failed_at" in columns:
        op.drop_column("ai_hot_tracker_tracking_runs", "failed_at")
    if "completed_at" in columns:
        op.drop_column("ai_hot_tracker_tracking_runs", "completed_at")
    if "started_at" in columns:
        op.drop_column("ai_hot_tracker_tracking_runs", "started_at")
