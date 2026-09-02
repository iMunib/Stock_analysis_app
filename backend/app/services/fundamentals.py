"""Map provider AnnualStatement rows onto financial_snapshots column names.

Pure functions — no network, no DB. NULL semantics preserved: absent facts stay
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

    # Gross Margin = Gross_Profit / Revenue
    if snap.gross_profit is not None and snap.revenue is not None and snap.revenue > 0:
        if snap.grossmargin_calc is None:
            snap.grossmargin_calc = float(snap.gross_profit) / float(snap.revenue)
            changed.append("grossmargin_calc")

    # FCF Margin = FCF_Calc / Revenue
    if snap.fcf_calc is not None and snap.revenue is not None and snap.revenue > 0:
        if snap.fcfmargin_calc is None:
            snap.fcfmargin_calc = float(snap.fcf_calc) / float(snap.revenue)
            changed.append("fcfmargin_calc")

    # 2. Currency check
    stmt_cur = (snap.currency or getattr(company, "reporting_currency", None) or "").strip().upper()
    price_cur = (snap.price_currency or getattr(company, "currency", None) or "").strip().upper()
    mismatch = bool(stmt_cur and price_cur and stmt_cur != price_cur)

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
