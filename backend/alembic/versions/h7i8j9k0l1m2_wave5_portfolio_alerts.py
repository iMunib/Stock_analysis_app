"""wave5 portfolio, journal, alerts

Revision ID: h7i8j9k0l1m2
Revises: 23317f57050f
Create Date: 2026-09-05
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = 'h7i8j9k0l1m2'
down_revision = ('23317f57050f', 'g1h2i3j4k5l6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('portfolio_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('account_type', sa.String(length=16), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('portfolio_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('company_id', sa.String(length=32), nullable=False),
        sa.Column('txn_type', sa.String(length=16), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price_per_share', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('txn_date', sa.Date(), nullable=False),
        sa.Column('fees', sa.Float(), nullable=True, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['portfolio_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('portfolio_transactions', schema=None) as batch_op:
        batch_op.create_index('ix_portfolio_txn_account', ['account_id'], unique=False)
        batch_op.create_index('ix_portfolio_txn_company', ['company_id'], unique=False)

    op.create_table('decision_journal',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_id', sa.String(length=32), nullable=False),
        sa.Column('account_id', sa.String(length=36), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('strategy_tag', sa.String(length=32), nullable=True),
        sa.Column('thesis', sa.Text(), nullable=True),
        sa.Column('kill_conditions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('decision_journal', schema=None) as batch_op:
        batch_op.create_index('ix_journal_company', ['company_id'], unique=False)

    op.create_table('alert_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_id', sa.String(length=32), nullable=True),
        sa.Column('rule_type', sa.String(length=32), nullable=False),
        sa.Column('params_json', sa.JSON(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('alert_rules', schema=None) as batch_op:
        batch_op.create_index('ix_alert_company', ['company_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('alert_rules', schema=None) as batch_op:
        batch_op.drop_index('ix_alert_company')
    op.drop_table('alert_rules')
    with op.batch_alter_table('decision_journal', schema=None) as batch_op:
        batch_op.drop_index('ix_journal_company')
    op.drop_table('decision_journal')
    with op.batch_alter_table('portfolio_transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_portfolio_txn_company')
        batch_op.drop_index('ix_portfolio_txn_account')
    op.drop_table('portfolio_transactions')
    op.drop_table('portfolio_accounts')
