"""normalize_3nf_schema

Revision ID: g1h2i3j4k5l6
Revises: d1e2f3a4b5c6
Create Date: 2026-09-03
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "g1h2i3j4k5l6"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create financial_statements
    op.create_table(
        "financial_statements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.String(length=32), sa.ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("period_type", sa.String(length=8), nullable=False, server_default="FY"),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("source", sa.String(length=256), nullable=True),
        sa.Column("filing_type", sa.String(length=16), nullable=True),
        # Income statement
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("gross_profit", sa.Float(), nullable=True),
        sa.Column("ebit", sa.Float(), nullable=True),
        sa.Column("ebitda", sa.Float(), nullable=True),
        sa.Column("net_income", sa.Float(), nullable=True),
        sa.Column("diluted_eps", sa.Float(), nullable=True),
        sa.Column("interest_expense", sa.Float(), nullable=True),
        sa.Column("interest_income", sa.Float(), nullable=True),
        sa.Column("topline_alt", sa.Float(), nullable=True),
        # Cash flow statement
        sa.Column("operating_cash_flow", sa.Float(), nullable=True),
        sa.Column("capex", sa.Float(), nullable=True),
        sa.Column("free_cash_flow", sa.Float(), nullable=True),
        sa.Column("fcf_reported", sa.Float(), nullable=True),
        sa.Column("stock_based_compensation", sa.Float(), nullable=True),
        # Balance sheet
        sa.Column("cash_st_investments", sa.Float(), nullable=True),
        sa.Column("accounts_receivable", sa.Float(), nullable=True),
        sa.Column("inventory", sa.Float(), nullable=True),
        sa.Column("current_assets", sa.Float(), nullable=True),
        sa.Column("ppe_net", sa.Float(), nullable=True),
        sa.Column("total_assets", sa.Float(), nullable=True),
        sa.Column("current_liabilities", sa.Float(), nullable=True),
        sa.Column("total_debt", sa.Float(), nullable=True),
        sa.Column("total_liabilities", sa.Float(), nullable=True),
        sa.Column("book_equity", sa.Float(), nullable=True),
        sa.Column("retained_earnings", sa.Float(), nullable=True),
        # Bank / insurer regulatory fields
        sa.Column("cet1_ratio", sa.Float(), nullable=True),
        sa.Column("cet1_approach", sa.String(length=256), nullable=True),
        sa.Column("cet1_requirement_or_target", sa.Float(), nullable=True),
        sa.Column("total_capital_ratio", sa.Float(), nullable=True),
        sa.Column("leverage_ratio", sa.Float(), nullable=True),
        sa.Column("nim_fy2025", sa.Float(), nullable=True),
        sa.Column("nim_q4_2025", sa.Float(), nullable=True),
        sa.Column("efficiency_ratio", sa.Float(), nullable=True),
        sa.Column("roaa", sa.Float(), nullable=True),
        # Metadata
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("company_id", "fiscal_year", "period_type", name="uq_financial_statements_company_year_period"),
    )
    op.create_index("ix_financial_statements_company_year", "financial_statements", ["company_id", "fiscal_year"])

    # 2. Create derived_metrics
    op.create_table(
        "derived_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.String(length=32), sa.ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("period_type", sa.String(length=8), nullable=False, server_default="FY"),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        # Price and market
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("price_currency", sa.String(length=8), nullable=True),
        sa.Column("price_asof", sa.String(length=32), nullable=True),
        sa.Column("shares_snapshot", sa.Float(), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        # Valuation ratios
        sa.Column("pe_calc", sa.Float(), nullable=True),
        sa.Column("pb_calc", sa.Float(), nullable=True),
        sa.Column("ev_calc", sa.Float(), nullable=True),
        sa.Column("ev_to_ebitda_calc", sa.Float(), nullable=True),
        # Profitability ratios
        sa.Column("grossmargin_calc", sa.Float(), nullable=True),
        sa.Column("fcfmargin_calc", sa.Float(), nullable=True),
        sa.Column("roe_calc", sa.Float(), nullable=True),
        sa.Column("roa_calc", sa.Float(), nullable=True),
        sa.Column("roic_calc", sa.Float(), nullable=True),
        # Cash & leverage
        sa.Column("fcf_calc", sa.Float(), nullable=True),
        sa.Column("netdebt_calc", sa.Float(), nullable=True),
        # Forensic & growth
        sa.Column("altman_z", sa.Float(), nullable=True),
        sa.Column("beneish_m_score", sa.Float(), nullable=True),
        sa.Column("sloan_accrual_ratio", sa.Float(), nullable=True),
        sa.Column("revenue_cagr_3y", sa.Float(), nullable=True),
        sa.Column("revenue_cagr_5y", sa.Float(), nullable=True),
        sa.Column("eps_cagr_3y", sa.Float(), nullable=True),
        sa.Column("eps_cagr_5y", sa.Float(), nullable=True),
        sa.Column("fcf_cagr_5y", sa.Float(), nullable=True),
        # Quality & provenance
        sa.Column("extraction_status", sa.String(length=32), nullable=True),
        sa.Column("fill_ok", sa.String(length=8), nullable=True),
        sa.Column("membership_flag", sa.String(length=64), nullable=True),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("company_id", "fiscal_year", "period_type", name="uq_derived_metrics_company_year_period"),
    )
    op.create_index("ix_derived_metrics_company_year", "derived_metrics", ["company_id", "fiscal_year"])

    # 3. Create peer_benchmarks
    op.create_table(
        "peer_benchmarks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("peer_group_name", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("metric_name", sa.String(length=32), nullable=False),
        sa.Column("p10", sa.Float(), nullable=True),
        sa.Column("p25", sa.Float(), nullable=True),
        sa.Column("median", sa.Float(), nullable=True),
        sa.Column("p75", sa.Float(), nullable=True),
        sa.Column("p90", sa.Float(), nullable=True),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("peer_group_name", "currency", "metric_name", name="uq_peer_benchmarks_group_cur_metric"),
    )
    op.create_index("ix_peer_benchmarks_group", "peer_benchmarks", ["peer_group_name"])

    # 4. Migrate existing data from financial_snapshots into financial_statements & derived_metrics
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT OR IGNORE INTO financial_statements (
            company_id, fiscal_year, period_type, as_of_date, period_end, currency, source,
            revenue, gross_profit, ebit, ebitda, net_income, diluted_eps, interest_expense, interest_income, topline_alt,
            operating_cash_flow, capex, free_cash_flow, fcf_reported, stock_based_compensation,
            cash_st_investments, accounts_receivable, inventory, current_assets, ppe_net, total_assets,
            current_liabilities, total_debt, total_liabilities, book_equity, retained_earnings,
            cet1_ratio, cet1_approach, cet1_requirement_or_target, total_capital_ratio, leverage_ratio,
            nim_fy2025, nim_q4_2025, efficiency_ratio, roaa, fetched_at
        )
        SELECT
            company_id, fiscal_year, period_type, as_of_date, provider_as_of, currency, source,
            revenue, gross_profit, ebit, ebitda, net_income, diluted_eps, interest_expense, interest_income, topline_alt,
            operating_cash_flow, capex, free_cash_flow, fcf_reported, stock_based_compensation,
            cash_st_investments, accounts_receivable, inventory, current_assets, ppe_net, total_assets,
            current_liabilities, total_debt, total_liabilities, book_equity, retained_earnings,
            cet1_ratio, cet1_approach, cet1_requirement_or_target, total_capital_ratio, leverage_ratio,
            nim_fy2025, nim_q4_2025, efficiency_ratio, roaa, fetched_at
        FROM financial_snapshots;
    """))

    conn.execute(sa.text("""
        INSERT OR IGNORE INTO derived_metrics (
            company_id, fiscal_year, period_type, as_of_date,
            price, price_currency, price_asof, shares_snapshot, market_cap,
            pe_calc, pb_calc, ev_calc, ev_to_ebitda_calc,
            grossmargin_calc, fcfmargin_calc, roe_calc, roa_calc,
            fcf_calc, netdebt_calc,
            extraction_status, fill_ok, membership_flag, computed_at
        )
        SELECT
            company_id, fiscal_year, period_type, as_of_date,
            price, price_currency, price_asof, shares_snapshot, market_cap,
            pe_calc, pb_calc, ev_calc, ev_to_ebitda_calc,
            grossmargin_calc, fcfmargin_calc, roe_calc, roa_calc,
            fcf_calc, netdebt_calc,
            extraction_status, fill_ok, membership_flag, fetched_at
        FROM financial_snapshots;
    """))


def downgrade() -> None:
    op.drop_index("ix_peer_benchmarks_group", table_name="peer_benchmarks")
    op.drop_table("peer_benchmarks")
    op.drop_index("ix_derived_metrics_company_year", table_name="derived_metrics")
    op.drop_table("derived_metrics")
    op.drop_index("ix_financial_statements_company_year", table_name="financial_statements")
    op.drop_table("financial_statements")
