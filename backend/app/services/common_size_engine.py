"""Koyfin-style Common-Size Financial Statement Engine (Master Directive WS2).

Standardizes income statements (normalized to Total Revenue) and balance sheets
(normalized to Total Assets) to allow cross-border, cross-scale comparisons.
Detects multi-year margin contraction and operating cost creep.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot


def compute_common_size(db: Session, company_id: str, years: int = 5) -> dict[str, Any]:
    """Generates multi-year common-size income statement and balance sheet with drift flags."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    # Fetch annual statements ordered chronologically
    snaps = db.execute(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
        .order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()

    dated = [s for s in snaps if s.fiscal_year is not None]
    seed = [s for s in snaps if s.fiscal_year is None]
    target_snaps = dated[-years:] if dated else seed

    income_statement: list[dict[str, Any]] = []
    balance_sheet: list[dict[str, Any]] = []
    om_history: list[tuple[int, float]] = []
    cost_history: list[tuple[int, float]] = []

    def _pct(num: float | None, denom: float | None) -> float | None:
        if num is None or denom is None or denom <= 0:
            return None
        return round((num / denom) * 100.0, 2)

    for s in target_snaps:
        fy = s.fiscal_year or (s.as_of_date.year if s.as_of_date else None)
        rev = s.revenue
        ta = s.total_assets

        # Income Statement items (% of Revenue)
        gp = s.gross_profit
        ebit = s.ebit
        ebitda = s.ebitda
        ni = s.net_income
        cfo = s.operating_cash_flow
        capex = s.capex
        fcf = s.fcf_calc if s.fcf_calc is not None else s.free_cash_flow

        # SG&A / OpEx proxy = Gross Profit - EBIT (when explicit SG&A not in base row)
        opex = (gp - ebit) if (gp is not None and ebit is not None) else None

        om_pct = _pct(ebit, rev)
        cost_pct = _pct(opex, rev)

        if fy is not None and om_pct is not None:
            om_history.append((fy, om_pct))
        if fy is not None and cost_pct is not None:
            cost_history.append((fy, cost_pct))

        income_statement.append({
            "fiscal_year": s.fiscal_year,
            "period_type": s.period_type,
            "currency": s.currency or company.currency,
            "revenue": {"raw": rev, "pct": 100.0 if rev and rev > 0 else None},
            "gross_profit": {"raw": gp, "pct": _pct(gp, rev)},
            "ebit": {"raw": ebit, "pct": om_pct},
            "ebitda": {"raw": ebitda, "pct": _pct(ebitda, rev)},
            "net_income": {"raw": ni, "pct": _pct(ni, rev)},
            "operating_cash_flow": {"raw": cfo, "pct": _pct(cfo, rev)},
            "capex": {"raw": capex, "pct": _pct(capex, rev)},
            "fcf": {"raw": fcf, "pct": _pct(fcf, rev)},
            "operating_expenses": {"raw": opex, "pct": cost_pct},
        })

        # Balance Sheet items (% of Total Assets)
        cash = s.cash_st_investments
        debt = s.total_debt
        tl = s.total_liabilities
        equity = s.book_equity
        net_debt = s.netdebt_calc

        balance_sheet.append({
            "fiscal_year": s.fiscal_year,
            "period_type": s.period_type,
            "currency": s.currency or company.currency,
            "total_assets": {"raw": ta, "pct": 100.0 if ta and ta > 0 else None},
            "cash_st_investments": {"raw": cash, "pct": _pct(cash, ta)},
            "total_debt": {"raw": debt, "pct": _pct(debt, ta)},
            "total_liabilities": {"raw": tl, "pct": _pct(tl, ta)},
            "book_equity": {"raw": equity, "pct": _pct(equity, ta)},
            "net_debt": {"raw": net_debt, "pct": _pct(net_debt, ta)},
        })

    # Multi-Year Margin Drift Detection
    flags: list[dict[str, Any]] = []

    # Check Operating Margin contraction (> 300 bps over up to 3-year span)
    if len(om_history) >= 2:
        for i in range(1, len(om_history)):
            curr_fy, curr_om = om_history[i]
            # check against prior periods up to 3 years back
            for j in range(max(0, i - 3), i):
                prev_fy, prev_om = om_history[j]
                change_bps = (curr_om - prev_om) * 100.0
                if change_bps < -300.0:  # declined by > 300 bps
                    flags.append({
                        "code": "MARGIN_CONTRACTION",
                        "severity": "warning",
                        "metric": "Operating Margin",
                        "from_year": prev_fy,
                        "to_year": curr_fy,
                        "change_bps": round(change_bps, 1),
                        "message": (
                            f"Operating margin contracted by {abs(round(change_bps, 1)):.0f} bps "
                            f"from {prev_om:.1f}% ({prev_fy}) to {curr_om:.1f}% ({curr_fy})."
                        ),
                    })
                    break  # one flag per current year is sufficient

    # Check Cost Creep (SG&A/OpEx / Revenue increased by > 200 bps over up to 3-year span)
    if len(cost_history) >= 2:
        for i in range(1, len(cost_history)):
            curr_fy, curr_cost = cost_history[i]
            for j in range(max(0, i - 3), i):
                prev_fy, prev_cost = cost_history[j]
                change_bps = (curr_cost - prev_cost) * 100.0
                if change_bps > 200.0:  # increased by > 200 bps
                    flags.append({
                        "code": "COST_CREEP",
                        "severity": "warning",
                        "metric": "Operating Expenses / Revenue",
                        "from_year": prev_fy,
                        "to_year": curr_fy,
                        "change_bps": round(change_bps, 1),
                        "message": (
                            f"Operating expenses grew {round(change_bps, 1):.0f} bps faster than revenue "
                            f"from {prev_cost:.1f}% ({prev_fy}) to {curr_cost:.1f}% ({curr_fy})."
                        ),
                    })
                    break

    return {
        "company_id": company_id,
        "currency": company.currency,
        "years_requested": years,
        "years_delivered": len(target_snaps),
        "income_statement_common_size": income_statement,
        "balance_sheet_common_size": balance_sheet,
        "margin_drift_flags": flags,
    }
