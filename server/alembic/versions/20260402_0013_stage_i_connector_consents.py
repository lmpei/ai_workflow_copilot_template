"""Add Stage I workspace connector consent table.

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
    op.create_table(
        "workspace_connector_consents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("connector_id", sa.String(length=100), nullable=False),
        sa.Column("granted_by", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("consent_note", sa.Text(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "workspace_id",
            "connector_id",
            name="uq_workspace_connector_consents_workspace_connector",
        ),
    )
    op.create_index(
        "ix_workspace_connector_consents_workspace_id",
        "workspace_connector_consents",
        ["workspace_id"],
    )
    op.create_index(
        "ix_workspace_connector_consents_connector_id",
        "workspace_connector_consents",
        ["connector_id"],
    )
    op.create_index(
        "ix_workspace_connector_consents_granted_by",
        "workspace_connector_consents",
        ["granted_by"],
    )
    op.create_index(
        "ix_workspace_connector_consents_status",
        "workspace_connector_consents",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_connector_consents_status", table_name="workspace_connector_consents")
    op.drop_index("ix_workspace_connector_consents_granted_by", table_name="workspace_connector_consents")
    op.drop_index("ix_workspace_connector_consents_connector_id", table_name="workspace_connector_consents")
    op.drop_index("ix_workspace_connector_consents_workspace_id", table_name="workspace_connector_consents")
    op.drop_table("workspace_connector_consents")
