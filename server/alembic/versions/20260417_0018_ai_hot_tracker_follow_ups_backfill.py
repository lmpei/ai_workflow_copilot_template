"""Backfill AI hot tracker follow_ups in saved records.

Revision ID: 20260417_0018
Revises: 20260409_0017
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260417_0018"
down_revision = "20260409_0017"
branch_labels = None
depends_on = None

_TABLE_NAME = "ai_frontier_research_records"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if _TABLE_NAME not in set(inspector.get_table_names()):
        return

    table = sa.table(
        _TABLE_NAME,
        sa.column("id", sa.String(length=36)),
        sa.column("source_set_json", sa.JSON()),
    )

    rows = bind.execute(sa.select(table.c.id, table.c.source_set_json)).all()
    for row in rows:
        source_set = row.source_set_json if isinstance(row.source_set_json, dict) else {}
        follow_ups = source_set.get("follow_ups")
        if isinstance(follow_ups, list):
            continue

        next_source_set = dict(source_set)
        next_source_set["follow_ups"] = []
        bind.execute(
            sa.update(table)
            .where(table.c.id == row.id)
            .values(source_set_json=next_source_set)
        )


def downgrade() -> None:
    # Historical records stay normalized; do not remove follow_ups keys on downgrade.
    return
