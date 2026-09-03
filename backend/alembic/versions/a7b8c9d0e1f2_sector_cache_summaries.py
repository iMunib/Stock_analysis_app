"""Materialized sector summary cache for sub-25ms snapshot responses.

Revision ID: a7b8c9d0e1f2
Revises: f4c8d9e2a603
Create Date: 2026-09-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f4c8d9e2a603"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sector_cache_summaries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sector_name", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("company_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scored_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("median_composite", sa.Float(), nullable=True),
        sa.Column("median_pe", sa.Float(), nullable=True),
        sa.Column("median_pb", sa.Float(), nullable=True),
        sa.Column("median_roe", sa.Float(), nullable=True),
        sa.Column("signal_distribution_json", sa.JSON(), nullable=True),
        sa.Column("top_json", sa.JSON(), nullable=True),
        sa.Column("bottom_json", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("sector_name", "currency", name="uq_sector_cache_name_cur"),
    )
    op.create_index("ix_sector_cache_name", "sector_cache_summaries", ["sector_name"])


def downgrade() -> None:
    op.drop_index("ix_sector_cache_name", table_name="sector_cache_summaries")
    op.drop_table("sector_cache_summaries")
