"""Phase 3 schema: scores + halal_flags.

Revision ID: c3d4e5f6a780
Revises: b7f2a91c4d50
Create Date: 2026-09-01
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a780"
down_revision = "b7f2a91c4d50"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scores",
        sa.Column("company_id", sa.String(length=32), primary_key=True),
        sa.Column("as_of_fy", sa.Integer(), nullable=True),
        sa.Column("composite", sa.Float(), nullable=True),
        sa.Column("quality", sa.Float(), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("growth", sa.Float(), nullable=True),
        sa.Column("risk", sa.Float(), nullable=True),
        sa.Column("coverage", sa.Integer(), nullable=True),
        sa.Column("signal", sa.String(length=24), nullable=True),
        sa.Column("peer_set_type", sa.String(length=32), nullable=True),
        sa.Column("peer_n", sa.Integer(), nullable=True),
        sa.Column("peer_rank", sa.Integer(), nullable=True),
        sa.Column("method_version", sa.String(length=8), nullable=False, server_default="v1"),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.Column("inputs_json", sa.JSON(), nullable=True),
    )
    op.create_table(
        "halal_flags",
        sa.Column("company_id", sa.String(length=32), primary_key=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("tests_json", sa.JSON(), nullable=True),
        sa.Column("method", sa.String(length=24), nullable=False, server_default="aaoifi_style_v1"),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("halal_flags")
    op.drop_table("scores")
