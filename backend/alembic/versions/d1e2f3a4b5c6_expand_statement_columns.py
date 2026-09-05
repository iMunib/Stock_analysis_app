"""expand_statement_columns

Revision ID: d1e2f3a4b5c6
Revises: c9d0e1f2a3b4
Create Date: 2026-09-03
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d1e2f3a4b5c6"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("financial_snapshots") as batch_op:
        batch_op.add_column(sa.Column("accounts_receivable", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("inventory", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("current_assets", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("current_liabilities", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("ppe_net", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("retained_earnings", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("stock_based_compensation", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("interest_income", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("financial_snapshots") as batch_op:
        batch_op.drop_column("accounts_receivable")
        batch_op.drop_column("inventory")
        batch_op.drop_column("current_assets")
        batch_op.drop_column("current_liabilities")
        batch_op.drop_column("ppe_net")
        batch_op.drop_column("retained_earnings")
        batch_op.drop_column("stock_based_compensation")
        batch_op.drop_column("interest_income")
