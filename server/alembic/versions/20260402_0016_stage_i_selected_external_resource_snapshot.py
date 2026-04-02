"""Add selected external resource snapshot to research analysis runs.

Revision ID: 20260402_0016
Revises: 20260402_0015
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260402_0016"
down_revision = "20260402_0015"
branch_labels = None
depends_on = None

_SELECTED_SNAPSHOT_FK = "fk_research_runs_selected_snapshot_id"
_SELECTED_SNAPSHOT_INDEX = "ix_research_runs_selected_snapshot_id"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    run_columns = {column["name"] for column in inspector.get_columns("research_analysis_runs")}
    if "selected_external_resource_snapshot_id" not in run_columns:
        op.add_column(
            "research_analysis_runs",
            sa.Column("selected_external_resource_snapshot_id", sa.String(length=36), nullable=True),
        )
        inspector = inspect(bind)

    existing_run_foreign_keys = {
        foreign_key["name"] for foreign_key in inspector.get_foreign_keys("research_analysis_runs")
    }
    if _SELECTED_SNAPSHOT_FK not in existing_run_foreign_keys:
        op.create_foreign_key(
            _SELECTED_SNAPSHOT_FK,
            "research_analysis_runs",
            "research_external_resource_snapshots",
            ["selected_external_resource_snapshot_id"],
            ["id"],
        )

    existing_run_indexes = {index["name"] for index in inspector.get_indexes("research_analysis_runs")}
    if _SELECTED_SNAPSHOT_INDEX not in existing_run_indexes:
        op.create_index(
            _SELECTED_SNAPSHOT_INDEX,
            "research_analysis_runs",
            ["selected_external_resource_snapshot_id"],
        )


def downgrade() -> None:
    op.drop_index(
        _SELECTED_SNAPSHOT_INDEX,
        table_name="research_analysis_runs",
    )
    op.drop_constraint(
        _SELECTED_SNAPSHOT_FK,
        "research_analysis_runs",
        type_="foreignkey",
    )
    op.drop_column("research_analysis_runs", "selected_external_resource_snapshot_id")
