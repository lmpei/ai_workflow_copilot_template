"""Add Stage I research external resource snapshots.

Revision ID: 20260402_0015
Revises: 20260402_0014
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0015"
down_revision = "20260402_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_index(
        "ix_research_external_resource_snapshots_workspace_id",
        "research_external_resource_snapshots",
        ["workspace_id"],
    )
    op.create_index(
        "ix_research_external_resource_snapshots_conversation_id",
        "research_external_resource_snapshots",
        ["conversation_id"],
    )
    op.create_index(
        "ix_research_external_resource_snapshots_created_by",
        "research_external_resource_snapshots",
        ["created_by"],
    )
    op.create_index(
        "ix_research_external_resource_snapshots_connector_id",
        "research_external_resource_snapshots",
        ["connector_id"],
    )
    op.create_index(
        "ix_research_external_resource_snapshots_source_run_id",
        "research_external_resource_snapshots",
        ["source_run_id"],
    )

    op.add_column(
        "research_analysis_runs",
        sa.Column("external_resource_snapshot_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_research_analysis_runs_external_resource_snapshot_id",
        "research_analysis_runs",
        "research_external_resource_snapshots",
        ["external_resource_snapshot_id"],
        ["id"],
    )
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
