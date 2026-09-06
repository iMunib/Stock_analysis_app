"""Greenwald Earnings Power Value (EPV) Engine (Wave 4 Epic 10 US-0106/US-0115).

Greenwald (Value Investing, 2001):
  EPV = Normalized Operating Earnings × (1 − tax) / WACC
  Reproduction Cost ≈ Total Assets (owner workbook proxy; honest about limitation)
  Margin-of-Safety Floor = min(EPV, Reproduction Cost)

- Normalized earnings = 5-yr median EBIT where ≥3 points exist; otherwise latest EBIT
  with `thin_history` flag.
- WACC default 9% (user-overridable via DCF params); tax 21% (clamped 15–30% if
  effective tax derivable from OCF/NI, else 21%).
- Missing inputs → `insufficient_data` + descriptive flag, never invented.

For Financials (Banks/Insurance/Credit), EPV is structurally weaker (EBIT not
meaningful); the engine still computes but tags `financial_sector_note`.
"""
from __future__ import annotations

from statistics import median
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.penman_engine import is_financial_institution
from app.services.valuation_engine import DEFAULT_WACC

DEFAULT_TAX = 0.21


def _median_5y(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None and v != 0]
    if len(clean) < 3:
        return None
    return float(median(clean[-5:]))


def compute_epv(db: Session, company_id: str, wacc: float = DEFAULT_WACC) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    snaps = db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == company_id, FinancialSnapshot.period_type == "FY")
        .order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()

    dated = [s for s in snaps if s.fiscal_year is not None]
    seed = next((s for s in snaps if s.fiscal_year is None), None)
    latest = dated[-1] if dated else seed

    is_fin_early = False
    try:
        from app.services.penman_engine import is_financial_institution as _is_fin
        is_fin_early = _is_fin(company) if company else False
    except Exception:
        pass
    if latest is None:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "reason": "no_snapshot_rows",
            "epv": None,
            "reproduction_cost": None,
            "is_financial": is_fin_early,
            "financial_note": "EPV structurally weaker for banks/insurers - see Bank DDM/Residual Income." if is_fin_early else None,
            "disclaimer": "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
        }

    # EBIT history for normalization
    ebit_history = [float(s.ebit) for s in dated if s.ebit is not None]
    # Also try ebitda-derived ebit where ebit missing? use ebit only per spec
    normalized_ebit = _median_5y(ebit_history) if ebit_history else None
    thin_history = False
    source_ebit: float | None = None
    if normalized_ebit is not None:
        source_ebit = normalized_ebit
    else:
        # Fallback to latest EBIT if median not available
        if latest.ebit is not None:
            source_ebit = float(latest.ebit)
            thin_history = True
        else:
            # Try operating income proxy? Use EBIT from seed if needed
            if seed and seed.ebit is not None:
                source_ebit = float(seed.ebit)
                thin_history = True

    if source_ebit is None:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "reason": "ebit_missing_for_epv",
            "epv": None,
            "reproduction_cost": None,
            "currency": company.currency,
            "is_financial": is_fin_early,
            "financial_note": "EPV structurally weaker for banks/insurers - see Bank DDM/Residual Income." if is_fin_early else None,
            "disclaimer": "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
        }

    # Tax rate: try to derive effective tax from (ebit - net_income)/ebit where both present, clamped 15-30%
    tax = DEFAULT_TAX
    if latest.ebit is not None and latest.net_income is not None and latest.ebit != 0:
        try:
            eff = 1.0 - float(latest.net_income) / float(latest.ebit)
            # Clamp - but only if plausible (0 to 0.5)
            if 0 <= eff <= 0.5:
                tax = max(0.15, min(0.30, eff))
        except Exception:
            pass

    nopat = source_ebit * (1.0 - tax)
    epv = nopat / wacc if wacc and wacc > 0 else None

    # Reproduction cost proxy: Total Assets (honest limitation noted)
    reproduction = None
    if latest.total_assets is not None:
        reproduction = float(latest.total_assets)
    elif seed and seed.total_assets is not None:
        reproduction = float(seed.total_assets)

    # Market cap
    mcap = None
    if latest.market_cap is not None:
        mcap = float(latest.market_cap)
    elif latest.price is not None and latest.shares_snapshot is not None:
        mcap = float(latest.price) * float(latest.shares_snapshot)
    elif seed and seed.market_cap is not None:
        mcap = float(seed.market_cap)
    elif seed and seed.price is not None and seed.shares_snapshot is not None:
        mcap = float(seed.price) * float(seed.shares_snapshot)

    # Margin of safety floor vs market cap
    floor = None
    if epv is not None and reproduction is not None:
        floor = min(epv, reproduction)
    elif epv is not None:
        floor = epv
    elif reproduction is not None:
        floor = reproduction

    premium_discount = None
    cheap_for_reason = False
    if floor is not None and mcap is not None and floor != 0:
        premium_discount = round((mcap - floor) / floor * 100.0, 1)
        # Cheap-for-a-reason check: price below floor but forensic flags fail (handled in API layer via forensic health)
        cheap_for_reason = premium_discount is not None and premium_discount < 0

    is_fin = is_financial_institution(company)

    return {
        "company_id": company_id,
        "currency": company.currency,
        "status": "computed" if epv is not None else "insufficient_data",
        "normalized_ebit": round(source_ebit, 2) if source_ebit is not None else None,
        "ebit_source": "median_5y" if not thin_history and normalized_ebit is not None else "latest_ebit_thin_history" if thin_history else "median_5y",
        "thin_history": thin_history,
        "tax_rate": round(tax, 4),
        "wacc": wacc,
        "nopat": round(nopat, 2) if nopat is not None else None,
        "epv": round(epv, 2) if epv is not None else None,
        "reproduction_cost": round(reproduction, 2) if reproduction is not None else None,
        "reproduction_note": "Reproduction cost proxied via Total Assets; owner workbook lacks separate reproduction cost build.",
        "market_cap": round(mcap, 2) if mcap is not None else None,
        "floor_value": round(floor, 2) if floor is not None else None,
        "premium_discount_pct": premium_discount,
        "cheap_for_reason_flag": cheap_for_reason,
        "is_financial": is_fin,
        "financial_note": "EPV structurally weaker for banks/insurers - see Bank DDM/Residual Income." if is_fin else None,
        "disclaimer": "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
        "method_version": "v1",
    }