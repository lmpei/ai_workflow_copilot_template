"""Add Stage I research external resource snapshots.

Revision ID: 20260402_0015
Revises: 20260402_0014
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260402_0015"
down_revision = "20260402_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("research_external_resource_snapshots"):
        op.create_table(
            "research_external_resource_snapshots",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
            sa.Column("conversation_id", sa.String(length=36), sa.ForeignKey("conversations.id"), nullable=True),
            sa.Column("created_by", sa.String(length=36), nullable=False),
            sa.Column("connector_id", sa.String(length=100), nullable=False),
            sa.Column("source_run_id", sa.String(length=36), sa.ForeignKey("research_analysis_runs.id"), nullable=True),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("analysis_focus", sa.Text(), nullable=True),
            sa.Column("search_query", sa.Text(), nullable=False),
            sa.Column("resource_count", sa.Integer(), nullable=False),
            sa.Column("resources_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        inspector = inspect(bind)

    existing_snapshot_indexes = {
        index["name"] for index in inspector.get_indexes("research_external_resource_snapshots")
    }
    for index_name, columns in [
        ("ix_research_external_resource_snapshots_workspace_id", ["workspace_id"]),
        ("ix_research_external_resource_snapshots_conversation_id", ["conversation_id"]),
        ("ix_research_external_resource_snapshots_created_by", ["created_by"]),
        ("ix_research_external_resource_snapshots_connector_id", ["connector_id"]),
        ("ix_research_external_resource_snapshots_source_run_id", ["source_run_id"]),
    ]:
        if index_name not in existing_snapshot_indexes:
            op.create_index(index_name, "research_external_resource_snapshots", columns)

    run_columns = {column["name"] for column in inspector.get_columns("research_analysis_runs")}
    if "external_resource_snapshot_id" not in run_columns:
        op.add_column(
            "research_analysis_runs",
            sa.Column("external_resource_snapshot_id", sa.String(length=36), nullable=True),
        )
        inspector = inspect(bind)

    existing_run_foreign_keys = {
        foreign_key["name"] for foreign_key in inspector.get_foreign_keys("research_analysis_runs")
    }
    if "fk_research_analysis_runs_external_resource_snapshot_id" not in existing_run_foreign_keys:
        op.create_foreign_key(
            "fk_research_analysis_runs_external_resource_snapshot_id",
            "research_analysis_runs",
            "research_external_resource_snapshots",
            ["external_resource_snapshot_id"],
            ["id"],
        )

    existing_run_indexes = {index["name"] for index in inspector.get_indexes("research_analysis_runs")}
    if "ix_research_analysis_runs_external_resource_snapshot_id" not in existing_run_indexes:
        op.create_index(
            "ix_research_analysis_runs_external_resource_snapshot_id",
            "research_analysis_runs",
            ["external_resource_snapshot_id"],
        )


def downgrade() -> None:
    op.drop_index(
        "ix_research_analysis_runs_external_resource_snapshot_id",
        table_name="research_analysis_runs",
    )
    op.drop_constraint(
        "fk_research_analysis_runs_external_resource_snapshot_id",
        "research_analysis_runs",
        type_="foreignkey",
    )
    op.drop_column("research_analysis_runs", "external_resource_snapshot_id")

    op.drop_index(
        "ix_research_external_resource_snapshots_source_run_id",
        table_name="research_external_resource_snapshots",
    )
    op.drop_index(
        "ix_research_external_resource_snapshots_connector_id",
        table_name="research_external_resource_snapshots",
    )
    op.drop_index(
        "ix_research_external_resource_snapshots_created_by",
        table_name="research_external_resource_snapshots",
    )
    op.drop_index(
        "ix_research_external_resource_snapshots_conversation_id",
        table_name="research_external_resource_snapshots",
    )
    op.drop_index(
        "ix_research_external_resource_snapshots_workspace_id",
        table_name="research_external_resource_snapshots",
    )
    op.drop_table("research_external_resource_snapshots")
