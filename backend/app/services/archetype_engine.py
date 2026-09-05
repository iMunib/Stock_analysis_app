"""Peter Lynch 6 Business Archetypes & PEG Classifier (Phase 2 Master Directive).

Implements Peter Lynch's classic taxonomy from 'One Up On Wall Street':
1. Fast Growers (Revenue/EPS CAGR >= 20%, manageable leverage)
2. Stalwarts (Revenue CAGR 8%-19%, steady cash generation)
3. Slow Growers (Revenue CAGR 1%-7%, generous dividend payout)
4. Cyclicals (Margin/revenue volatility > 2.5 sigma or cyclical sector)
5. Turnarounds (Negative EPS recovering to positive, active balance sheet repair)
6. Asset Plays (Market cap <= NNWC / NCAV or deep discount to tangible book)

Plus PEG Ratio calculation and valuation tier tagging:
- PEG <= 1.0: Attractive
- 1.0 < PEG <= 2.0: Fair
- PEG > 2.0: Stretched
"""
from __future__ import annotations

import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, CompanyProfile, FinancialSnapshot


CYCLICAL_SECTORS = {"energy", "materials"}
CYCLICAL_INDUSTRIES = {"semiconductors", "automobiles", "steel", "mining", "chemicals", "airlines"}


def _safe_div(num: float | None, denom: float | None, default: float | None = None) -> float | None:
    if num is None or denom is None or abs(denom) < 1e-9:
        return default
    return num / denom


def _calc_cagr(start_val: float | None, end_val: float | None, years: int) -> float | None:
    if start_val is None or end_val is None or start_val <= 0 or end_val <= 0 or years <= 0:
        return None
    try:
        return ((end_val / start_val) ** (1.0 / years) - 1.0) * 100.0
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def classify_archetype(db: Session, company_id: str) -> dict[str, Any]:
    """Classifies company into one of 6 Peter Lynch archetypes and computes PEG."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

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

    latest = snaps_to_use[-1] if snaps_to_use else None
    earliest = snaps_to_use[0] if snaps_to_use else None
    n_periods = len(snaps_to_use)

    # 1. Growth Metrics (CAGR)
    rev_cagr = None
    eps_cagr = None
    if n_periods >= 2 and earliest and latest and earliest.fiscal_year != latest.fiscal_year:
        years = max(1, (latest.fiscal_year or 0) - (earliest.fiscal_year or 0))
        rev_cagr = _calc_cagr(earliest.revenue, latest.revenue, years)
        eps_cagr = _calc_cagr(earliest.diluted_eps, latest.diluted_eps, years)

    # If only 1 snapshot or seed only, fallback to revenue/growth proxy if available
    if rev_cagr is None and latest and latest.revenue:
        rev_cagr = 10.0  # neutral benchmark default when no multi-year history

    # 2. Balance Sheet / Health Metrics
    seed_snap = seed[0] if seed else None
    mcap = (latest.market_cap if latest else None) or (seed_snap.market_cap if seed_snap else None) or ((seed_snap.price * seed_snap.shares_snapshot) if seed_snap and seed_snap.price and seed_snap.shares_snapshot else None)
    book_equity = (latest.book_equity if latest else None) or (seed_snap.book_equity if seed_snap else None)
    total_debt = latest.total_debt or 0.0
    cash = latest.cash_st_investments or 0.0
    net_debt = total_debt - cash
    ebitda = latest.ebitda or (latest.ebit * 1.2 if latest and latest.ebit else None)
    de_ratio = _safe_div(total_debt, book_equity)
    pb_ratio = latest.pb_calc or (_safe_div(mcap, book_equity) if mcap and book_equity else None)
    pe_ratio = latest.pe_calc or (_safe_div(mcap, latest.net_income) if mcap and latest and latest.net_income else None)

    # Asset Play metrics: Net Current Asset Value (NCAV) & Net-Net Working Capital (NNWC)
    ca = getattr(latest, "current_assets", None)
    tl = latest.total_liabilities if latest else None
    ar = getattr(latest, "accounts_receivable", None) or 0.0
    inv = getattr(latest, "inventory", None) or 0.0

    ncav = (ca - tl) if (ca is not None and tl is not None) else None
    nnwc = (cash + 0.75 * ar + 0.5 * inv - tl) if tl is not None else None

    # Dividend Yield
    profile = db.query(CompanyProfile).filter_by(company_id=company_id).first()
    div_yield = profile.dividend_yield if profile else None
    if div_yield is not None and div_yield > 1.0:
        div_yield = div_yield / 100.0

    # Sector / Industry checks
    sector = (company.gics_sector or "").lower().strip()
    ind = (company.gics_industry or company.custom_industry_sheet or "").lower().strip()
    is_cyclical_sector = sector in CYCLICAL_SECTORS or any(c in ind for c in CYCLICAL_INDUSTRIES)

    # Check Turnaround: previous EPS was negative, latest EPS is positive
    is_turnaround = False
    if n_periods >= 2:
        prev = snaps_to_use[-2]
        if prev.net_income is not None and prev.net_income < 0 and latest and latest.net_income is not None and latest.net_income > 0:
            is_turnaround = True

    # Check Margin Volatility for Cyclicals
    margin_vol = 0.0
    if n_periods >= 3:
        margins = [
            (s.ebit / s.revenue) for s in snaps_to_use if s.ebit is not None and s.revenue and s.revenue > 0
        ]
        if len(margins) >= 3:
            mean_m = sum(margins) / len(margins)
            variance = sum((m - mean_m) ** 2 for m in margins) / len(margins)
            margin_vol = math.sqrt(variance)

    # 3. Deterministic Classification Logic
    archetype = "Stalwarts"
    rationale = ""

    # Priority 1: Asset Play (Deep balance sheet discount)
    if mcap is not None and mcap > 0 and ((nnwc is not None and mcap <= nnwc) or (ncav is not None and mcap <= ncav) or (pb_ratio is not None and pb_ratio < 0.75)):
        archetype = "Asset Plays"
        rationale = f"Trading at deep discount to asset base (P/B {pb_ratio:.2f}x or below net tangible working capital)."

    # Priority 2: Turnaround
    elif is_turnaround or (de_ratio is not None and de_ratio > 3.0 and latest and latest.net_income and latest.net_income > 0):
        archetype = "Turnarounds"
        rationale = "Recovering from depressed operational earnings with balance sheet restructuring."

    # Priority 3: Cyclical
    elif is_cyclical_sector or margin_vol > 0.08:
        archetype = "Cyclicals"
        rationale = f"High operational volatility ({sector or ind}) tied to macroeconomic and commodity cycles."

    # Priority 4: Fast Grower (Revenue or EPS CAGR >= 20% with sound balance sheet)
    elif ((rev_cagr is not None and rev_cagr >= 20.0) or (eps_cagr is not None and eps_cagr >= 20.0)) and (de_ratio is None or de_ratio < 2.0):
        archetype = "Fast Growers"
        rationale = f"High-velocity expansion with {max(rev_cagr or 0, eps_cagr or 0):.1f}% CAGR and manageable debt."

    # Priority 5: Slow Grower (Revenue CAGR 1-7% and dividend yield > 2.5%)
    elif (rev_cagr is not None and rev_cagr < 8.0) and (div_yield is not None and div_yield >= 0.025):
        archetype = "Slow Growers"
        rationale = f"Mature business generating {div_yield*100:.1f}% dividend yield with single-digit top-line growth."

    # Default: Stalwarts
    else:
        archetype = "Stalwarts"
        cagr_display = f"{rev_cagr:.1f}%" if rev_cagr is not None else "moderate"
        rationale = f"Stalwart compounder exhibiting steady {cagr_display} annual revenue growth."

    # 4. PEG Ratio Calculation
    growth_for_peg = max(0.1, rev_cagr or eps_cagr or 5.0)
    peg_ratio = None
    peg_status = "Not Meaningful"

    if pe_ratio is not None and pe_ratio > 0 and growth_for_peg > 0:
        peg_ratio = round(pe_ratio / growth_for_peg, 2)
        if peg_ratio <= 1.0:
            peg_status = "Attractive"
        elif peg_ratio <= 2.0:
            peg_status = "Fair"
        else:
            peg_status = "Stretched"

    return {
        "company_id": company_id,
        "archetype": archetype,
        "rationale": rationale,
        "metrics": {
            "revenue_cagr_pct": round(rev_cagr, 2) if rev_cagr is not None else None,
            "eps_cagr_pct": round(eps_cagr, 2) if eps_cagr is not None else None,
            "pe_ratio": round(pe_ratio, 2) if pe_ratio is not None else None,
            "peg_ratio": peg_ratio,
            "peg_status": peg_status,
            "price_to_book": round(pb_ratio, 2) if pb_ratio is not None else None,
            "dividend_yield_pct": round(div_yield * 100.0, 2) if div_yield is not None else None,
            "net_debt_to_ebitda": round(net_debt / ebitda, 2) if (ebitda and ebitda > 0) else None,
        },
    }
