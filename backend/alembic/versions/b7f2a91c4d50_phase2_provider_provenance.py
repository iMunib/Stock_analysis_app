"""Phase 2 schema: provider provenance + nullable quality flags.

Revision ID: b7f2a91c4d50
Revises: ccf1cb226400
Create Date: 2026-09-01
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b7f2a91c4d50"
down_revision = "ccf1cb226400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("financial_snapshots") as batch:
        batch.add_column(sa.Column("fetched_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("provider_as_of", sa.Date(), nullable=True))
    with op.batch_alter_table("data_quality_flags") as batch:
        batch.alter_column("company_id", existing_type=sa.String(length=32), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("data_quality_flags") as batch:
        batch.alter_column("company_id", existing_type=sa.String(length=32), nullable=False)
    with op.batch_alter_table("financial_snapshots") as batch:
        batch.drop_column("provider_as_of")
        batch.drop_column("fetched_at")
