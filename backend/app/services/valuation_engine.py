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

    db.flush()
    return row
