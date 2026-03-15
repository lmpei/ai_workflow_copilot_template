"""Add Phase 4 evaluation dataset and result tables."""

import sqlalchemy as sa

from alembic import op

revision = "20260314_0005"
down_revision = "20260314_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "eval_datasets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("eval_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_eval_datasets_workspace_id"),
        "eval_datasets",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(op.f("ix_eval_datasets_name"), "eval_datasets", ["name"], unique=False)
    op.create_index(
        op.f("ix_eval_datasets_eval_type"),
        "eval_datasets",
        ["eval_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_eval_datasets_created_by"),
        "eval_datasets",
        ["created_by"],
        unique=False,
    )

    op.create_table(
        "eval_cases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("case_index", sa.Integer(), nullable=False),
        sa.Column("input_json", sa.JSON(), nullable=False),
        sa.Column("expected_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["eval_datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id", "case_index", name="uq_eval_case_dataset_index"),
    )
    op.create_index(op.f("ix_eval_cases_dataset_id"), "eval_cases", ["dataset_id"], unique=False)

    op.create_table(
        "eval_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("eval_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["dataset_id"], ["eval_datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_eval_runs_workspace_id"),
        "eval_runs",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(op.f("ix_eval_runs_dataset_id"), "eval_runs", ["dataset_id"], unique=False)
    op.create_index(op.f("ix_eval_runs_eval_type"), "eval_runs", ["eval_type"], unique=False)
    op.create_index(op.f("ix_eval_runs_status"), "eval_runs", ["status"], unique=False)
    op.create_index(op.f("ix_eval_runs_created_by"), "eval_runs", ["created_by"], unique=False)

    op.create_table(
        "eval_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("eval_run_id", sa.String(length=36), nullable=False),
        sa.Column("eval_case_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("output_json", sa.JSON(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["eval_run_id"], ["eval_runs.id"]),
        sa.ForeignKeyConstraint(["eval_case_id"], ["eval_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_eval_results_eval_run_id"),
        "eval_results",
        ["eval_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_eval_results_eval_case_id"),
        "eval_results",
        ["eval_case_id"],
        unique=False,
    )
    op.create_index(op.f("ix_eval_results_status"), "eval_results", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_eval_results_status"), table_name="eval_results")
    op.drop_index(op.f("ix_eval_results_eval_case_id"), table_name="eval_results")
    op.drop_index(op.f("ix_eval_results_eval_run_id"), table_name="eval_results")
    op.drop_table("eval_results")

    op.drop_index(op.f("ix_eval_runs_created_by"), table_name="eval_runs")
    op.drop_index(op.f("ix_eval_runs_status"), table_name="eval_runs")
    op.drop_index(op.f("ix_eval_runs_eval_type"), table_name="eval_runs")
    op.drop_index(op.f("ix_eval_runs_dataset_id"), table_name="eval_runs")
    op.drop_index(op.f("ix_eval_runs_workspace_id"), table_name="eval_runs")
    op.drop_table("eval_runs")

    op.drop_index(op.f("ix_eval_cases_dataset_id"), table_name="eval_cases")
    op.drop_table("eval_cases")

    op.drop_index(op.f("ix_eval_datasets_created_by"), table_name="eval_datasets")
    op.drop_index(op.f("ix_eval_datasets_eval_type"), table_name="eval_datasets")
    op.drop_index(op.f("ix_eval_datasets_name"), table_name="eval_datasets")
    op.drop_index(op.f("ix_eval_datasets_workspace_id"), table_name="eval_datasets")
    op.drop_table("eval_datasets")
