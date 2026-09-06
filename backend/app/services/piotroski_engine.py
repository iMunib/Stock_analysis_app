"""Piotroski F-Score Fundamental Accounting Engine.

Implements the classic 9-test fundamental framework from Joseph Piotroski (2000):
"Value Investing: The Use of Historical Financial Statement Data to Separate
Winners from Losers", Journal of Accounting Research.

Separates financial health into 3 distinct operational dimensions:
1. Profitability (4 tests: ROA > 0, CFO > 0, Delta ROA > 0, CFO > NI accruals).
2. Leverage, Liquidity & Dilution (3 tests: Leverage Down, Current Ratio Up, No Dilution).
3. Operating Efficiency (2 tests: Gross Margin Up, Asset Turnover Up).

Invariants:
- Never invents numbers. Missing inputs -> test is None (omitted from denominator or flagged).
- Banks / Financial Institutions: Tests depending on corporate debt or gross margin
  return None per Rule #8.
- Native currency values only: never cross-converts currencies.
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


def compute_piotroski_f_score(db: Session, company_id: str) -> dict[str, Any]:
    """Computes the full 9-point Piotroski F-Score breakdown for a company."""
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
    cur: FinancialSnapshot | None = dated[0] if dated else (snaps[0] if snaps else None)
    prior: FinancialSnapshot | None = dated[1] if len(dated) >= 2 else None

    if cur is None:
        return {
            "company_id": company_id,
            "f_score": 0,
            "f_possible": 0,
            "signal": "Insufficient Data",
            "interpretation": "No financial statements available for scoring.",
            "tests": {},
            "categories": {},
        }

    fy_cur = cur.fiscal_year
    fy_prior = prior.fiscal_year if prior else None

    # Helper to register tests
    results: dict[str, dict[str, Any]] = {}
    used = 0
    possible = 0

    def add_test(
        key: str,
        name: str,
        category: str,
        passed: bool | None,
        val_cur: float | None,
        val_prior: float | None,
        description: str,
    ):
        nonlocal used, possible
        if passed is not None:
            possible += 1
            if passed:
                used += 1
        results[key] = {
            "name": name,
            "category": category,
            "passed": passed,
            "current_value": round(val_cur, 4) if isinstance(val_cur, float) else val_cur,
            "prior_value": round(val_prior, 4) if isinstance(val_prior, float) else val_prior,
            "description": description,
        }

    # -------------------------------------------------------------------------
    # Group 1: Profitability (4 tests)
    # -------------------------------------------------------------------------
    # 1. ROA > 0
    roa_cur = _safe_div(cur.net_income, cur.total_assets)
    roa_pass = (roa_cur > 0) if roa_cur is not None else ((cur.net_income > 0) if cur.net_income is not None else None)
    add_test(
        "roa_positive",
        "Positive Return on Assets",
        "Profitability",
        roa_pass,
        roa_cur,
        None,
        "Net income is positive relative to total assets.",
    )

    # 2. Operating Cash Flow > 0
    cfo_pass = (cur.operating_cash_flow > 0) if cur.operating_cash_flow is not None else None
    add_test(
        "cfo_positive",
        "Positive Operating Cash Flow",
        "Profitability",
        cfo_pass,
        cur.operating_cash_flow,
        None,
        "Operating cash flow is positive for the fiscal year.",
    )

    # 3. Delta ROA > 0
    roa_prior = _safe_div(prior.net_income, prior.total_assets) if prior else None
    delta_roa_pass = (roa_cur > roa_prior) if (roa_cur is not None and roa_prior is not None) else None
    add_test(
        "delta_roa",
        "ROA Expansion",
        "Profitability",
        delta_roa_pass,
        roa_cur,
        roa_prior,
        "Current year ROA is higher than prior year ROA.",
    )

    # 4. Quality of Accruals: CFO > Net Income
    accrual_pass = (
        (cur.operating_cash_flow > cur.net_income)
        if (cur.operating_cash_flow is not None and cur.net_income is not None)
        else None
    )
    add_test(
        "quality_of_accruals",
        "Cash Generation > Net Income",
        "Profitability",
        accrual_pass,
        cur.operating_cash_flow,
        cur.net_income,
        "Operating cash flow exceeds net income (low accruals / honest accounting).",
    )

    # -------------------------------------------------------------------------
    # Group 2: Leverage, Liquidity & Source of Funds (3 tests)
    # -------------------------------------------------------------------------
    # 5. Leverage Down: Total Debt / Total Assets in current < prior
    if is_bank:
        add_test(
            "leverage_down",
            "Decreased Leverage",
            "Leverage & Liquidity",
            None,
            None,
            None,
            "N/A: Financial institution regulatory capital model (Rule #8).",
        )
    else:
        lev_cur = _safe_div(cur.total_debt, cur.total_assets)
        lev_prior = _safe_div(prior.total_debt, prior.total_assets) if prior else None
        lev_pass = (lev_cur < lev_prior) if (lev_cur is not None and lev_prior is not None) else None
        add_test(
            "leverage_down",
            "Decreased Leverage",
            "Leverage & Liquidity",
            lev_pass,
            lev_cur,
            lev_prior,
            "Long-term debt to total assets decreased compared to prior year.",
        )

    # 6. Current Ratio Up: Current Assets / Current Liabilities
    cr_cur = _safe_div(cur.current_assets, cur.current_liabilities)
    cr_prior = _safe_div(prior.current_assets, prior.current_liabilities) if prior else None
    if cr_cur is not None and cr_prior is not None:
        cr_pass = cr_cur > cr_prior
    else:
        cr_pass = None
    add_test(
        "current_ratio_up",
        "Liquidity Improvement",
        "Leverage & Liquidity",
        cr_pass,
        cr_cur,
        cr_prior,
        "Current ratio (liquidity) improved over the prior year.",
    )

    # 7. No Dilution: Diluted shares current <= prior
    sh_cur = cur.shares_snapshot
    sh_prior = prior.shares_snapshot if prior else None
    dilution_pass = (sh_cur <= sh_prior) if (sh_cur is not None and sh_prior is not None) else None
    add_test(
        "no_dilution",
        "Zero Share Dilution",
        "Leverage & Liquidity",
        dilution_pass,
        sh_cur,
        sh_prior,
        "Shares outstanding did not increase (no shareholder dilution).",
    )

    # -------------------------------------------------------------------------
    # Group 3: Operating Efficiency (2 tests)
    # -------------------------------------------------------------------------
    # 8. Delta Gross Margin > 0
    if is_bank:
        add_test(
            "gross_margin_up",
            "Gross Margin Expansion",
            "Operating Efficiency",
            None,
            None,
            None,
            "N/A: Financial institution without gross profit line item (Rule #8).",
        )
    else:
        gm_cur = cur.grossmargin_calc or _safe_div(cur.gross_profit, cur.revenue)
        gm_prior = (prior.grossmargin_calc or _safe_div(prior.gross_profit, prior.revenue)) if prior else None
        gm_pass = (gm_cur > gm_prior) if (gm_cur is not None and gm_prior is not None) else None
        add_test(
            "gross_margin_up",
            "Gross Margin Expansion",
            "Operating Efficiency",
            gm_pass,
            gm_cur,
            gm_prior,
            "Gross profit margin expanded compared to the previous fiscal year.",
        )

    # 9. Delta Asset Turnover > 0: Revenue / Total Assets
    at_cur = _safe_div(cur.revenue, cur.total_assets)
    at_prior = _safe_div(prior.revenue, prior.total_assets) if prior else None
    at_pass = (at_cur > at_prior) if (at_cur is not None and at_prior is not None) else None
    add_test(
        "asset_turnover_up",
        "Asset Turnover Acceleration",
        "Operating Efficiency",
        at_pass,
        at_cur,
        at_prior,
        "Revenue per dollar of assets increased, demonstrating greater efficiency.",
    )

    # Categorize tests
    categories = {
        "profitability": [t for t in results.values() if t["category"] == "Profitability"],
        "leverage_liquidity": [t for t in results.values() if t["category"] == "Leverage & Liquidity"],
        "efficiency": [t for t in results.values() if t["category"] == "Operating Efficiency"],
    }

    # Signal & interpretation
    ratio = (used / possible) if possible > 0 else 0.0
    if possible >= 7:
        if used >= 8:
            signal = "Strong"
            interp = "Exceptional fundamental health and operational turnaround momentum."
        elif used >= 5:
            signal = "Moderate"
            interp = "Mixed fundamental trajectory; some operational or balance sheet headwinds."
        else:
            signal = "Weak"
            interp = "Weakening fundamental health; heightened risk of value trap or deterioration."
    else:
        if ratio >= 0.75:
            signal = "Strong"
            interp = f"Strong performance on available tests ({used}/{possible})."
        elif ratio >= 0.50:
            signal = "Moderate"
            interp = f"Moderate performance on available tests ({used}/{possible})."
        else:
            signal = "Weak"
            interp = f"Weak performance across available tests ({used}/{possible})."

    return {
        "company_id": company_id,
        "fiscal_year": fy_cur,
        "prior_fiscal_year": fy_prior,
        "f_score": used,
        "f_possible": possible,
        "signal": signal,
        "interpretation": interp,
        "is_bank": is_bank,
        "tests": results,
        "categories": categories,
    }
