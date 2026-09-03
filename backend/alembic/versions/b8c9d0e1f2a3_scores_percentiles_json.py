"""Add percentiles_json to scores table (Master Directive WS5).

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-09-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("scores") as batch_op:
        batch_op.add_column(sa.Column("percentiles_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("scores") as batch_op:
        batch_op.drop_column("percentiles_json")
