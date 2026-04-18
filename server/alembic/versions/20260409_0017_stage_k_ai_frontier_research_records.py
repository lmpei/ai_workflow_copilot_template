"""Add AI frontier research records.

Revision ID: 20260409_0017
Revises: 20260402_0016
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260409_0017"
down_revision = "20260402_0016"
branch_labels = None
depends_on = None

_TABLE_NAME = "ai_frontier_research_records"


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
        sa.Column("conversation_id", sa.String(length=36), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("source_run_id", sa.String(length=36), sa.ForeignKey("research_analysis_runs.id"), nullable=True),
        sa.Column("source_trace_id", sa.String(length=36), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("frontier_summary", sa.Text(), nullable=False),
        sa.Column("trend_judgment", sa.Text(), nullable=False),
        sa.Column("themes_json", sa.JSON(), nullable=False),
        sa.Column("events_json", sa.JSON(), nullable=False),
        sa.Column("project_cards_json", sa.JSON(), nullable=False),
        sa.Column("reference_sources_json", sa.JSON(), nullable=False),
        sa.Column("source_set_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_frontier_records_workspace_id", _TABLE_NAME, ["workspace_id"])
    op.create_index("ix_ai_frontier_records_conversation_id", _TABLE_NAME, ["conversation_id"])
    op.create_index("ix_ai_frontier_records_source_run_id", _TABLE_NAME, ["source_run_id"])
    op.create_index("ix_ai_frontier_records_source_trace_id", _TABLE_NAME, ["source_trace_id"])
    op.create_index("ix_ai_frontier_records_created_by", _TABLE_NAME, ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_ai_frontier_records_created_by", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_frontier_records_source_trace_id", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_frontier_records_source_run_id", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_frontier_records_conversation_id", table_name=_TABLE_NAME)
    op.drop_index("ix_ai_frontier_records_workspace_id", table_name=_TABLE_NAME)
    op.drop_table(_TABLE_NAME)
