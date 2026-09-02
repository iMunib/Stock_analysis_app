"""Trust sprint B+C: ROIC denominator diagnostics and valuation provenance.

Revision ID: e9f2a7b3c501
Revises: 23317f57050f
Create Date: 2026-09-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e9f2a7b3c501"
down_revision = "23317f57050f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("financial_snapshots_ttm") as batch:
        batch.add_column(sa.Column("invested_capital_to_assets", sa.Float(), nullable=True))
        batch.add_column(sa.Column("roic_interpretation", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("roic_confidence", sa.String(length=8), nullable=True))
        batch.add_column(sa.Column("roic_warning_reason", sa.String(length=64), nullable=True))

    with op.batch_alter_table("valuation_reverse_dcf") as batch:
        batch.add_column(sa.Column("price_as_of", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("market_cap_as_of", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("enterprise_value_as_of", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("baseline_fcf_period_end", sa.Date(), nullable=True))
        batch.add_column(sa.Column("baseline_fcf_basis", sa.String(length=8), nullable=True))
        batch.add_column(
            sa.Column(
                "valuation_computed_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("valuation_reverse_dcf") as batch:
        batch.drop_column("valuation_computed_at")
        batch.drop_column("baseline_fcf_basis")
        batch.drop_column("baseline_fcf_period_end")
        batch.drop_column("enterprise_value_as_of")
        batch.drop_column("market_cap_as_of")
        batch.drop_column("price_as_of")

    with op.batch_alter_table("financial_snapshots_ttm") as batch:
        batch.drop_column("roic_warning_reason")
        batch.drop_column("roic_confidence")
        batch.drop_column("roic_interpretation")
        batch.drop_column("invested_capital_to_assets")
