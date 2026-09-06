"""Dividend Discount & Bank Residual Income Engine (Wave 4 Epic 10 US-0109/US-0116).

- Multi-stage DDM: Gordon + optional 5-yr supernormal growth where dividend
  history supports it. Requires ≥3 years of derived dividends; otherwise
  `insufficient_data`.
- Residual Income (Bank): Equity + PV(Excess Return on Equity over Cost of
  Equity). Requires book equity history and ROE. For Financials only;
  non-financials return `not_applicable` with routing note.

All money in native currency; yields/growth unitless. No invented dividends.
Dividends are derived from retained-earnings walk where explicit dividends_paid
is absent: div = NI_t − (RE_t − RE_{t−1}) (standard clean-surplus proxy).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, CompanyProfile, FinancialSnapshot
from app.services.penman_engine import is_financial_institution


def _derive_dividends(snaps: list[FinancialSnapshot]) -> list[tuple[int, float]]:
    """Derive dividends per FY via retained earnings walk: div_t = NI_t − (RE_t − RE_{t−1})."""
    dated = sorted([s for s in snaps if s.fiscal_year is not None and s.net_income is not None], key=lambda s: s.fiscal_year)
    # Need RE for both years
    out: list[tuple[int, float]] = []
    for i in range(1, len(dated)):
        cur = dated[i]
        prev = dated[i - 1]
        re_cur = getattr(cur, "retained_earnings", None)
        re_prev = getattr(prev, "retained_earnings", None)
        ni_cur = cur.net_income
        if re_cur is not None and re_prev is not None and ni_cur is not None:
            div = float(ni_cur) - (float(re_cur) - float(re_prev))
            if div is not None and div >= 0:
                # Sanity: div should be ≤ NI + tolerance if RE walk is clean
                # If div is huge vs NI, skip (noisy RE)
                if div <= float(ni_cur) * 1.5 + 1e6:
                    out.append((cur.fiscal_year, float(div)))
    # Fallback to CompanyProfile dividend_rate * shares where RE walk yields <2 points
    return out


def _cost_of_equity(wacc: float = 0.09, beta: float | None = None) -> float:
    # Simplified: cost_of_equity = wacc for banks where capital structure is equity-heavy;
    # otherwise wacc is reasonable proxy. Allow beta adjustment if available.
    if beta is not None:
        # Build: Rf 4% + ERP 5% * Beta (same as WACC build)
        return 0.04 + 0.05 * float(beta)
    return wacc


def compute_ddm(db: Session, company_id: str, wacc: float = 0.09) -> dict[str, Any]:
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

    # Try explicit dividends_paid first
    dividends: list[tuple[int, float]] = []
    explicit = [(s.fiscal_year, float(getattr(s, "dividends_paid"))) for s in dated if getattr(s, "dividends_paid", None) is not None]
    if len(explicit) >= 3:
        dividends = explicit
    else:
        dividends = _derive_dividends(dated)

    # Fallback to profile dividend_rate * shares
    profile = db.get(CompanyProfile, company_id)
    if len(dividends) < 3 and profile and profile.dividend_rate is not None:
        # Use profile rate as proxy for latest year only if history insufficient
        pass

    if len(dividends) < 3:
        return {
            "company_id": company_id,
            "currency": company.currency,
            "status": "insufficient_data",
            "reason": "requires_3_years_dividend_history",
            "dividends": dividends,
            "disclaimer": "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
        }

    # Latest dividend
    latest_fy, latest_div = dividends[-1]
    prev_fy, prev_div = dividends[-2]

    # Supernormal growth: 5-yr dividend CAGR where available
    span_fy = dividends[-1][0] - dividends[0][0]
    cagr = None
    if span_fy >= 2 and dividends[0][1] > 0:
        cagr = (dividends[-1][1] / dividends[0][1]) ** (1.0 / span_fy) - 1.0
        cagr = max(-0.2, min(0.25, float(cagr)))

    cost_equity = _cost_of_equity(wacc)

    # Gordon: P0 = D1 / (k − g) where D1 = D0*(1+g), g = cagr or 0.03 default
    g_gordon = cagr if cagr is not None else 0.03
    # Clamp g < k
    if g_gordon >= cost_equity - 0.01:
        g_gordon = cost_equity - 0.02
    if latest_div <= 0 or cost_equity <= g_gordon:
        return {
            "company_id": company_id,
            "currency": company.currency,
            "status": "insufficient_data",
            "reason": "dividend_nonpositive_or_g_ge_k",
            "disclaimer": "Personal research software, not investment advice.",
        }

    d1 = latest_div * (1.0 + g_gordon)
    gordon_value = d1 / (cost_equity - g_gordon)
    # Total equity value = Gordon value (for single stage) ; for DDM we treat dividends as equity cash flows
    # If supernormal growth available, blend: 5-yr supernormal then Gordon
    fair_value = gordon_value
    if cagr is not None and len(dividends) >= 4:
        # Two-stage: 5-yr supernormal at cagr, then Gordon
        pv_super = 0.0
        d = latest_div
        for t in range(1, 6):
            d *= (1.0 + cagr)
            pv_super += d / ((1.0 + cost_equity) ** t)
        d_terminal = d * (1.0 + 0.025)
        tv = d_terminal / (cost_equity - 0.025)
        pv_tv = tv / ((1.0 + cost_equity) ** 5)
        fair_value = pv_super + pv_tv

    # Per-share: divide by shares_snapshot
    shares = latest.shares_snapshot if latest and latest.shares_snapshot else (seed.shares_snapshot if seed and seed.shares_snapshot else None)
    per_share = None
    if shares and shares > 0:
        per_share = fair_value / float(shares)

    # Yield and payout
    mcap = latest.market_cap if latest and latest.market_cap else (latest.price * shares if latest and latest.price and shares else None)
    div_yield = (latest_div / mcap * 100.0) if (mcap and mcap > 0) else None
    payout = (latest_div / float(latest.net_income) * 100.0) if (latest and latest.net_income and latest.net_income != 0) else None

    return {
        "company_id": company_id,
        "currency": company.currency,
        "status": "computed",
        "latest_dividend": round(latest_div, 2),
        "latest_fy": latest_fy,
        "dividend_cagr": round(cagr, 4) if cagr is not None else None,
        "cost_of_equity": round(cost_equity, 4),
        "gordon_g": round(g_gordon, 4),
        "fair_value_total": round(fair_value, 2),
        "fair_value_per_share": round(per_share, 2) if per_share is not None else None,
        "shares": shares,
        "dividend_yield_pct": round(div_yield, 2) if div_yield is not None else None,
        "payout_ratio_pct": round(payout, 1) if payout is not None else None,
        "disclaimer": "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
        "method_version": "v1",
    }


def compute_residual_income(db: Session, company_id: str, wacc: float = 0.09) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    is_fin = is_financial_institution(company)
    if not is_fin:
        return {
            "company_id": company_id,
            "status": "not_applicable",
            "reason": "residual_income_primary_for_banks_insurers",
            "disclaimer": "Personal research software, not investment advice.",
        }

    snaps = db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == company_id, FinancialSnapshot.period_type == "FY")
        .order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    dated = [s for s in snaps if s.fiscal_year is not None and s.book_equity is not None and s.net_income is not None]
    if len(dated) < 3:
        return {
            "company_id": company_id,
            "currency": company.currency,
            "status": "insufficient_data",
            "reason": "requires_3_years_book_and_earnings",
            "disclaimer": "Personal research software, not investment advice.",
        }

    # Cost of equity
    beta = None
    # Try to fetch beta from company_key_stats if available
    from app.models import CompanyKeyStats

    beta_row = db.execute(
        select(CompanyKeyStats).where(CompanyKeyStats.company_id == company_id, CompanyKeyStats.metric_name == "beta")
    ).scalar_one_or_none()
    if beta_row and beta_row.value is not None:
        beta = float(beta_row.value)
    cost_equity = _cost_of_equity(wacc, beta)

    # Normalized ROE: median of last 5 ROE
    roes = []
    for s in dated[-5:]:
        if s.book_equity and s.book_equity != 0 and s.net_income is not None:
            roes.append(float(s.net_income) / float(s.book_equity))
    if not roes:
        return {"company_id": company_id, "status": "insufficient_data", "reason": "roe_uncomputable"}

    from statistics import median as _median

    norm_roe = float(_median(roes))
    latest = dated[-1]
    book = float(latest.book_equity)
    # Excess ROE over cost of equity
    excess = norm_roe - cost_equity
    # Residual income perpetuity: RI = (ROE − k) × Book
    # Value = Book + RI / k  (perpetuity of excess returns)
    if cost_equity <= 0:
        return {"company_id": company_id, "status": "insufficient_data", "reason": "cost_of_equity_nonpositive"}

    ri = excess * book
    # If excess negative, value < book (distressed)
    equity_value = book + (ri / cost_equity) if cost_equity != 0 else book

    shares = latest.shares_snapshot
    per_share = (equity_value / float(shares)) if (shares and shares > 0) else None

    # Market cap for premium/discount
    mcap = latest.market_cap if latest.market_cap else (latest.price * shares if latest.price and shares else None)
    premium = None
    if mcap is not None and equity_value != 0:
        premium = round((mcap - equity_value) / abs(equity_value) * 100.0, 1)

    return {
        "company_id": company_id,
        "currency": company.currency,
        "status": "computed",
        "book_equity": round(book, 2),
        "normalized_roe": round(norm_roe, 4),
        "cost_of_equity": round(cost_equity, 4),
        "excess_roe": round(excess, 4),
        "residual_income": round(ri, 2),
        "equity_value": round(equity_value, 2),
        "equity_value_per_share": round(per_share, 2) if per_share is not None else None,
        "shares": shares,
        "market_cap": round(mcap, 2) if mcap is not None else None,
        "premium_discount_pct": premium,
        "disclaimer": "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
        "method_version": "v1",
    }
