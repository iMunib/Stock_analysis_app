"""Specialized Banking & Financial Institution Model (Phase 3 Master Directive).

Strict adherence to AGENTS.md rules:
- Banks/insurers: corporate debt, FCF, and gross profit remain NULL/blank.
- Never mix CAD and USD money; compute unitless financial ratios.

Metrics:
1. Return on Average Assets (ROAA % = Net Income / Avg Total Assets * 100)
2. Return on Average Equity (ROAE % = Net Income / Avg Book Equity * 100)
3. Efficiency Ratio (Non-Interest / Operating Expense / Revenue * 100)
4. Net Interest Margin (NIM % = (Interest Income - Interest Expense) / Avg Assets * 100)
5. Capital Adequacy / Leverage (Equity / Total Assets % or explicit CET1)
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.penman_engine import is_financial_institution


def compute_bank_metrics(db: Session, company_id: str) -> dict[str, Any]:
    """Computes specialized banking and financial institution performance metrics."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    if not is_financial_institution(company):
        return {
            "company_id": company_id,
            "status": "non_financial_excluded",
            "message": "Commercial/industrial company; bank financial model not applicable.",
        }

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
    snaps_to_use = dated if len(dated) >= 2 else (dated + seed if dated else seed)

    if not snaps_to_use:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "message": "No financial snapshots on file for institution.",
        }

    latest = snaps_to_use[-1]
    prev = snaps_to_use[-2] if len(snaps_to_use) >= 2 else None

    # Strict compliance with AGENTS.md: Never fabricate corporate debt, FCF, or gross profit
    corporate_debt = None
    free_cash_flow = None
    gross_profit = None

    ni = latest.net_income
    rev = latest.revenue or 1.0
    ta_curr = latest.total_assets
    ta_prev = prev.total_assets if (prev and prev.total_assets) else ta_curr
    eq_curr = latest.book_equity
    eq_prev = prev.book_equity if (prev and prev.book_equity) else eq_curr

    # Average Assets & Average Equity
    avg_assets = (ta_curr + (ta_prev or ta_curr)) / 2.0 if ta_curr else None
    avg_equity = (eq_curr + (eq_prev or eq_curr)) / 2.0 if eq_curr else None

    # 1. Return on Average Assets (ROAA %)
    roaa_pct = None
    if ni is not None and avg_assets is not None and avg_assets > 0:
        roaa_pct = round((ni / avg_assets) * 100.0, 2)

    # 2. Return on Average Equity (ROAE %)
    roae_pct = None
    if ni is not None and avg_equity is not None and avg_equity > 0:
        roae_pct = round((ni / avg_equity) * 100.0, 2)

    # 3. Efficiency Ratio (Operating Expenses / Revenue %)
    ebit = latest.ebit
    efficiency_ratio_pct = None
    if ebit is not None and rev > 0:
        opex = max(0.0, rev - ebit)
        efficiency_ratio_pct = round((opex / rev) * 100.0, 2)

    # 4. Net Interest Margin (NIM %)
    int_inc = getattr(latest, "interest_income", None)
    int_exp = latest.interest_expense
    nim_pct = None
    if int_inc is not None and int_exp is not None and avg_assets and avg_assets > 0:
        net_int_income = int_inc - int_exp
        nim_pct = round((net_int_income / avg_assets) * 100.0, 2)

    # 5. Capital Adequacy / Leverage
    equity_to_assets_pct = None
    if eq_curr is not None and ta_curr is not None and ta_curr > 0:
        equity_to_assets_pct = round((eq_curr / ta_curr) * 100.0, 2)

    # Explicit CET1 if present on snapshot
    cet1_ratio = getattr(latest, "cet1_ratio", None)

    # Capitalization Health Assessment
    if cet1_ratio is not None:
        c_pct = cet1_ratio * 100.0 if cet1_ratio <= 1.0 else cet1_ratio
        capital_health = "Well Capitalized" if c_pct >= 10.5 else ("Adequate" if c_pct >= 8.0 else "Constrained")
    elif equity_to_assets_pct is not None:
        capital_health = "Well Capitalized" if equity_to_assets_pct >= 6.0 else ("Adequate" if equity_to_assets_pct >= 4.0 else "Highly Leveraged")
    else:
        capital_health = "Unknown"

    return {
        "company_id": company_id,
        "currency": company.currency,
        "status": "computed",
        "corporate_debt": corporate_debt,
        "free_cash_flow": free_cash_flow,
        "gross_profit": gross_profit,
        "roaa_pct": roaa_pct,
        "roae_pct": roae_pct,
        "efficiency_ratio_pct": efficiency_ratio_pct,
        "net_interest_margin_pct": nim_pct,
        "equity_to_assets_pct": equity_to_assets_pct,
        "cet1_ratio": cet1_ratio,
        "capital_health": capital_health,
        "compliance_notes": "Corporate debt, FCF, and gross profit strictly kept blank per AGENTS.md financial rules.",
    }
