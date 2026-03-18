"""Add runtime control columns for Stage B recovery actions."""

import sqlalchemy as sa

from alembic import op

revision = "20260318_0009"
down_revision = "20260318_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "control_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )
    op.add_column(
        "eval_runs",
        sa.Column(
            "control_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )


def downgrade() -> None:
    op.drop_column("eval_runs", "control_json")
    op.drop_column("tasks", "control_json")
