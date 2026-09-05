"""Warren Buffett Owner Earnings Engine (Phase 2 Master Directive).

Calculates true economic owner earnings using Bruce Greenwald's
Maintenance vs. Growth CapEx separation:
1. Sales / PP&E Capital Intensity:
   Capital Intensity = Revenue / PP&E Net
2. Growth CapEx:
   Growth CapEx = max(0, Delta Revenue) / Capital Intensity
3. Maintenance CapEx:
   Maintenance CapEx = max(0, Total CapEx - Growth CapEx)
4. Owner Earnings:
   Owner Earnings = Net Income + D&A - Maintenance CapEx - Delta Working Capital
5. Owner Earnings Yield:
   Yield % = (Owner Earnings / Market Cap) * 100
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.penman_engine import is_financial_institution


def compute_owner_earnings(db: Session, company_id: str) -> dict[str, Any]:
    """Computes Buffett Owner Earnings and Owner Earnings Yield."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    if is_financial_institution(company):
        return {
            "company_id": company_id,
            "status": "financial_institution_excluded",
            "owner_earnings": None,
            "owner_earnings_yield_pct": None,
            "maintenance_capex": None,
            "growth_capex": None,
            "message": "Financial institutions excluded (FCF and CapEx not applicable).",
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
            "owner_earnings": None,
            "owner_earnings_yield_pct": None,
            "message": "No financial snapshots available.",
        }

    latest = snaps_to_use[-1]
    prev = snaps_to_use[-2] if len(snaps_to_use) >= 2 else None

    net_income = latest.net_income or 0.0
    ebit = latest.ebit or 0.0
    ebitda = latest.ebitda or (ebit * 1.2 if ebit else net_income * 1.3)
    dna = max(0.0, ebitda - ebit)

    total_capex = abs(latest.capex or 0.0)
    rev_t = latest.revenue or 0.0
    rev_prev = prev.revenue if (prev and prev.revenue) else rev_t
    delta_rev = max(0.0, rev_t - rev_prev)

    ppe = getattr(latest, "ppe_net", None) or (latest.total_assets * 0.3 if latest.total_assets else None)

    # Greenwald Sales/PP&E ratio
    if ppe is not None and ppe > 0 and rev_t > 0:
        sales_to_ppe = rev_t / ppe
    else:
        sales_to_ppe = 2.5  # standard industrial benchmark

    if sales_to_ppe > 0:
        growth_capex = min(total_capex, delta_rev / sales_to_ppe)
    else:
        growth_capex = 0.0

    maintenance_capex = max(0.0, total_capex - growth_capex)

    # Delta Working Capital
    ca_t = getattr(latest, "current_assets", None)
    cl_t = getattr(latest, "current_liabilities", None)
    ca_prev = getattr(prev, "current_assets", None) if prev else None
    cl_prev = getattr(prev, "current_liabilities", None) if prev else None

    if ca_t is not None and cl_t is not None and ca_prev is not None and cl_prev is not None:
        wc_t = ca_t - cl_t
        wc_prev = ca_prev - cl_prev
        delta_wc = wc_t - wc_prev
    else:
        delta_wc = 0.0

    # Buffett Owner Earnings Formula:
    # Owner Earnings = Net Income + D&A - Maintenance CapEx - Delta Working Capital
    owner_earnings = net_income + dna - maintenance_capex - delta_wc

    # Owner Earnings Yield %
    mcap = latest.market_cap
    if mcap is None and latest.price and latest.shares_snapshot:
        mcap = latest.price * latest.shares_snapshot

    oe_yield_pct = None
    if mcap is not None and mcap > 0:
        oe_yield_pct = round((owner_earnings / mcap) * 100.0, 2)

    return {
        "company_id": company_id,
        "fiscal_year": latest.fiscal_year,
        "status": "computed",
        "net_income": net_income,
        "depreciation_amortization": round(dna, 2),
        "total_capex": round(total_capex, 2),
        "growth_capex": round(growth_capex, 2),
        "maintenance_capex": round(maintenance_capex, 2),
        "delta_working_capital": round(delta_wc, 2),
        "owner_earnings": round(owner_earnings, 2),
        "market_cap": mcap,
        "owner_earnings_yield_pct": oe_yield_pct,
    }
