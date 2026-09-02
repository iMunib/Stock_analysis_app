"""Phase 10: Forensic Accounting, Reverse DCF, TTM snapshots, Screener Presets, and soft deletion.

Revision ID: a1b2c3d4e5f6
Revises: f8a1b2c3d400
Create Date: 2026-09-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "f8a1b2c3d400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add is_deleted to companies
    with op.batch_alter_table("companies") as batch_op:
        batch_op.add_column(sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))

    # 2. Table: financial_snapshots_ttm
    op.create_table(
        "financial_snapshots_ttm",
        sa.Column("company_id", sa.String(length=32), sa.ForeignKey("companies.company_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        sa.Column("quarter_count", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("operating_income", sa.Float(), nullable=True),
        sa.Column("net_income", sa.Float(), nullable=True),
        sa.Column("diluted_shares", sa.Float(), nullable=True),
        sa.Column("operating_cash_flow", sa.Float(), nullable=True),
        sa.Column("capex", sa.Float(), nullable=True),
        sa.Column("fcf", sa.Float(), nullable=True),
        sa.Column("nopat", sa.Float(), nullable=True),
        sa.Column("invested_capital", sa.Float(), nullable=True),
        sa.Column("roic", sa.Float(), nullable=True),
        sa.Column("fcf_yield", sa.Float(), nullable=True),
        sa.Column("ev_ebitda", sa.Float(), nullable=True),
        sa.Column("pe_ratio", sa.Float(), nullable=True),
        sa.Column("sloan_accrual_ratio", sa.Float(), nullable=True),
        sa.Column("cash_conversion_ratio", sa.Float(), nullable=True),
        sa.Column("is_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
    )

    # 3. Table: valuation_reverse_dcf
    op.create_table(
        "valuation_reverse_dcf",
        sa.Column("company_id", sa.String(length=32), sa.ForeignKey("companies.company_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.Column("current_share_price", sa.Float(), nullable=True),
        sa.Column("diluted_shares", sa.Float(), nullable=True),
        sa.Column("net_debt", sa.Float(), nullable=True),
        sa.Column("baseline_fcf", sa.Float(), nullable=True),
        sa.Column("terminal_growth_rate", sa.Float(), nullable=False, server_default="0.025"),
        sa.Column("wacc", sa.Float(), nullable=False, server_default="0.09"),
        sa.Column("market_implied_growth_10y", sa.Float(), nullable=True),
        sa.Column("historical_5y_cagr", sa.Float(), nullable=True),
        sa.Column("expectations_gap", sa.Float(), nullable=True),
        sa.Column("sensitivity_matrix_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="converged"),
    )

    # 4. Table: screener_presets
    op.create_table(
        "screener_presets",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("criteria_json", sa.JSON(), nullable=False),
        sa.Column("is_system_preset", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("screener_presets")
    op.drop_table("valuation_reverse_dcf")
    op.drop_table("financial_snapshots_ttm")
    with op.batch_alter_table("companies") as batch_op:
        batch_op.drop_column("is_deleted")
