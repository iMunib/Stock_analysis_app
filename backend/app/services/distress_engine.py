"""GuruFocus-style Solvency & Distress Engine (Altman Z-Score) (Master Directive WS3).

Calculates:
1. Original 5-Factor Altman Z-Score for manufacturing & capital-intensive firms:
   Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5
   Zones: Z > 2.99 (Safe), 1.81 <= Z <= 2.99 (Grey), Z < 1.81 (Distress)

2. Altman Z''-Score for service, tech & asset-light non-manufacturing firms:
   Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
   Zones: Z'' > 2.60 (Safe), 1.10 <= Z'' <= 2.60 (Grey), Z'' < 1.10 (Distress)

Excludes Financials (Banks, Insurers, Credit Services) where balance sheet
structures render corporate distress ratios non-applicable.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.penman_engine import is_financial_institution

MANUFACTURING_SECTORS = {
    "industrials",
    "materials",
    "energy",
    "consumer staples",
}


def _compute_factors(snap: FinancialSnapshot) -> dict[str, float] | None:
    """Extracts X1-X5 factors from snapshot row."""
    ta = snap.total_assets
    tl = snap.total_liabilities
    cash = snap.cash_st_investments or 0.0
    debt = snap.total_debt or 0.0
    equity = snap.book_equity
    ebit = snap.ebit
    rev = snap.revenue
    mcap = snap.market_cap

    if ta is None or ta <= 0 or tl is None or equity is None:
        return None

    # X1: Working Capital / Total Assets
    # Working Capital proxy: Current Assets (Cash + 0.35 * non-cash assets) - Current Liabilities (TL - Debt)
    ca_proxy = cash + 0.35 * max(0.0, ta - cash)
    cl_proxy = max(0.0, tl - debt) if debt <= tl else 0.5 * tl
    wc = ca_proxy - cl_proxy
    x1 = wc / ta

    # X2: Retained Earnings / Total Assets (approximate by Book Equity)
    x2 = equity / ta

    # X3: EBIT / Total Assets
    x3 = (ebit / ta) if ebit is not None else 0.0

    # X4: Market Value of Equity / Total Liabilities
    equity_val = mcap if (mcap is not None and mcap > 0) else equity
    x4 = (equity_val / tl) if tl > 0 else (equity_val / ta)

    # X5: Sales / Total Assets
    x5 = (rev / ta) if (rev is not None and rev > 0) else 0.0

    return {
        "x1_working_capital_to_ta": round(x1, 4),
        "x2_retained_earnings_to_ta": round(x2, 4),
        "x3_ebit_to_ta": round(x3, 4),
        "x4_market_equity_to_tl": round(x4, 4),
        "x5_sales_to_ta": round(x5, 4),
    }


def compute_distress(db: Session, company_id: str) -> dict[str, Any]:
    """Computes Altman Z and Z'' scores, classification zones, and factors."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    # Financial institutions exclusion
    if is_financial_institution(company):
        return {
            "company_id": company_id,
            "status": "financial_institution_excluded",
            "model_used": "excluded",
            "z_score": None,
            "z_double_prime": None,
            "zone": "Excluded",
            "message": "Financial institutions excluded from Altman Z-score analysis.",
            "factors": None,
        }

    # Fetch latest snapshot (dated annual preferred, then seed)
    latest = db.execute(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_not(None),
            FinancialSnapshot.period_type == "FY",
        )
        .order_by(FinancialSnapshot.fiscal_year.desc())
    ).scalars().first()

    seed = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_(None),
            FinancialSnapshot.period_type == "FY",
        )
    ).scalar_one_or_none()

    snap = latest or seed
    if snap is None:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "model_used": None,
            "z_score": None,
            "z_double_prime": None,
            "zone": "Unknown",
            "message": "No balance sheet snapshots found.",
            "factors": None,
        }

    factors = _compute_factors(snap)
    if factors is None:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "model_used": None,
            "z_score": None,
            "z_double_prime": None,
            "zone": "Unknown",
            "message": "Required balance sheet items (assets, liabilities, equity) incomplete.",
            "factors": None,
        }

    x1 = factors["x1_working_capital_to_ta"]
    x2 = factors["x2_retained_earnings_to_ta"]
    x3 = factors["x3_ebit_to_ta"]
    x4 = factors["x4_market_equity_to_tl"]
    x5 = factors["x5_sales_to_ta"]

    # 1. Classic Altman Z-score: 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5
    z_classic = round(1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5, 2)

    # 2. Altman Z''-score: 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
    z_double_prime = round(6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4, 2)

    # Determine sector archetype
    sector = (company.gics_sector or "").lower().strip()
    is_mfg = sector in MANUFACTURING_SECTORS
    model_used = "manufacturing" if is_mfg else "non_manufacturing"
    active_z = z_classic if is_mfg else z_double_prime

    # Determine Zone
    if is_mfg:
        if z_classic > 2.99:
            zone = "Safe"
        elif z_classic >= 1.81:
            zone = "Grey"
        else:
            zone = "Distress"
    else:
        if z_double_prime > 2.60:
            zone = "Safe"
        elif z_double_prime >= 1.10:
            zone = "Grey"
        else:
            zone = "Distress"

    return {
        "company_id": company_id,
        "fiscal_year": snap.fiscal_year,
        "status": "computed",
        "model_used": model_used,
        "z_score": z_classic,
        "z_double_prime": z_double_prime,
        "active_z": active_z,
        "zone": zone,
        "factors": factors,
    }
