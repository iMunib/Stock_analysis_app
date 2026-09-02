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
    return changed


def statement_year(stmt: AnnualStatement) -> int | None:
    return stmt.fiscal_year
