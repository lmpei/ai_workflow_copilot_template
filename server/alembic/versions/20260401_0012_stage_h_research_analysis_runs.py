"""Add Stage H Research analysis run table.

Revision ID: 20260401_0012
Revises: 20260328_0011
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260401_0012"
down_revision = "20260328_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_analysis_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=36), nullable=True),
        sa.Column("sources_json", sa.JSON(), nullable=False),
        sa.Column("tool_steps_json", sa.JSON(), nullable=False),
        sa.Column("analysis_focus", sa.Text(), nullable=True),
        sa.Column("search_query", sa.Text(), nullable=True),
        sa.Column("degraded_reason", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_research_analysis_runs_workspace_id", "research_analysis_runs", ["workspace_id"])
    op.create_index("ix_research_analysis_runs_conversation_id", "research_analysis_runs", ["conversation_id"])
    op.create_index("ix_research_analysis_runs_created_by", "research_analysis_runs", ["created_by"])
    op.create_index("ix_research_analysis_runs_status", "research_analysis_runs", ["status"])
    op.create_index("ix_research_analysis_runs_trace_id", "research_analysis_runs", ["trace_id"])


def downgrade() -> None:
    op.drop_index("ix_research_analysis_runs_trace_id", table_name="research_analysis_runs")
    op.drop_index("ix_research_analysis_runs_status", table_name="research_analysis_runs")
    op.drop_index("ix_research_analysis_runs_created_by", table_name="research_analysis_runs")
    op.drop_index("ix_research_analysis_runs_conversation_id", table_name="research_analysis_runs")
    op.drop_index("ix_research_analysis_runs_workspace_id", table_name="research_analysis_runs")
    op.drop_table("research_analysis_runs")
