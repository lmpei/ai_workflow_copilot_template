"""Add selected external resource snapshot to research analysis runs.

Revision ID: 20260402_0016
Revises: 20260402_0015
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0016"
down_revision = "20260402_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "research_analysis_runs",
        sa.Column("selected_external_resource_snapshot_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_research_analysis_runs_selected_external_resource_snapshot_id",
        "research_analysis_runs",
        "research_external_resource_snapshots",
        ["selected_external_resource_snapshot_id"],
        ["id"],
    )
    op.create_index(
        "ix_research_analysis_runs_selected_external_resource_snapshot_id",
        "research_analysis_runs",
        ["selected_external_resource_snapshot_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_research_analysis_runs_selected_external_resource_snapshot_id",
        table_name="research_analysis_runs",
    )
    op.drop_constraint(
        "fk_research_analysis_runs_selected_external_resource_snapshot_id",
        "research_analysis_runs",
        type_="foreignkey",
    )
    op.drop_column("research_analysis_runs", "selected_external_resource_snapshot_id")
