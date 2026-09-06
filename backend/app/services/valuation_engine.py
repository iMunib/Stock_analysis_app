"""Deterministic Reverse DCF Engine (Expectations Investing).

Solves for the 10-year FCF compound annual growth rate (g) embedded in the current
market Enterprise Value using Brent's method.
Formula:
  EV = sum_{t=1..10} [ FCF_0 * (1+g)^t / (1+WACC)^t ] + [ FCF_10 * (1+g_term) / (WACC - g_term) / (1+WACC)^10 ]
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot, ValuationReverseDCF

DEFAULT_WACC = 0.09
DEFAULT_G_TERMINAL = 0.025


def _brentq(f, a: float, b: float, xtol: float = 1e-8, maxiter: int = 100) -> float:
    """Pure Python implementation of Brent's root-finding method."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        # If bracket doesn't cross zero, try expanding bracket
        for mult in [1.5, 2.0, 3.0]:
            expanded_a = max(a * mult if a < 0 else a / mult, -0.90)
            expanded_b = min(b * mult, 2.0)
            fa, fb = f(expanded_a), f(expanded_b)
            if fa * fb <= 0:
                a, b = expanded_a, expanded_b
                break
        else:
            raise ValueError(f"Root not bracketed: f({a})={fa}, f({b})={fb}")

    if abs(fa) < abs(fb):
        a, b = b, a
        fa, fb = fb, fa

    c = a
    fc = fa
    mflag = True
    d = 0.0

    for _ in range(maxiter):
        if abs(fb) < xtol or abs(b - a) < xtol:
            return b

        if fa != fc and fb != fc:
            s = (a * fb * fc) / ((fa - fb) * (fa - fc)) + (b * fa * fc) / ((fb - fa) * (fb - fc)) + (c * fa * fb) / ((fc - fa) * (fc - fb))
        else:
            s = b - fb * (b - a) / (fb - fa)

        cond1 = not ((3 * a + b) / 4 <= s <= b or b <= s <= (3 * a + b) / 4)
        cond2 = mflag and (abs(s - b) >= abs(b - c) / 2)
        cond3 = (not mflag) and (abs(s - b) >= abs(c - d) / 2)
        cond4 = mflag and (abs(b - c) < xtol)
        cond5 = (not mflag) and (abs(c - d) < xtol)

        if cond1 or cond2 or cond3 or cond4 or cond5:
            s = (a + b) / 2
            mflag = True
        else:
            mflag = False

        fs = f(s)
        d = c
        c = b
        fc = fb

        if fa * fs < 0:
            b = s
            fb = fs
        else:
            a = s
            fa = fs

        if abs(fa) < abs(fb):
            a, b = b, a
            fa, fb = fb, fa

    return b


def dcf_enterprise_value(g: float, baseline_fcf: float, wacc: float = DEFAULT_WACC, g_terminal: float = DEFAULT_G_TERMINAL, years: int = 10) -> float:
    """Calculates discounted 10-year cash flows + perpetual terminal value."""
    if wacc <= g_terminal:
        raise ValueError(f"WACC ({wacc}) must be strictly greater than terminal growth ({g_terminal})")

    pv_flows = sum(baseline_fcf * ((1.0 + g) ** t) / ((1.0 + wacc) ** t) for t in range(1, years + 1))
    fcf_n = baseline_fcf * ((1.0 + g) ** years)
    terminal_val = (fcf_n * (1.0 + g_terminal)) / (wacc - g_terminal)
    pv_tv = terminal_val / ((1.0 + wacc) ** years)
    return pv_flows + pv_tv


def solve_market_implied_growth(
    target_ev: float,
    baseline_fcf: float,
    wacc: float = DEFAULT_WACC,
    g_terminal: float = DEFAULT_G_TERMINAL,
    bracket: tuple[float, float] = (-0.40, 0.60),
) -> float | None:
    """Solves for g equating dcf_enterprise_value(g) to target_ev."""
    if baseline_fcf <= 0 or target_ev <= 0:
        return None

    def obj(g_candidate: float) -> float:
        return dcf_enterprise_value(g_candidate, baseline_fcf, wacc, g_terminal) - target_ev

    try:
        try:
            from scipy.optimize import brentq as scipy_brentq  # type: ignore
            return float(scipy_brentq(obj, bracket[0], bracket[1], xtol=1e-6))
        except (ImportError, ValueError):
            return float(_brentq(obj, bracket[0], bracket[1], xtol=1e-6))
    except Exception:
        return None


def compute_historical_fcf_cagr(history_snaps: list[FinancialSnapshot]) -> float | None:
    """Calculates 5-year (or available >=2 years) FCF CAGR from historical annual rows."""
    valid_snaps = [s for s in history_snaps if s.fiscal_year and s.fcf_calc and s.fcf_calc > 0]
    valid_snaps.sort(key=lambda s: s.fiscal_year)
    if len(valid_snaps) < 2:
        return None

    # Use up to 5-year span
    oldest = valid_snaps[0]
    latest = valid_snaps[-1]
    span = latest.fiscal_year - oldest.fiscal_year
    if span < 1:
        return None

    start_fcf = oldest.fcf_calc
    end_fcf = latest.fcf_calc
    if start_fcf <= 0 or end_fcf <= 0:
        return None

    try:
        cagr = (end_fcf / start_fcf) ** (1.0 / span) - 1.0
        # Clamp extreme values for stability
        return max(-0.80, min(1.50, float(cagr)))
    except (ZeroDivisionError, ValueError):
        return None


def compute_sensitivity_matrix(
    target_ev: float,
    baseline_fcf: float,
    wacc_list: tuple[float, ...] = (0.08, 0.09, 0.10),
    g_term_list: tuple[float, ...] = (0.02, 0.025, 0.03),
) -> dict[str, Any]:
    """Computes a 3x3 sensitivity grid of implied growth rates (WACC vs Terminal g)."""
    grid = []
    for w in wacc_list:
        row = []
        for gt in g_term_list:
            g_implied = solve_market_implied_growth(target_ev, baseline_fcf, wacc=w, g_terminal=gt)
            row.append({
                "wacc": w,
                "terminal_g": gt,
                "implied_growth": round(g_implied, 4) if g_implied is not None else None,
            })
        grid.append(row)
    return {
        "wacc_headers": list(wacc_list),
        "terminal_g_headers": list(g_term_list),
        "grid": grid,
    }


def get_freshness_status(as_of_date, now, kind: str = "price") -> str:
    """Trust sprint C: freshness classification for price/statement inputs.

    kind="price": <=1 day green, 2-7 amber, >7 red.
    kind="statement": <=120 days green, 121-180 amber, >180 red.
    Returns "unknown" when the date is missing.
    """
    if as_of_date is None:
        return "unknown"
    from datetime import date as _date, datetime as _datetime

    if isinstance(as_of_date, str):
        try:
            as_of_date = _datetime.strptime(str(as_of_date)[:10], "%Y-%m-%d").date()
        except ValueError:
            return "unknown"
    if isinstance(as_of_date, _datetime):
        as_of_date = as_of_date.date()
    if not isinstance(as_of_date, _date):
        return "unknown"
    if isinstance(now, _datetime):
        today = now.date()
    else:
        today = now
    days = (today - as_of_date).days
    if days < 0:
        days = 0
    if kind == "statement":
        if days <= 120:
            return "green"
        if days <= 180:
            return "amber"
        return "red"
    # default: market data (price / market cap / EV)
    if days <= 1:
        return "green"
    if days <= 7:
        return "amber"
    return "red"


def compute_and_store_reverse_dcf(db: Session, company_id: str) -> ValuationReverseDCF:
    """Computes reverse DCF metrics and stores/updates valuation_reverse_dcf row."""
    # Find seed / latest snapshot with price & shares
    seed = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_(None),
            FinancialSnapshot.period_type == "FY",
        )
    ).scalar_one_or_none()

    # Find latest annual historical snapshot for FCF and history
    annual_snaps = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_not(None),
            FinancialSnapshot.period_type == "FY",
        ).order_by(FinancialSnapshot.fiscal_year.desc())
    ).scalars().all()

    latest_annual = annual_snaps[0] if annual_snaps else None

    # Share price and shares
    price = None
    shares = None
    if seed:
        price = seed.price
        shares = seed.shares_snapshot
    if not price and latest_annual:
        price = latest_annual.price
    if not shares and latest_annual:
        shares = latest_annual.shares_snapshot

    # Baseline FCF
    baseline_fcf = None
    if latest_annual and latest_annual.fcf_calc:
        baseline_fcf = latest_annual.fcf_calc
    elif seed and seed.fcf_calc:
        baseline_fcf = seed.fcf_calc

    # Debt and Cash
    debt = 0.0
    cash = 0.0
    if seed:
        debt = seed.total_debt or 0.0
        cash = seed.cash_st_investments or 0.0
    elif latest_annual:
        debt = latest_annual.total_debt or 0.0
        cash = latest_annual.cash_st_investments or 0.0
    net_debt = debt - cash

    # Compute EV
    market_cap = (price * shares) if (price and shares) else None
    target_ev = (market_cap + net_debt) if market_cap is not None else None

    # Check negative or missing FCF
    status = "converged"
    implied_g = None
    hist_cagr = None
    gap = None
    matrix = None

    if not baseline_fcf or baseline_fcf <= 0:
        status = "dcf_unviable_negative_fcf"
    elif not target_ev or target_ev <= 0:
        status = "missing_market_cap_or_ev"
    else:
        implied_g = solve_market_implied_growth(target_ev, baseline_fcf, DEFAULT_WACC, DEFAULT_G_TERMINAL)
        hist_cagr = compute_historical_fcf_cagr(list(annual_snaps))
        if implied_g is not None and hist_cagr is not None:
            gap = round(implied_g - hist_cagr, 4)
        matrix = compute_sensitivity_matrix(target_ev, baseline_fcf)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = db.get(ValuationReverseDCF, company_id)
    if row is None:
        row = ValuationReverseDCF(company_id=company_id)
        db.add(row)

    row.computed_at = now
    row.current_share_price = price
    row.diluted_shares = shares
    row.net_debt = net_debt
    row.baseline_fcf = baseline_fcf
    row.terminal_growth_rate = DEFAULT_G_TERMINAL
    row.wacc = DEFAULT_WACC
    row.market_implied_growth_10y = round(implied_g, 4) if implied_g is not None else None
    row.historical_5y_cagr = round(hist_cagr, 4) if hist_cagr is not None else None
    row.expectations_gap = gap
    row.sensitivity_matrix_json = matrix
    row.status = status
    # Trust sprint C: provenance. The DB's price/market-cap as-of comes from the
    # snapshot we actually used (seed preferred, else latest annual); the FCF
    # basis records which statement the baseline came from.
    price_source_snap = seed if (seed and price == seed.price) else latest_annual
    price_as_of = getattr(price_source_snap, "as_of_date", None) if price_source_snap else None
    row.price_as_of = price_as_of
    row.market_cap_as_of = price_as_of
    row.enterprise_value_as_of = price_as_of
    if latest_annual and baseline_fcf == latest_annual.fcf_calc:
        row.baseline_fcf_basis = "FY"
        row.baseline_fcf_period_end = latest_annual.as_of_date
    elif seed and baseline_fcf == seed.fcf_calc:
        row.baseline_fcf_basis = "FY"
        row.baseline_fcf_period_end = seed.as_of_date
    else:
        row.baseline_fcf_basis = None
        row.baseline_fcf_period_end = None
    row.valuation_computed_at = now

    db.flush()
    return row


OPPORTUNITY_COST_HURDLE = 0.08  # Burton Malkiel & J.L. Collins 8.0% nominal index hurdle


def compute_normalized_earnings(db: Session, company_id: str) -> dict[str, Any]:
    """Mid-cycle normalized earnings (US-0117/US-0142).

    For cyclical sectors (Energy, Materials, Industrials) with ≥5 FY EBIT,
    returns 5-yr median EBIT and compares to current/peak. Otherwise returns
    latest EBIT as fallback with `is_normalized=False`.
    """
    from statistics import median as _median

    company = db.get(Company, company_id)
    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == company_id, FinancialSnapshot.period_type == "FY").order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    dated = [s for s in snaps if s.fiscal_year is not None and s.ebit is not None]
    if not dated:
        seed = next((s for s in snaps if s.fiscal_year is None), None)
        if seed and seed.ebit is not None:
            return {
                "company_id": company_id,
                "normalized_ebit": float(seed.ebit),
                "is_normalized": False,
                "reason": "only_seed_ebit",
                "current_ebit": float(seed.ebit),
                "median_5y": None,
                "peak_ebit": float(seed.ebit),
                "delta_vs_peak_pct": 0.0,
            }
        return {"company_id": company_id, "normalized_ebit": None, "is_normalized": False, "reason": "ebit_missing"}

    # Cyclical check
    cyclical_sectors = {"energy", "materials", "industrials"}
    is_cyclical = (company.gics_sector or "").lower() in cyclical_sectors if company else False

    ebits = [float(s.ebit) for s in dated[-10:]]
    median_5y = float(_median(ebits[-5:])) if len(ebits) >= 5 else None
    current = ebits[-1]
    peak = max(ebits)

    # Only normalize if cyclical or if current is >20% above median (peak bias guard)
    if median_5y is not None and (is_cyclical or (current > median_5y * 1.2)):
        norm = median_5y
        is_norm = True
    else:
        norm = current
        is_norm = False

    delta_vs_peak = round((norm - peak) / abs(peak) * 100.0, 1) if peak else 0.0

    # 10-yr range for context (US-0142)
    min_ebit = min(ebits) if ebits else None
    max_ebit = max(ebits) if ebits else None

    return {
        "company_id": company_id,
        "normalized_ebit": round(norm, 2) if norm is not None else None,
        "is_normalized": is_norm,
        "is_cyclical": is_cyclical,
        "median_5y": round(median_5y, 2) if median_5y is not None else None,
        "current_ebit": round(current, 2),
        "peak_ebit": round(peak, 2) if peak is not None else None,
        "min_10y": round(min_ebit, 2) if min_ebit is not None else None,
        "max_10y": round(max_ebit, 2) if max_ebit is not None else None,
        "delta_vs_peak_pct": delta_vs_peak,
    }


def decompose_implied_growth(db: Session, company_id: str, implied_g: float | None = None) -> dict[str, Any]:
    """Decompose implied 10-yr growth into volume/price/margin components where data allows (US-0122).

    Volume ≈ revenue CAGR, Price ≈ implied from CPI/producer proxy (not stored → insufficient),
    Margin recovery ≈ (current margin vs 5-yr median) contribution. Honest about missing price.
    """
    if implied_g is None:
        dcf = compute_and_store_reverse_dcf(db, company_id)
        implied_g = dcf.market_implied_growth_10y
    if implied_g is None:
        return {"status": "insufficient_data", "reason": "market_implied_growth_unavailable"}

    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == company_id, FinancialSnapshot.period_type == "FY").order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    dated = [s for s in snaps if s.fiscal_year is not None and s.revenue is not None and s.revenue > 0]
    if len(dated) < 3:
        return {"status": "insufficient_data", "reason": "requires_3_fy_revenue_for_decomposition"}

    # Volume: revenue CAGR
    start = dated[0].revenue
    end = dated[-1].revenue
    span = dated[-1].fiscal_year - dated[0].fiscal_year if dated[-1].fiscal_year and dated[0].fiscal_year else 1
    vol = ( (end / start) ** (1.0 / span) - 1.0) if start and span else 0.0

    # Margin recovery: compare current operating margin vs 5-yr median
    from statistics import median as _median

    margins = []
    for s in dated[-5:]:
        if s.ebit is not None and s.revenue not in (None, 0):
            margins.append(float(s.ebit) / float(s.revenue))
    median_margin = float(_median(margins)) if margins else None
    cur_margin = float(dated[-1].ebit) / float(dated[-1].revenue) if (dated[-1].ebit is not None and dated[-1].revenue) else None
    margin_recovery = None
    if median_margin is not None and cur_margin is not None and median_margin != 0:
        # If current margin below median, market may price margin recovery
        margin_recovery = round(cur_margin - median_margin, 4)

    # Price component: not locally stored (requires price-level deflators) → insufficient
    price_component = None

    return {
        "status": "computed",
        "implied_growth": round(implied_g, 4),
        "volume_component": round(vol, 4),
        "price_component": price_component,
        "price_note": "Price (inflation) component requires external deflator feed - not in local scope.",
        "margin_recovery_component": margin_recovery,
        "median_margin_5y": round(median_margin, 4) if median_margin is not None else None,
        "current_margin": round(cur_margin, 4) if cur_margin is not None else None,
    }


def compute_guided_dcf(
    db: Session,
    company_id: str,
    revenue_growth: float | None = None,
    operating_margin: float | None = None,
    wacc: float | None = None,
    terminal_g: float | None = None,
    years: int = 5,
    risk_free: float = 0.04,
    erp: float = 0.05,
    beta: float | None = None,
) -> dict[str, Any]:
    """Guided DCF sandbox (US-0101/US-0108/US-0125/US-0126/US-0145).

    Steps: Revenue → EBIT → NOPAT → FCF → Discount → Terminal → EV → Equity → per-share.
    Returns arithmetic resolution, WACC build, terminal %, and uncertainty range.
    """
    from app.services.penman_engine import is_financial_institution

    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    if is_financial_institution(company):
        return {
            "company_id": company_id,
            "status": "financial_institution_excluded",
            "reason": "FCF DCF not meaningful for banks/insurers - use DDM/Residual Income.",
            "is_financial": True,
            "disclaimer": "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
        }

    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == company_id, FinancialSnapshot.period_type == "FY").order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    dated = [s for s in snaps if s.fiscal_year is not None]
    seed = next((s for s in snaps if s.fiscal_year is None), None)
    latest = dated[-1] if dated else seed
    if latest is None:
        return {"company_id": company_id, "status": "insufficient_data", "reason": "no_snapshot"}

    # Defaults from history where user didn't override
    rev0 = float(latest.revenue) if latest and latest.revenue else (float(seed.revenue) if seed and seed.revenue else None)
    if rev0 is None or rev0 <= 0:
        return {"company_id": company_id, "status": "insufficient_data", "reason": "revenue_missing"}

    # Derive default growth/margin from history if not supplied
    if revenue_growth is None:
        # 3-yr revenue CAGR
        revs = [float(s.revenue) for s in dated[-4:] if s.revenue and s.revenue > 0]
        if len(revs) >= 2:
            span = (dated[-1].fiscal_year - dated[-len(revs)].fiscal_year) if dated[-1].fiscal_year and dated[-len(revs)].fiscal_year else 1
            revenue_growth = ( (revs[-1] / revs[0]) ** (1.0 / max(1, span)) - 1.0) if revs[0] > 0 else 0.05
            revenue_growth = max(-0.1, min(0.25, float(revenue_growth)))
        else:
            revenue_growth = 0.05
            thin_history = True
        # Will set thin flag below
    if operating_margin is None:
        # median operating margin last 5
        margins = [float(s.ebit) / float(s.revenue) for s in dated[-5:] if s.ebit is not None and s.revenue not in (None, 0)]
        if margins:
            from statistics import median as _median

            operating_margin = float(_median(margins))
        else:
            operating_margin = 0.15

    # WACC build
    # Try to fetch beta from key stats
    if beta is None:
        from app.models import CompanyKeyStats

        beta_row = db.execute(select(CompanyKeyStats).where(CompanyKeyStats.company_id == company_id, CompanyKeyStats.metric_name == "beta")).scalar_one_or_none()
        beta = float(beta_row.value) if beta_row and beta_row.value is not None else 1.0

    if wacc is None:
        wacc = risk_free + erp * float(beta)
    terminal_g = terminal_g if terminal_g is not None else DEFAULT_G_TERMINAL

    # Thin history warning
    thin_history = len(dated) < 3

    # Tax
    tax = 0.21
    if latest.ebit is not None and latest.net_income is not None and latest.ebit != 0:
        try:
            eff = 1.0 - float(latest.net_income) / float(latest.ebit)
            if 0 <= eff <= 0.5:
                tax = max(0.15, min(0.30, eff))
        except Exception:
            pass

    # Project
    rev = rev0
    pv_sum = 0.0
    steps: list[dict[str, Any]] = []
    fcf_series: list[float] = []
    for t in range(1, years + 1):
        rev *= (1.0 + revenue_growth)
        ebit = rev * operating_margin
        nopat = ebit * (1.0 - tax)
        # FCF proxy: NOPAT (simplified; capex/ΔWC not modeled per spec's plain-English sandbox)
        fcf = nopat
        pv = fcf / ((1.0 + wacc) ** t)
        pv_sum += pv
        fcf_series.append(fcf)
        steps.append({
            "year": t,
            "revenue": round(rev, 2),
            "ebit": round(ebit, 2),
            "nopat": round(nopat, 2),
            "fcf": round(fcf, 2),
            "discount_factor": round(1.0 / ((1.0 + wacc) ** t), 4),
            "pv_fcf": round(pv, 2),
            "formula": f"Year {t}: FCF {round(fcf,2)} / (1+{wacc:.3f})^{t} = {round(pv,2)}",
        })

    # Terminal value (Gordon)
    fcf_n = fcf_series[-1] if fcf_series else rev0 * operating_margin * (1.0 - tax)
    if wacc <= terminal_g:
        terminal_g = wacc - 0.02
    tv = fcf_n * (1.0 + terminal_g) / (wacc - terminal_g)
    pv_tv = tv / ((1.0 + wacc) ** years)
    ev = pv_sum + pv_tv

    # Equity value
    total_debt = float(latest.total_debt or 0) if latest else 0.0
    cash = float(latest.cash_st_investments or 0) if latest else 0.0
    net_debt = total_debt - cash
    equity_value = ev - net_debt
    shares = float(latest.shares_snapshot) if latest and latest.shares_snapshot else (float(seed.shares_snapshot) if seed and seed.shares_snapshot else None)
    per_share = (equity_value / shares) if (shares and shares > 0) else None

    # Terminal % warning
    terminal_pct = (pv_tv / ev * 100.0) if ev else 0.0
    terminal_heavy = terminal_pct > 70.0

    # Price comparison
    price = float(latest.price) if latest and latest.price else (float(seed.price) if seed and seed.price else None)
    premium_discount = None
    if price is not None and per_share not in (None, 0):
        premium_discount = round((price - per_share) / per_share * 100.0, 1)

    # Uncertainty range: 10th/50th/90th via ± growth/WACC shocks
    # 10th: growth -1.5pp, WACC +1pp; 90th: growth +1.5pp, WACC -1pp
    def _ev_at(g: float, w: float) -> float:
        r = rev0
        pv = 0.0
        for t in range(1, years + 1):
            r *= (1.0 + g)
            e = r * operating_margin * (1.0 - tax)
            pv += e / ((1.0 + w) ** t)
        fcf_last = r * operating_margin * (1.0 - tax)
        tg = terminal_g
        if w <= tg:
            tg = w - 0.02
        tv2 = fcf_last * (1.0 + tg) / (w - tg)
        return pv + tv2 / ((1.0 + w) ** years)

    ev_p10 = _ev_at(revenue_growth - 0.015, wacc + 0.01)
    ev_p90 = _ev_at(revenue_growth + 0.015, wacc - 0.01)
    eq_p10 = ev_p10 - net_debt
    eq_p90 = ev_p90 - net_debt
    ps_p10 = (eq_p10 / shares) if shares else None
    ps_p90 = (eq_p90 / shares) if shares else None

    return {
        "company_id": company_id,
        "currency": company.currency,
        "status": "computed",
        "inputs": {
            "revenue_growth": round(revenue_growth, 4),
            "operating_margin": round(operating_margin, 4),
            "wacc": round(wacc, 4),
            "terminal_g": round(terminal_g, 4),
            "years": years,
            "risk_free": risk_free,
            "erp": erp,
            "beta": round(float(beta), 2),
            "tax_rate": round(tax, 4),
            "thin_history": thin_history,
        },
        "wacc_build": {
            "risk_free": risk_free,
            "erp": erp,
            "beta": round(float(beta), 2),
            "formula": f"WACC = Rf ({risk_free:.2%}) + ERP ({erp:.2%}) × Beta ({float(beta):.2f}) = {wacc:.2%}",
            "wacc": round(wacc, 4),
        },
        "steps": steps,
        "fcf_series": [round(v, 2) for v in fcf_series],
        "pv_sum": round(pv_sum, 2),
        "terminal_value": round(tv, 2),
        "pv_terminal": round(pv_tv, 2),
        "enterprise_value": round(ev, 2),
        "net_debt": round(net_debt, 2),
        "equity_value": round(equity_value, 2),
        "shares": shares,
        "per_share": round(per_share, 2) if per_share is not None else None,
        "price": price,
        "premium_discount_pct": premium_discount,
        "terminal_pct": round(terminal_pct, 1),
        "terminal_heavy": terminal_heavy,
        "uncertainty_range": {
            "p10_per_share": round(ps_p10, 2) if ps_p10 is not None else None,
            "p50_per_share": round(per_share, 2) if per_share is not None else None,
            "p90_per_share": round(ps_p90, 2) if ps_p90 is not None else None,
        },
        "disclaimer": "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
        "method_version": "v1",
    }


def evaluate_reverse_dcf_hurdles(dcf_row: ValuationReverseDCF | None) -> dict[str, Any]:
    """Evaluates expectations gap and benchmarks against 8.0% Malkiel/Collins index hurdle."""
    if dcf_row is None or dcf_row.market_implied_growth_10y is None:
        return {
            "hurdle_rate": OPPORTUNITY_COST_HURDLE,
            "market_implied_growth_10y": None,
            "historical_5y_cagr": None,
            "expectations_gap": None,
            "hurdle_status": "insufficient_data",
            "gap_status": "insufficient_data",
            "hurdle_passed": False,
        }
    implied = dcf_row.market_implied_growth_10y
    gap = dcf_row.expectations_gap
    cagr = dcf_row.historical_5y_cagr

    hurdle_passed = implied <= OPPORTUNITY_COST_HURDLE
    hurdle_status = (
        f"Implied growth ({implied*100:.1f}%) exceeds the 8.0% Malkiel/Collins index opportunity cost hurdle."
        if not hurdle_passed
        else f"Implied growth ({implied*100:.1f}%) is within or below the 8.0% Malkiel/Collins index hurdle."
    )

    if gap is not None:
        if gap <= 0.02:
            gap_status = "low_expectations"
        elif gap <= 0.06:
            gap_status = "moderate_expectations"
        else:
            gap_status = "priced_for_perfection"
    else:
        gap_status = "unknown_gap"

    return {
        "hurdle_rate": OPPORTUNITY_COST_HURDLE,
        "market_implied_growth_10y": implied,
        "historical_5y_cagr": cagr,
        "expectations_gap": gap,
        "hurdle_passed": hurdle_passed,
        "hurdle_status": hurdle_status,
        "gap_status": gap_status,
    }