"""Add Stage E Job hiring workbench tables.

Revision ID: 20260328_0011
Revises: 20260328_0010
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260328_0011"
down_revision = "20260328_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_hiring_packets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("target_role", sa.String(length=255), nullable=True),
        sa.Column("target_role_key", sa.String(length=255), nullable=True),
        sa.Column("seniority", sa.String(length=100), nullable=True),
        sa.Column("latest_task_id", sa.String(length=36), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("latest_task_type", sa.String(length=100), nullable=False),
        sa.Column("latest_input_json", sa.JSON(), nullable=False),
        sa.Column("latest_result_json", sa.JSON(), nullable=False),
        sa.Column("latest_summary", sa.Text(), nullable=False),
        sa.Column("latest_recommended_outcome", sa.String(length=100), nullable=True),
        sa.Column("latest_evidence_status", sa.String(length=50), nullable=True),
        sa.Column("latest_fit_signal", sa.String(length=50), nullable=True),
        sa.Column("latest_shortlist_json", sa.JSON(), nullable=True),
        sa.Column("latest_next_steps_json", sa.JSON(), nullable=False),
        sa.Column("candidate_labels_json", sa.JSON(), nullable=False),
        sa.Column("comparison_history_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_hiring_packets_workspace_id", "job_hiring_packets", ["workspace_id"])
    op.create_index("ix_job_hiring_packets_created_by", "job_hiring_packets", ["created_by"])
    op.create_index("ix_job_hiring_packets_status", "job_hiring_packets", ["status"])
    op.create_index("ix_job_hiring_packets_target_role_key", "job_hiring_packets", ["target_role_key"])
    op.create_index("ix_job_hiring_packets_latest_task_id", "job_hiring_packets", ["latest_task_id"])

    op.create_table(
        "job_hiring_packet_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_hiring_packet_id", sa.String(length=36), sa.ForeignKey("job_hiring_packets.id"), nullable=False),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("event_kind", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("packet_status", sa.String(length=50), nullable=False),
        sa.Column("candidate_label", sa.String(length=255), nullable=True),
        sa.Column("target_role", sa.String(length=255), nullable=True),
        sa.Column("fit_signal", sa.String(length=50), nullable=True),
        sa.Column("evidence_status", sa.String(length=50), nullable=True),
        sa.Column("recommended_outcome", sa.String(length=100), nullable=True),
        sa.Column("comparison_task_ids_json", sa.JSON(), nullable=False),
        sa.Column("shortlist_entry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_id", name="uq_job_hiring_packet_event_task_id"),
    )
    op.create_index("ix_job_hiring_packet_events_job_hiring_packet_id", "job_hiring_packet_events", ["job_hiring_packet_id"])
    op.create_index("ix_job_hiring_packet_events_task_id", "job_hiring_packet_events", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_job_hiring_packet_events_task_id", table_name="job_hiring_packet_events")
    op.drop_index("ix_job_hiring_packet_events_job_hiring_packet_id", table_name="job_hiring_packet_events")
    op.drop_table("job_hiring_packet_events")

    op.drop_index("ix_job_hiring_packets_latest_task_id", table_name="job_hiring_packets")
    op.drop_index("ix_job_hiring_packets_target_role_key", table_name="job_hiring_packets")
    op.drop_index("ix_job_hiring_packets_status", table_name="job_hiring_packets")
    op.drop_index("ix_job_hiring_packets_created_by", table_name="job_hiring_packets")
    op.drop_index("ix_job_hiring_packets_workspace_id", table_name="job_hiring_packets")
    op.drop_table("job_hiring_packets")
