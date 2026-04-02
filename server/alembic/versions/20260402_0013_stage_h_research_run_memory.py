"""Add resumed run pointers and bounded run memory to research analysis runs.

Revision ID: 20260402_0013
Revises: 20260401_0012
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0013"
down_revision = "20260401_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "research_analysis_runs",
        sa.Column("resumed_from_run_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "research_analysis_runs",
        sa.Column("run_memory_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_foreign_key(
        "fk_research_analysis_runs_resumed_from_run_id",
        "research_analysis_runs",
        "research_analysis_runs",
        ["resumed_from_run_id"],
        ["id"],
    )
    op.create_index(
        "ix_research_analysis_runs_resumed_from_run_id",
        "research_analysis_runs",
        ["resumed_from_run_id"],
    )
    op.alter_column("research_analysis_runs", "run_memory_json", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_research_analysis_runs_resumed_from_run_id", table_name="research_analysis_runs")
    op.drop_constraint(
        "fk_research_analysis_runs_resumed_from_run_id",
        "research_analysis_runs",
        type_="foreignkey",
    )
    op.drop_column("research_analysis_runs", "run_memory_json")
    op.drop_column("research_analysis_runs", "resumed_from_run_id")
