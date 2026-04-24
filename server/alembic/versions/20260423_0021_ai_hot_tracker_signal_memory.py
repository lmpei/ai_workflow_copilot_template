"""Add AI hot tracker signal memory.

Revision ID: 20260423_0021
Revises: 20260421_0020
Create Date: 2026-04-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260423_0021"
down_revision = "20260421_0020"
branch_labels = None
depends_on = None

_TABLE_NAME = "ai_hot_tracker_signal_memory"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if _TABLE_NAME in table_names:
        return

    op.create_table(
        _TABLE_NAME,
        sa.Column("id", sa.String(length=40), primary_key=True),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("fingerprint", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("continuity_state", sa.String(length=20), nullable=False, server_default="continuing"),
        sa.Column("activity_state", sa.String(length=20), nullable=False, server_default="continuing"),
        sa.Column("source_families_json", sa.JSON(), nullable=False),
        sa.Column("source_item_ids_json", sa.JSON(), nullable=False),
        sa.Column("source_labels_json", sa.JSON(), nullable=False),
        sa.Column("latest_priority_level", sa.String(length=10), nullable=False, server_default="low"),
        sa.Column("latest_rank_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "last_seen_run_id",
            sa.String(length=36),
            sa.ForeignKey("ai_hot_tracker_tracking_runs.id"),
            nullable=True,
        ),
        sa.Column("last_cluster_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "workspace_id",
            "fingerprint",
            name="uq_ai_hot_tracker_signal_memory_workspace_fingerprint",
        ),
    )
    op.create_index("ix_ai_hot_tracker_signal_memory_workspace_id", _TABLE_NAME, ["workspace_id"])
    op.create_index("ix_ai_hot_tracker_signal_memory_fingerprint", _TABLE_NAME, ["fingerprint"])
    op.create_index("ix_ai_hot_tracker_signal_memory_category", _TABLE_NAME, ["category"])
    op.create_index("ix_ai_hot_tracker_signal_memory_last_seen_at", _TABLE_NAME, ["last_seen_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_hot_tracker_signal_memory_last_seen_at", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_hot_tracker_signal_memory_category", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_hot_tracker_signal_memory_fingerprint", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_hot_tracker_signal_memory_workspace_id", table_name=_TABLE_NAME)
    op.drop_table(_TABLE_NAME)
