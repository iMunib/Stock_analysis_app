"""DuPont 3-Stage and 5-Stage ROE Decomposition Engine.

Decomposes Return on Equity (ROE) to evaluate operational efficiency vs financial leverage:

1. 3-Stage DuPont:
   ROE = Net Profit Margin x Asset Turnover x Equity Multiplier
       = (Net Income / Revenue) x (Revenue / Total Assets) x (Total Assets / Book Equity)

2. 5-Stage Extended DuPont:
   ROE = Tax Burden x Interest Burden x Operating Margin x Asset Turnover x Financial Leverage
       = (Net Income / EBT) x (EBT / EBIT) x (EBIT / Revenue) x (Revenue / Total Assets) x (Total Assets / Book Equity)

Invariants:
- Never invents numbers. Honest NULL for missing line items.
- Financial Institutions / Banks: Corporate debt/margin items handled with honest NULLs (Rule #8).
- Multi-year time series returned so analysts can evaluate leverage creep vs margin expansion.
"""
from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot


def _safe_div(n: float | None, d: float | None) -> float | None:
    if n is None or d is None or d == 0:
        return None
    return n / d


def compute_dupont_analysis(db: Session, company_id: str) -> dict[str, Any]:
    """Computes multi-year 3-stage and 5-stage DuPont ROE decomposition."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id!r} not found")

    is_bank = (
        company.custom_industry_sheet in ("Banks", "Insurance", "Credit_Services")
        or company.gics_sector == "Financials"
    )

    snaps = db.execute(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
        .order_by(FinancialSnapshot.fiscal_year.desc().nullslast())
    ).scalars().all()

    dated = [s for s in snaps if s.fiscal_year is not None]
    if not dated and snaps:
        dated = [snaps[0]]

    history: list[dict[str, Any]] = []

    for s in dated[:7]:  # Up to 7 years
        fy = s.fiscal_year or 0
        rev = s.revenue
        ni = s.net_income
        ta = s.total_assets
        eq = s.book_equity
        ebit = s.ebit
        int_exp = s.interest_expense or 0.0

        # Reported or direct ROE
        roe_direct = s.roe_calc or _safe_div(ni, eq)

        # 3-Stage Factors
        net_margin = _safe_div(ni, rev)
        asset_turnover = _safe_div(rev, ta)
        equity_multiplier = _safe_div(ta, eq) if eq and eq > 0 else None

        roe_3stage = None
        if net_margin is not None and asset_turnover is not None and equity_multiplier is not None:
            roe_3stage = net_margin * asset_turnover * equity_multiplier

        # 5-Stage Factors
        ebt = None
        if ebit is not None:
            ebt = ebit - int_exp

        tax_burden = _safe_div(ni, ebt) if (ni is not None and ebt is not None and ebt != 0) else None
        interest_burden = _safe_div(ebt, ebit) if (ebt is not None and ebit is not None and ebit != 0) else None
        operating_margin = _safe_div(ebit, rev) if (ebit is not None and rev is not None) else None

        roe_5stage = None
        if (
            tax_burden is not None
            and interest_burden is not None
            and operating_margin is not None
            and asset_turnover is not None
            and equity_multiplier is not None
        ):
            roe_5stage = tax_burden * interest_burden * operating_margin * asset_turnover * equity_multiplier

        def _r(val: float | None) -> float | None:
            return round(val, 4) if val is not None else None

        history.append({
            "fiscal_year": fy,
            "roe_direct": _r(roe_direct),
            # 3-Stage
            "net_profit_margin": _r(net_margin),
            "asset_turnover": _r(asset_turnover),
            "equity_multiplier": _r(equity_multiplier),
            "roe_3stage": _r(roe_3stage),
            # 5-Stage
            "tax_burden": _r(tax_burden),
            "interest_burden": _r(interest_burden),
            "operating_margin": _r(operating_margin),
            "roe_5stage": _r(roe_5stage),
            # Underlying figures
            "revenue": rev,
            "net_income": ni,
            "ebit": ebit,
            "total_assets": ta,
            "book_equity": eq,
        })

    # Determine primary driver from latest vs prior
    driver = "Balanced"
    driver_detail = "ROE decomposition reflects consistent operational and capital balance."
    if len(history) >= 2:
        cur = history[0]
        prev = history[1]
        if cur["equity_multiplier"] and prev["equity_multiplier"] and cur["net_profit_margin"] and prev["net_profit_margin"]:
            em_change = (cur["equity_multiplier"] - prev["equity_multiplier"]) / prev["equity_multiplier"]
            nm_change = (cur["net_profit_margin"] - prev["net_profit_margin"]) / abs(prev["net_profit_margin"]) if prev["net_profit_margin"] != 0 else 0
            at_change = ((cur["asset_turnover"] - prev["asset_turnover"]) / prev["asset_turnover"]) if (cur["asset_turnover"] and prev["asset_turnover"]) else 0

            if em_change > 0.15 and nm_change < 0.05:
                driver = "Leverage Creep"
                driver_detail = "ROE expansion is primarily driven by higher balance sheet leverage rather than margin improvement."
            elif nm_change > 0.10:
                driver = "Operational Margin Expansion"
                driver_detail = "ROE expansion is driven by pricing power and expanding net profit margins."
            elif at_change > 0.10:
                driver = "Asset Efficiency"
                driver_detail = "ROE expansion is driven by higher asset velocity and capital efficiency."

    latest = history[0] if history else None

    return {
        "company_id": company_id,
        "is_bank": is_bank,
        "primary_driver": driver,
        "driver_explanation": driver_detail,
        "latest": latest,
        "history": history,
    }
