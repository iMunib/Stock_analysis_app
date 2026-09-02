"""Analytical sprint WS2/WS3: Penman analysis table + Schilit forensic flags on TTM.

Revision ID: f4c8d9e2a603
Revises: e9f2a7b3c501
Create Date: 2026-09-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f4c8d9e2a603"
down_revision = "e9f2a7b3c501"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "financial_penman_analysis",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.String(length=32), sa.ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("period_type", sa.String(length=8), nullable=True),
        sa.Column("noa", sa.Float(), nullable=True),
        sa.Column("nfo", sa.Float(), nullable=True),
        sa.Column("nopat", sa.Float(), nullable=True),
        sa.Column("rnoa", sa.Float(), nullable=True),
        sa.Column("flev", sa.Float(), nullable=True),
        sa.Column("nbc", sa.Float(), nullable=True),
        sa.Column("roe_operational_spread", sa.Float(), nullable=True),
        sa.Column("identity_ok", sa.Boolean(), nullable=True),
        sa.Column("leverage_distortion", sa.Boolean(), nullable=True),
        sa.Column("exclusion", sa.String(length=64), nullable=True),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table("financial_snapshots_ttm") as batch:
        batch.add_column(sa.Column("dso", sa.Float(), nullable=True))
        batch.add_column(sa.Column("dso_spread", sa.Float(), nullable=True))
        batch.add_column(sa.Column("eqr", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("forensic_flags_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("financial_snapshots_ttm") as batch:
        batch.drop_column("forensic_flags_json")
        batch.drop_column("eqr")
        batch.drop_column("dso_spread")
        batch.drop_column("dso")

    op.drop_table("financial_penman_analysis")
