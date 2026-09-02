"""Phase 10: llm_cache table.

Revision ID: e7f9a0b1c200
Revises: d6e7f8a9b001
Create Date: 2026-09-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e7f9a0b1c200"
down_revision = "d6e7f8a9b001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_cache",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("subject_id", sa.String(length=64), nullable=False),
        sa.Column("method_version", sa.String(length=8), nullable=False, server_default="v1"),
        sa.Column("score_computed_at", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("narration", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("kind", "subject_id", "method_version", "score_computed_at", "model", name="uq_llm_cache"),
    )


def downgrade() -> None:
    op.drop_table("llm_cache")
