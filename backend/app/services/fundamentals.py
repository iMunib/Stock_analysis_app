"""Map provider AnnualStatement rows onto financial_snapshots column names.

Pure functions - no network, no DB. NULL semantics preserved: absent facts stay
absent (never 0, never guessed).
"""
from __future__ import annotations

from app.providers.base import AnnualStatement

# AnnualStatement.fields (already canonical names) -> FinancialSnapshot attrs
_FIELD_TO_ATTR = {
    "Revenue": "revenue",
    "TopLine_Alt": "topline_alt",
    "Net_Income": "net_income",
    "Diluted_EPS": "diluted_eps",
    "Gross_Profit": "gross_profit",
    "Operating_Cash_Flow": "operating_cash_flow",
    "Capex": "capex",
    "Free_Cash_Flow": "free_cash_flow",
    "Total_Debt": "total_debt",
    "Cash_ST_Investments": "cash_st_investments",
    "Book_Equity": "book_equity",
    "Total_Assets": "total_assets",
    "Total_Liabilities": "total_liabilities",
    "EBIT": "ebit",
    "EBITDA": "ebitda",
    "Interest_Expense": "interest_expense",
    "Accounts_Receivable": "accounts_receivable",
    "Inventory": "inventory",
    "Current_Assets": "current_assets",
    "Current_Liabilities": "current_liabilities",
    "PPE_Net": "ppe_net",
    "Retained_Earnings": "retained_earnings",
    "Stock_Based_Compensation": "stock_based_compensation",
    "Interest_Income": "interest_income",
}

# Derived, only when both inputs exist (computed at ingest; NULL otherwise).
_DERIVED = {
    "FCF_Calc": ("operating_cash_flow", "capex"),
    "NetDebt_Calc": ("total_debt", "cash_st_investments"),
}


def apply_statement_to_snapshot(snap, stmt: AnnualStatement) -> list[str]:
    """Set snapshot attributes from a provider statement. Returns changed attrs.

    Never touches values that would become None (missing fact == no change).
    """
    changed: list[str] = []
    for field, value in stmt.fields.items():
        attr = _FIELD_TO_ATTR.get(field)
        if attr is None or value is None:
            continue
        try:
            fv = float(value)
        except (TypeError, ValueError):
            continue
        if fv != fv:  # NaN
            continue
        setattr(snap, attr, fv)
        changed.append(attr)

    ocf, capex = stmt.fields.get("Operating_Cash_Flow"), stmt.fields.get("Capex")
    if ocf is not None and capex is not None:
        snap.fcf_calc = float(ocf) - abs(float(capex))
        changed.append("fcf_calc")
    debt, cash = stmt.fields.get("Total_Debt"), stmt.fields.get("Cash_ST_Investments")
    if debt is not None and cash is not None:
        snap.netdebt_calc = float(debt) - float(cash)
        changed.append("netdebt_calc")

    snap.currency = stmt.currency or snap.currency
    snap.provider_as_of = stmt.period_end
    if stmt.period_end and not snap.as_of_date:
        snap.as_of_date = stmt.period_end
    stmt_fetched = getattr(stmt, "fetched_at", None)
    if stmt_fetched is not None:
        snap.fetched_at = stmt_fetched

    # Extract shares if provided in statement
    sh = stmt.fields.get("Common_Shares")
    if sh is not None and getattr(snap, "shares_snapshot", None) is None:
        try:
            snap.shares_snapshot = float(sh)
            changed.append("shares_snapshot")
        except (ValueError, TypeError):
            pass

    return changed


def compute_snapshot_ratios(snap, company) -> list[str]:
    """Compute ROE, ROA, GrossMargin, FCFMargin, PE, PB, EV/EBITDA, and MarketCap.

    If statement currency != price currency (e.g. BABA: CNY statements vs USD price):
    Price-based ratios (PE, PB, EV/EBITDA) stay None (currency mismatch).
    Non-price ratios (ROE, ROA, margins) are computed in native statement currency.
    """
    changed = []

    # 1. Statement-only ratios (same numerator and denominator currency)
    # ROE = Net_Income / Book_Equity
    if snap.net_income is not None and snap.book_equity is not None and snap.book_equity > 0:
        if snap.roe_calc is None:
            snap.roe_calc = float(snap.net_income) / float(snap.book_equity)
            changed.append("roe_calc")

    # ROA = Net_Income / Total_Assets
    if snap.net_income is not None and snap.total_assets is not None and snap.total_assets > 0:
        if snap.roa_calc is None:
            snap.roa_calc = float(snap.net_income) / float(snap.total_assets)
            changed.append("roa_calc")

    # Gross Profit derivation from Cost of Revenue if missing
    if snap.gross_profit is None and snap.revenue is not None and getattr(snap, "cost_of_revenue", None) is not None:
        snap.gross_profit = float(snap.revenue) - float(snap.cost_of_revenue)
        changed.append("gross_profit")

    # Gross Margin = Gross_Profit / Revenue
    if snap.gross_profit is not None and snap.revenue is not None and snap.revenue > 0:
        if snap.grossmargin_calc is None:
            snap.grossmargin_calc = float(snap.gross_profit) / float(snap.revenue)
            changed.append("grossmargin_calc")

    # EBITDA derivation from EBIT + D&A if missing
    if snap.ebitda is None and snap.ebit is not None and getattr(snap, "depreciation_amortization", None) is not None:
        snap.ebitda = float(snap.ebit) + float(snap.depreciation_amortization)
        changed.append("ebitda")


    # FCF Calc fallback
    if snap.fcf_calc is None:
        if snap.free_cash_flow is not None:
            snap.fcf_calc = float(snap.free_cash_flow)
            changed.append("fcf_calc")
        elif snap.operating_cash_flow is not None and snap.capex is not None:
            snap.fcf_calc = float(snap.operating_cash_flow) - abs(float(snap.capex))
            changed.append("fcf_calc")
        elif snap.operating_cash_flow is not None:
            snap.fcf_calc = float(snap.operating_cash_flow)
            changed.append("fcf_calc")

    # Net Debt Calc fallback
    if snap.netdebt_calc is None and snap.total_debt is not None and snap.cash_st_investments is not None:
        snap.netdebt_calc = float(snap.total_debt) - float(snap.cash_st_investments)
        changed.append("netdebt_calc")

    # FCF Margin = FCF_Calc / Revenue
    if snap.fcf_calc is not None and snap.revenue is not None and snap.revenue > 0:
        if snap.fcfmargin_calc is None:
            snap.fcfmargin_calc = float(snap.fcf_calc) / float(snap.revenue)
            changed.append("fcfmargin_calc")

    # 2. Currency check
    stmt_cur = (snap.currency or getattr(company, "reporting_currency", None) or "").strip().upper()
    price_cur = (snap.price_currency or getattr(company, "currency", None) or "").strip().upper()
    mismatch = bool(stmt_cur and price_cur and stmt_cur != price_cur)

    # Implied shares from net income and diluted EPS
    if snap.shares_snapshot is None and snap.diluted_eps and snap.net_income and snap.diluted_eps > 0 and snap.net_income > 0:
        snap.shares_snapshot = float(snap.net_income) / float(snap.diluted_eps)
        changed.append("shares_snapshot")

    # Price derivation if missing but market_cap & shares present
    if snap.price is None and snap.market_cap is not None and snap.shares_snapshot is not None and snap.shares_snapshot > 0:
        snap.price = float(snap.market_cap) / float(snap.shares_snapshot)
        if not snap.price_currency:
            snap.price_currency = company.currency or snap.currency or "USD"
        changed.append("price")

    # If currencies match, compute price-based multiples
    if not mismatch and snap.price is not None:
        # Market Cap = price * shares
        if snap.market_cap is None and snap.shares_snapshot is not None:
            snap.market_cap = float(snap.price) * float(snap.shares_snapshot)
            changed.append("market_cap")

        # PE = price / diluted_eps
        if snap.pe_calc is None and snap.diluted_eps is not None and snap.diluted_eps != 0:
            snap.pe_calc = float(snap.price) / float(snap.diluted_eps)
            changed.append("pe_calc")

        # PB = market_cap / book_equity
        if snap.pb_calc is None and snap.market_cap is not None and snap.book_equity is not None and snap.book_equity > 0:
            snap.pb_calc = float(snap.market_cap) / float(snap.book_equity)
            changed.append("pb_calc")

        # EV = market_cap + netdebt_calc
        if snap.ev_calc is None and snap.market_cap is not None and snap.netdebt_calc is not None:
            snap.ev_calc = float(snap.market_cap) + float(snap.netdebt_calc)
            changed.append("ev_calc")

        # EV / EBITDA
        if snap.ev_to_ebitda_calc is None and snap.ev_calc is not None and snap.ebitda is not None and snap.ebitda > 0:
            snap.ev_to_ebitda_calc = float(snap.ev_calc) / float(snap.ebitda)
            changed.append("ev_to_ebitda_calc")
    elif mismatch:
        # Cross-border currency mismatch: Price ratios stay None!
        if snap.pe_calc is not None:
            snap.pe_calc = None
            changed.append("pe_calc")
        if snap.pb_calc is not None:
            snap.pb_calc = None
            changed.append("pb_calc")
        if snap.ev_to_ebitda_calc is not None:
            snap.ev_to_ebitda_calc = None
            changed.append("ev_to_ebitda_calc")

    return changed


def statement_year(stmt: AnnualStatement) -> int | None:
    return stmt.fiscal_year


def sync_snapshot_to_3nf(db, snap, company=None):
    """Synchronize a FinancialSnapshot row into 3NF FinancialStatement and DerivedMetric."""
    from sqlalchemy import select
    from app.models import DerivedMetric, FinancialStatement

    # 1. FinancialStatement row
    year_filter = (
        FinancialStatement.fiscal_year == snap.fiscal_year
        if snap.fiscal_year is not None
        else FinancialStatement.fiscal_year.is_(None)
    )
    stmt_row = db.execute(
        select(FinancialStatement).where(
            FinancialStatement.company_id == snap.company_id,
            year_filter,
            FinancialStatement.period_type == snap.period_type,
        )
    ).scalar_one_or_none()
    if stmt_row is None:
        stmt_row = FinancialStatement(
            company_id=snap.company_id,
            fiscal_year=snap.fiscal_year,
            period_type=snap.period_type,
        )
        db.add(stmt_row)

    stmt_row.as_of_date = snap.as_of_date
    stmt_row.period_end = getattr(snap, "provider_as_of", None) or snap.as_of_date
    stmt_row.currency = snap.currency
    stmt_row.source = snap.source
    stmt_row.revenue = snap.revenue
    stmt_row.gross_profit = snap.gross_profit
    stmt_row.ebit = snap.ebit
    stmt_row.ebitda = snap.ebitda
    stmt_row.net_income = snap.net_income
    stmt_row.diluted_eps = snap.diluted_eps
    stmt_row.interest_expense = snap.interest_expense
    stmt_row.interest_income = getattr(snap, "interest_income", None)
    stmt_row.topline_alt = snap.topline_alt
    stmt_row.operating_cash_flow = snap.operating_cash_flow
    stmt_row.capex = snap.capex
    stmt_row.free_cash_flow = snap.free_cash_flow
    stmt_row.fcf_reported = snap.fcf_reported
    stmt_row.stock_based_compensation = getattr(snap, "stock_based_compensation", None)
    stmt_row.cash_st_investments = snap.cash_st_investments
    stmt_row.accounts_receivable = getattr(snap, "accounts_receivable", None)
    stmt_row.inventory = getattr(snap, "inventory", None)
    stmt_row.current_assets = getattr(snap, "current_assets", None)
    stmt_row.ppe_net = getattr(snap, "ppe_net", None)
    stmt_row.total_assets = snap.total_assets
    stmt_row.current_liabilities = getattr(snap, "current_liabilities", None)
    stmt_row.total_debt = snap.total_debt
    stmt_row.total_liabilities = snap.total_liabilities
    stmt_row.book_equity = snap.book_equity
    stmt_row.retained_earnings = getattr(snap, "retained_earnings", None)
    stmt_row.cet1_ratio = snap.cet1_ratio
    stmt_row.cet1_approach = snap.cet1_approach
    stmt_row.cet1_requirement_or_target = snap.cet1_requirement_or_target
    stmt_row.total_capital_ratio = snap.total_capital_ratio
    stmt_row.leverage_ratio = snap.leverage_ratio
    stmt_row.nim_fy2025 = snap.nim_fy2025
    stmt_row.nim_q4_2025 = snap.nim_q4_2025
    stmt_row.efficiency_ratio = snap.efficiency_ratio
    stmt_row.roaa = snap.roaa
    stmt_row.fetched_at = getattr(snap, "fetched_at", None)

    # 2. DerivedMetric row
    d_year_filter = (
        DerivedMetric.fiscal_year == snap.fiscal_year
        if snap.fiscal_year is not None
        else DerivedMetric.fiscal_year.is_(None)
    )
    derived_row = db.execute(
        select(DerivedMetric).where(
            DerivedMetric.company_id == snap.company_id,
            d_year_filter,
            DerivedMetric.period_type == snap.period_type,
        )
    ).scalar_one_or_none()
    if derived_row is None:
        derived_row = DerivedMetric(
            company_id=snap.company_id,
            fiscal_year=snap.fiscal_year,
            period_type=snap.period_type,
        )
        db.add(derived_row)

    derived_row.as_of_date = snap.as_of_date
    derived_row.price = snap.price
    derived_row.price_currency = snap.price_currency
    derived_row.price_asof = snap.price_asof
    derived_row.shares_snapshot = snap.shares_snapshot
    derived_row.market_cap = snap.market_cap
    derived_row.pe_calc = snap.pe_calc
    derived_row.pb_calc = snap.pb_calc
    derived_row.ev_calc = snap.ev_calc
    derived_row.ev_to_ebitda_calc = snap.ev_to_ebitda_calc
    derived_row.grossmargin_calc = snap.grossmargin_calc
    derived_row.fcfmargin_calc = snap.fcfmargin_calc
    derived_row.roe_calc = snap.roe_calc
    derived_row.roa_calc = snap.roa_calc
    derived_row.fcf_calc = snap.fcf_calc
    derived_row.netdebt_calc = snap.netdebt_calc
    derived_row.extraction_status = snap.extraction_status
    derived_row.fill_ok = snap.fill_ok
    derived_row.membership_flag = snap.membership_flag
    derived_row.computed_at = getattr(snap, "fetched_at", None)

    return stmt_row, derived_row
