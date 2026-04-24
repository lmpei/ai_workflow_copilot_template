"""Add AI hot tracker runtime and quality fields.

Revision ID: 20260424_0022
Revises: 20260423_0021
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260424_0022"
down_revision = "20260423_0021"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    tracking_state_columns = _column_names("ai_hot_tracker_tracking_state")
    if "latest_saved_run_generated_at" not in tracking_state_columns:
        op.add_column(
            "ai_hot_tracker_tracking_state",
            sa.Column("latest_saved_run_generated_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "latest_meaningful_update_at" not in tracking_state_columns:
        op.add_column(
            "ai_hot_tracker_tracking_state",
            sa.Column("latest_meaningful_update_at", sa.DateTime(timezone=True), nullable=True),
        )

    signal_memory_columns = _column_names("ai_hot_tracker_signal_memory")
    if "streak_count" not in signal_memory_columns:
        op.add_column(
            "ai_hot_tracker_signal_memory",
            sa.Column("streak_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if "cooling_since" not in signal_memory_columns:
        op.add_column(
            "ai_hot_tracker_signal_memory",
            sa.Column("cooling_since", sa.DateTime(timezone=True), nullable=True),
        )
    if "superseded_by_event_id" not in signal_memory_columns:
        op.add_column(
            "ai_hot_tracker_signal_memory",
            sa.Column("superseded_by_event_id", sa.String(length=40), nullable=True),
        )


def downgrade() -> None:
    signal_memory_columns = _column_names("ai_hot_tracker_signal_memory")
    if "superseded_by_event_id" in signal_memory_columns:
        op.drop_column("ai_hot_tracker_signal_memory", "superseded_by_event_id")
    if "cooling_since" in signal_memory_columns:
        op.drop_column("ai_hot_tracker_signal_memory", "cooling_since")
    if "streak_count" in signal_memory_columns:
        op.drop_column("ai_hot_tracker_signal_memory", "streak_count")

    tracking_state_columns = _column_names("ai_hot_tracker_tracking_state")
    if "latest_meaningful_update_at" in tracking_state_columns:
        op.drop_column("ai_hot_tracker_tracking_state", "latest_meaningful_update_at")
    if "latest_saved_run_generated_at" in tracking_state_columns:
        op.drop_column("ai_hot_tracker_tracking_state", "latest_saved_run_generated_at")
