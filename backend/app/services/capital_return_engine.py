"""Simply Wall St-style Dilution & True Shareholder Yield Engine (Master Directive WS3/WS4).

Calculates:
1. Share count change 1-Year Delta and 3-Year CAGR.
2. Net Diluted Share Reduction (Net Repurchase Rate).
3. Stock-Based Compensation (SBC) Drag % of Revenue.
4. Gross Buyback Yield % vs SBC Dilution Offset % vs Net Buyback Yield %.
5. True Shareholder Yield (TSY Net) = Dividend Yield + Net Buyback Yield.
6. Forensic flags: DILUTIVE_BUYBACKS, ORGANIC_FLOAT_SHRINK, SHAREHOLDER_DILUTION, ACCELERATED_BUYBACKS.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, CompanyProfile, FinancialSnapshot


def compute_shareholder_yield(db: Session, company_id: str, fallback_proxies: bool = False) -> dict[str, Any]:
    """Computes share count dilution trends, SBC drag, net buyback yield, and true shareholder yield."""
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
    target_snaps = dated if dated else seed

    # Extract multi-year share counts and latest snapshot metrics
    share_series: list[tuple[int, float]] = []
    latest_snap = target_snaps[-1] if target_snaps else None
    seed_snap = seed[0] if seed else None

    for s in target_snaps:
        fy = s.fiscal_year or (s.as_of_date.year if s.as_of_date else None)
        shares = s.shares_snapshot
        if shares is None and s.net_income is not None and s.diluted_eps is not None and s.diluted_eps > 0 and s.net_income > 0:
            shares = s.net_income / s.diluted_eps
        if fy is not None and shares is not None and shares > 0:
            share_series.append((fy, shares))

    delta_1y_pct: float | None = None
    cagr_3y_pct: float | None = None
    net_repurchase_rate: float | None = None
    flags: list[str] = []

    if len(share_series) >= 2:
        curr_fy, curr_shares = share_series[-1]
        prev_fy, prev_shares = share_series[-2]
        delta_1y = ((curr_shares - prev_shares) / prev_shares) * 100.0
        delta_1y_pct = round(delta_1y, 2)
        net_repurchase_rate = round(-delta_1y, 2)

        if delta_1y > 2.0:
            flags.append("SHAREHOLDER_DILUTION")
        elif delta_1y < -2.0:
            flags.append("ACCELERATED_BUYBACKS")

    if len(share_series) >= 4:
        curr_fy, curr_shares = share_series[-1]
        t3_fy, t3_shares = share_series[-4]
        if t3_shares > 0 and curr_shares > 0:
            cagr = ((curr_shares / t3_shares) ** (1.0 / 3.0) - 1.0) * 100.0
            cagr_3y_pct = round(cagr, 2)
            if cagr > 2.0 and "SHAREHOLDER_DILUTION" not in flags:
                flags.append("SHAREHOLDER_DILUTION")
            elif cagr < -2.0 and "ACCELERATED_BUYBACKS" not in flags:
                flags.append("ACCELERATED_BUYBACKS")

    float_shrink_3y_pct: float | None = round(-cagr_3y_pct, 2) if cagr_3y_pct is not None else None
    cagr_5y_pct: float | None = None
    float_shrink_5y_pct: float | None = None
    if len(share_series) >= 6:
        curr_fy, curr_shares = share_series[-1]
        t5_fy, t5_shares = share_series[-6]
        if t5_shares > 0 and curr_shares > 0:
            cagr_5 = ((curr_shares / t5_shares) ** (1.0 / 5.0) - 1.0) * 100.0
            cagr_5y_pct = round(cagr_5, 2)
            float_shrink_5y_pct = round(-cagr_5, 2)

    # Determine Market Cap
    mcap: float | None = None
    if latest_snap and latest_snap.market_cap is not None and latest_snap.market_cap > 0:
        mcap = latest_snap.market_cap
    elif seed_snap and seed_snap.market_cap is not None and seed_snap.market_cap > 0:
        mcap = seed_snap.market_cap
    elif latest_snap and latest_snap.price is not None and latest_snap.shares_snapshot is not None:
        mcap = latest_snap.price * latest_snap.shares_snapshot
    elif seed_snap and seed_snap.price is not None and seed_snap.shares_snapshot is not None:
        mcap = seed_snap.price * seed_snap.shares_snapshot

    # Revenue
    rev = latest_snap.revenue if latest_snap and latest_snap.revenue else (seed_snap.revenue if seed_snap else None)

    # Cash Repurchases: explicit or derived from share contraction
    explicit_repurchases = getattr(latest_snap, "cash_repurchase_equity", None)
    if explicit_repurchases is not None and explicit_repurchases > 0:
        cash_repurchase = explicit_repurchases
    elif net_repurchase_rate is not None and net_repurchase_rate > 0 and mcap is not None and mcap > 0:
        cash_repurchase = (net_repurchase_rate / 100.0) * mcap
    else:
        cash_repurchase = 0.0

    # Stock-Based Compensation (SBC) - actual filings strictly required (Rule #3: Never invent numbers)
    explicit_sbc = getattr(latest_snap, "stock_based_compensation", None)
    if explicit_sbc is None and seed_snap is not None:
        explicit_sbc = getattr(seed_snap, "stock_based_compensation", None)

    if explicit_sbc is not None:
        sbc = explicit_sbc
        sbc_source = "filing"
    else:
        sbc = None
        sbc_source = "missing"

    # SBC Drag % of Revenue
    sbc_drag_pct: float | None = None
    if rev is not None and rev > 0 and sbc is not None:
        sbc_drag_pct = round((sbc / rev) * 100.0, 2)

    # Gross Buyback Yield %
    gross_buyback_yield_pct: float | None = None
    if mcap is not None and mcap > 0:
        gross_buyback_yield_pct = round((cash_repurchase / mcap) * 100.0, 2)
    elif net_repurchase_rate is not None and net_repurchase_rate > 0:
        gross_buyback_yield_pct = net_repurchase_rate

    # SBC Dilution Offset % of Market Cap
    sbc_offset_pct: float | None = None
    if mcap is not None and mcap > 0 and sbc is not None:
        sbc_offset_pct = round((sbc / mcap) * 100.0, 2)

    # Net Buyback Yield %: max(0, (Cash Repurchases - Actual SBC) / Market Cap * 100)
    net_buyback_yield: float | None = None
    actual_sbc = sbc if sbc is not None else 0.0
    if mcap is not None and mcap > 0:
        net_buyback_yield = round(max(0.0, ((cash_repurchase - actual_sbc) / mcap) * 100.0), 2)
    elif net_repurchase_rate is not None:
        net_buyback_yield = round(max(0.0, net_repurchase_rate - (sbc_offset_pct or 0.0)), 2)

    # Flags logic
    # DILUTIVE_BUYBACKS: Cash Repurchases > 0 but shares expanded YoY (net_repurchase_rate < 0)
    if cash_repurchase > 0 and (net_repurchase_rate is not None and net_repurchase_rate < 0):
        if "DILUTIVE_BUYBACKS" not in flags:
            flags.append("DILUTIVE_BUYBACKS")

    # ORGANIC_FLOAT_SHRINK: Net Repurchase Rate > 2.0% and SBC Drag < 3.0%
    if net_repurchase_rate is not None and net_repurchase_rate > 2.0:
        if sbc_drag_pct is not None and sbc_drag_pct < 3.0:
            if "ORGANIC_FLOAT_SHRINK" not in flags:
                flags.append("ORGANIC_FLOAT_SHRINK")

    # Dividend Yield
    div_yield_pct: float | None = None
    profile = db.query(CompanyProfile).filter_by(company_id=company_id).first()
    if profile and profile.dividend_yield is not None:
        raw_dy = profile.dividend_yield
        div_yield_pct = round(raw_dy * 100.0 if raw_dy <= 1.0 else raw_dy, 2)

    # Total Shareholder Yield (TSY)
    total_shareholder_yield: float | None = None
    true_shareholder_yield: float | None = None
    if net_buyback_yield is not None or div_yield_pct is not None:
        by_component = net_buyback_yield or 0.0
        dy_component = div_yield_pct or 0.0
        true_shareholder_yield = round(by_component + dy_component, 2)
        total_shareholder_yield = true_shareholder_yield

    # Dividend Safety Rating & FCF Payout
    fcf = latest_snap.fcf_calc if latest_snap else (seed_snap.fcf_calc if seed_snap else None)
    div_rate = profile.dividend_rate if profile else None
    shares_count = latest_snap.shares_snapshot if latest_snap else (seed_snap.shares_snapshot if seed_snap else None)
    div_paid = getattr(latest_snap, "dividends_paid", None) or (div_rate * shares_count if (div_rate and shares_count) else None)

    dividend_safety_rating = "No Dividend Paid"
    fcf_payout_ratio = None
    if div_paid and div_paid > 0:
        if fcf is not None and fcf > 0:
            fcf_payout_ratio = round((div_paid / fcf) * 100.0, 1)
            if fcf_payout_ratio <= 50.0:
                dividend_safety_rating = "Very Safe"
            elif fcf_payout_ratio <= 75.0:
                dividend_safety_rating = "Safe"
            elif fcf_payout_ratio <= 100.0:
                dividend_safety_rating = "Borderline"
            else:
                dividend_safety_rating = "Unsafe / High Risk"
        elif fcf is not None and fcf <= 0:
            dividend_safety_rating = "Unsafe (Negative FCF)"
        else:
            dividend_safety_rating = "Unknown"

    sbc_to_buyback_ratio = round((actual_sbc / cash_repurchase) * 100.0, 1) if (cash_repurchase > 0 and actual_sbc > 0) else None

    return {
        "company_id": company_id,
        "currency": company.currency,
        "share_count_history": [{"fiscal_year": fy, "diluted_shares": sh} for fy, sh in share_series[-5:]],
        "share_count_delta_1y_pct": delta_1y_pct,
        "share_count_cagr_3y_pct": cagr_3y_pct,
        "float_shrink_3y_pct": float_shrink_3y_pct,
        "float_shrink_5y_pct": float_shrink_5y_pct,
        "net_repurchase_rate_pct": net_repurchase_rate,
        "gross_buyback_yield_pct": gross_buyback_yield_pct,
        "sbc_drag_pct": sbc_drag_pct,
        "sbc_dilution_offset_pct": sbc_offset_pct,
        "sbc_to_buyback_ratio": sbc_to_buyback_ratio,
        "net_buyback_yield_pct": net_buyback_yield,
        "dividend_yield_pct": div_yield_pct,
        "dividend_safety_rating": dividend_safety_rating,
        "fcf_payout_ratio": fcf_payout_ratio,
        "total_shareholder_yield_pct": total_shareholder_yield,
        "true_shareholder_yield_pct": true_shareholder_yield,
        "flags": flags,
    }
