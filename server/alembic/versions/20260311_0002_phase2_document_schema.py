"""Add document chunk and embedding mapping tables."""

import sqlalchemy as sa

from alembic import op

revision = "20260311_0002"
down_revision = "20260308_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )
    op.create_index(
        op.f("ix_document_chunks_document_id"),
        "document_chunks",
        ["document_id"],
        unique=False,
    )

    op.create_table(
        "embeddings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_chunk_id", sa.String(length=36), nullable=False),
        sa.Column("vector_store_id", sa.String(length=255), nullable=False),
        sa.Column("collection_name", sa.String(length=255), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_chunk_id"], ["document_chunks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_chunk_id",
            "collection_name",
            "embedding_model",
            name="uq_chunk_collection_model",
        ),
        sa.UniqueConstraint("vector_store_id"),
    )
    op.create_index(
        op.f("ix_embeddings_document_chunk_id"),
        "embeddings",
        ["document_chunk_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_embeddings_document_chunk_id"), table_name="embeddings")
    op.drop_table("embeddings")
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_table("document_chunks")
