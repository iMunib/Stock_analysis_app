"""Ingest state machine, reporting currency, CIK, and filing type.

Revision ID: f8a1b2c3d400
Revises: e7f9a0b1c200
Create Date: 2026-09-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f8a1b2c3d400"
down_revision = "e7f9a0b1c200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # companies
    with op.batch_alter_table("companies") as batch_op:
        batch_op.add_column(sa.Column("cik", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reporting_currency", sa.String(length=8), nullable=True))
        batch_op.add_column(sa.Column("filing_type", sa.String(length=16), nullable=True))

    # jobs
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("step", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("company_id", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("error_code", sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_column("error_code")
        batch_op.drop_column("company_id")
        batch_op.drop_column("message")
        batch_op.drop_column("step")

    with op.batch_alter_table("companies") as batch_op:
        batch_op.drop_column("filing_type")
        batch_op.drop_column("reporting_currency")
        batch_op.drop_column("cik")
