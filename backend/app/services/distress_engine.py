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


def _first_not_none(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _compute_factors(snap: FinancialSnapshot, seed: FinancialSnapshot | None = None) -> dict[str, float] | None:
    """Extracts X1-X5 factors from snapshot row with accounting identity fallbacks."""
    seed_ta = seed.total_assets if seed else None
    seed_tl = seed.total_liabilities if seed else None
    seed_cash = seed.cash_st_investments if seed else None
    seed_debt = seed.total_debt if seed else None
    seed_eq = seed.book_equity if seed else None
    seed_ebit = seed.ebit if seed else None
    seed_rev = seed.revenue if seed else None

    ta = _first_not_none(snap.total_assets, seed_ta)
    tl = _first_not_none(snap.total_liabilities, seed_tl)
    cash = _first_not_none(snap.cash_st_investments, seed_cash, 0.0)
    debt = _first_not_none(snap.total_debt, seed_debt, 0.0)
    equity = _first_not_none(snap.book_equity, seed_eq)

    # Accounting identities: Assets = Liabilities + Equity
    if equity is None and ta is not None and tl is not None:
        equity = ta - tl
    if tl is None and ta is not None and equity is not None:
        tl = max(0.0, ta - equity)

    ebit = _first_not_none(snap.ebit, seed_ebit)
    rev = _first_not_none(snap.revenue, seed_rev)
    mcap = snap.market_cap
    if (mcap is None or mcap <= 0) and seed is not None:
        mcap = seed.market_cap or ((seed.price or 0.0) * (seed.shares_snapshot or 0.0) if seed.price and seed.shares_snapshot else None)
    if (mcap is None or mcap <= 0) and snap.price and snap.shares_snapshot:
        mcap = snap.price * snap.shares_snapshot

    if ta is None or ta <= 0 or tl is None or equity is None:
        return None

    # X1: Working Capital / Total Assets
    # Genuine Working Capital = Current Assets - Current Liabilities
    ca = _first_not_none(getattr(snap, "current_assets", None), getattr(seed, "current_assets", None) if seed else None)
    cl = _first_not_none(getattr(snap, "current_liabilities", None), getattr(seed, "current_liabilities", None) if seed else None)
    if ca is not None and cl is not None:
        wc = ca - cl
    else:
        ca_proxy = cash + 0.35 * max(0.0, ta - cash)
        cl_proxy = max(0.0, tl - debt) if debt <= tl else 0.5 * tl
        wc = ca_proxy - cl_proxy
    x1 = wc / ta

    # X2: Retained Earnings / Total Assets
    re = _first_not_none(getattr(snap, "retained_earnings", None), getattr(seed, "retained_earnings", None) if seed else None)
    if re is not None:
        x2 = re / ta
    else:
        x2 = equity / ta

    # X3: EBIT / Total Assets
    if ebit is None:
        ebit = _first_not_none(getattr(snap, "net_income", None), getattr(seed, "net_income", None) if seed else None)
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

    factors = _compute_factors(snap, seed)
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

    data_quality_flags: list[str] = []
    ppe = _first_not_none(getattr(snap, "ppe_net", None), getattr(seed, "ppe_net", None) if seed else None)
    inv = _first_not_none(getattr(snap, "inventory", None), getattr(seed, "inventory", None) if seed else None)
    ca = _first_not_none(getattr(snap, "current_assets", None), getattr(seed, "current_assets", None) if seed else None)
    cl = _first_not_none(getattr(snap, "current_liabilities", None), getattr(seed, "current_liabilities", None) if seed else None)
    re = _first_not_none(getattr(snap, "retained_earnings", None), getattr(seed, "retained_earnings", None) if seed else None)

    if ca is None or cl is None:
        data_quality_flags.append("PROXY_WORKING_CAPITAL_USED")
    if re is None:
        data_quality_flags.append("PROXY_RETAINED_EARNINGS_USED")

    # Only fall back to Z'' when PP&E or inventory is inapplicable/absent
    if is_mfg:
        if (ppe is not None and ppe == 0) or (inv is not None and inv == 0):
            model_used = "non_manufacturing"
            active_z = z_double_prime
            data_quality_flags.append("FALLBACK_Z_DOUBLE_PRIME_INAPPLICABLE_CAPITAL_ITEMS")
        else:
            model_used = "manufacturing"
            active_z = z_classic
    else:
        model_used = "non_manufacturing"
        active_z = z_double_prime

    # Determine Zone
    if model_used == "manufacturing":
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
        "data_quality_flags": data_quality_flags,
    }
