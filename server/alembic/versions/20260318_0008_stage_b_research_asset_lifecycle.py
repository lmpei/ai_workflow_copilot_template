"""Add Stage B Research asset lifecycle tables."""

import sqlalchemy as sa

from alembic import op

revision = "20260318_0008"
down_revision = "20260318_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("latest_task_id", sa.String(length=36), nullable=True),
        sa.Column("latest_task_type", sa.String(length=100), nullable=False),
        sa.Column("latest_revision_number", sa.Integer(), nullable=False),
        sa.Column("latest_input_json", sa.JSON(), nullable=False),
        sa.Column("latest_result_json", sa.JSON(), nullable=False),
        sa.Column("latest_summary", sa.Text(), nullable=False),
        sa.Column("latest_report_headline", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["latest_task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_assets_workspace_id"), "research_assets", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_research_assets_created_by"), "research_assets", ["created_by"], unique=False)
    op.create_index(op.f("ix_research_assets_latest_task_id"), "research_assets", ["latest_task_id"], unique=False)

    op.create_table(
        "research_asset_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("research_asset_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("input_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("report_headline", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["research_asset_id"], ["research_assets.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("research_asset_id", "revision_number", name="uq_research_asset_revision_number"),
        sa.UniqueConstraint("task_id", name="uq_research_asset_revision_task_id"),
    )
    op.create_index(
        op.f("ix_research_asset_revisions_research_asset_id"),
        "research_asset_revisions",
        ["research_asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_research_asset_revisions_task_id"),
        "research_asset_revisions",
        ["task_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_research_asset_revisions_task_id"), table_name="research_asset_revisions")
    op.drop_index(
        op.f("ix_research_asset_revisions_research_asset_id"),
        table_name="research_asset_revisions",
    )
    op.drop_table("research_asset_revisions")

    op.drop_index(op.f("ix_research_assets_latest_task_id"), table_name="research_assets")
    op.drop_index(op.f("ix_research_assets_created_by"), table_name="research_assets")
    op.drop_index(op.f("ix_research_assets_workspace_id"), table_name="research_assets")
    op.drop_table("research_assets")
