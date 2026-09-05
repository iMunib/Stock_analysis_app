"""Richard Sloan Accrual Anomaly Engine (Phase 3 Master Directive).

Grounding in Sloan (1996) "Do Stock Prices Fully Reflect Information in Accruals
and Cash Flows about Future Earnings?":

Formula:
  Accrual Ratio = (Net Income - CFO) / Average Total Assets

Quality Classifications:
- Accrual Ratio > +10.0% (> +0.10): "Low Quality / Paper Earnings"
  (Earnings driven by non-cash working capital bloat / accounting recognition).
- Accrual Ratio < -10.0% (< -0.10): "High Quality / Cash Rich"
  (Operating cash flows strongly outpace reported net income).
- Between -10.0% and +10.0%: "Normal Accruals"
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.penman_engine import is_financial_institution


def compute_sloan_accruals(db: Session, company_id: str) -> dict[str, Any]:
    """Calculates Richard Sloan's Cash Flow and Balance Sheet Accrual Ratios."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    if is_financial_institution(company):
        return {
            "company_id": company_id,
            "status": "financial_institution_excluded",
            "accrual_ratio": None,
            "quality_rating": "Excluded",
            "flag": None,
            "message": "Financial institutions excluded from Sloan corporate accrual anomaly analysis.",
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
            "accrual_ratio": None,
            "quality_rating": "Unknown",
            "flag": None,
            "message": "No financial statements on file.",
        }

    latest = snaps_to_use[-1]
    prev = snaps_to_use[-2] if len(snaps_to_use) >= 2 else None

    net_income = latest.net_income
    cfo = latest.operating_cash_flow
    ta_latest = latest.total_assets
    ta_prev = prev.total_assets if (prev and prev.total_assets) else ta_latest

    if net_income is None or cfo is None or ta_latest is None or ta_latest <= 0:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "accrual_ratio": None,
            "quality_rating": "Unknown",
            "flag": None,
            "message": "Net income, CFO, or Total Assets incomplete on snapshot.",
        }

    # Average Total Assets
    avg_ta = (ta_latest + (ta_prev or ta_latest)) / 2.0
    if avg_ta <= 0:
        avg_ta = ta_latest

    # Cash Flow Accruals = Net Income - CFO
    cf_accruals = net_income - cfo
    accrual_ratio = cf_accruals / avg_ta
    accrual_ratio_rounded = round(accrual_ratio, 4)

    # Classification
    if accrual_ratio > 0.10:
        quality_rating = "Low Quality / Paper Earnings"
        flag = "HIGH_ACCRUALS_PAPER_EARNINGS"
        interpretation = (
            f"Accrual Ratio of {accrual_ratio_rounded*100:.1f}% indicates high non-cash accrual drag. "
            "Reported net income is heavily reliant on accounting accruals rather than real cash flow."
        )
    elif accrual_ratio < -0.10:
        quality_rating = "High Quality / Cash Rich"
        flag = "CASH_RICH_QUALITY_EARNINGS"
        interpretation = (
            f"Accrual Ratio of {accrual_ratio_rounded*100:.1f}% indicates strong cash conversion. "
            "Operating cash flows substantially exceed reported accounting net income."
        )
    else:
        quality_rating = "Normal Accruals"
        flag = None
        interpretation = (
            f"Accrual Ratio of {accrual_ratio_rounded*100:.1f}% falls within normal industrial bounds "
            "(-10% to +10%)."
        )

    # Balance Sheet Accruals if available
    bs_accrual_ratio = None
    if prev is not None:
        ca_latest = getattr(latest, "current_assets", None)
        ca_prev = getattr(prev, "current_assets", None)
        cash_latest = latest.cash_st_investments or 0.0
        cash_prev = prev.cash_st_investments or 0.0
        cl_latest = getattr(latest, "current_liabilities", None)
        cl_prev = getattr(prev, "current_liabilities", None)
        debt_latest = latest.total_debt or 0.0
        debt_prev = prev.total_debt or 0.0

        if ca_latest is not None and ca_prev is not None and cl_latest is not None and cl_prev is not None:
            delta_nca = (ca_latest - cash_latest) - (ca_prev - cash_prev)
            delta_ncl = (cl_latest - min(cl_latest, debt_latest)) - (cl_prev - min(cl_prev, debt_prev))
            bs_accruals = delta_nca - delta_ncl
            bs_accrual_ratio = round(bs_accruals / avg_ta, 4)

    return {
        "company_id": company_id,
        "fiscal_year": latest.fiscal_year,
        "status": "computed",
        "net_income": net_income,
        "operating_cash_flow": cfo,
        "total_accruals": round(cf_accruals, 2),
        "avg_total_assets": round(avg_ta, 2),
        "accrual_ratio": accrual_ratio_rounded,
        "bs_accrual_ratio": bs_accrual_ratio,
        "quality_rating": quality_rating,
        "flag": flag,
        "interpretation": interpretation,
    }
