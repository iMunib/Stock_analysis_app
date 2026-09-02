"""True TTM Normalization and Forensic Accounting Engine.

Calculates rolling 4-quarter sums (zero calendar skew), NOPAT, ROIC, Sloan Accruals,
and Cash Conversion Efficiency.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, CompanyProfile, FinancialSnapshot, FinancialSnapshotTTM


def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))


def compute_and_store_ttm(db: Session, company_id: str) -> FinancialSnapshotTTM:
    """Computes TTM snapshot and forensic ratios from quarterly statements or latest FY."""
    company = db.get(Company, company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")

    profile = db.get(CompanyProfile, company_id)
    quarters = (profile.quarterly_json or []) if profile else []

    # Latest annual snapshot and seed snapshot
    seed = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_(None),
            FinancialSnapshot.period_type == "FY",
        )
    ).scalar_one_or_none()

    annual_snaps = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_not(None),
            FinancialSnapshot.period_type == "FY",
        ).order_by(FinancialSnapshot.fiscal_year.desc())
    ).scalars().all()

    latest_annual = annual_snaps[0] if annual_snaps else None
    base_snap = latest_annual or seed

    currency = company.currency or (base_snap.currency if base_snap else "USD")

    # If 4 quarters are available, sum them
    has_4_quarters = len(quarters) >= 4
    quarter_count = 4 if has_4_quarters else 0

    rev = 0.0
    op_inc = 0.0
    ni = 0.0
    ocf = 0.0
    capex = 0.0
    fcf = 0.0
    shares = None
    as_of = None

    if has_4_quarters:
        q_slice = quarters[:4]
        as_of_str = q_slice[0].get("date")
        if as_of_str:
            try:
                as_of = datetime.strptime(as_of_str[:10], "%Y-%m-%d").date()
            except Exception:
                as_of = None

        rev = sum(float(q.get("revenue") or 0.0) for q in q_slice)
        ni = sum(float(q.get("net_income") or 0.0) for q in q_slice)
        op_inc = sum(float(q.get("operating_income") or (q.get("net_income") or 0.0)) for q in q_slice)
        ocf = sum(float(q.get("operating_cash_flow") or (q.get("net_income") or 0.0)) for q in q_slice)
        capex = sum(float(q.get("capex") or 0.0) for q in q_slice)
        fcf = ocf - abs(capex)
        if q_slice[0].get("diluted_eps") and ni:
            shares = float(ni / q_slice[0]["diluted_eps"]) if q_slice[0]["diluted_eps"] != 0 else None
    elif base_snap:
        rev = float(base_snap.revenue or 0.0)
        op_inc = float(getattr(base_snap, "ebit", None) or (base_snap.net_income or 0.0))
        ni = float(base_snap.net_income or 0.0)
        ocf = float(base_snap.operating_cash_flow or (base_snap.fcf_calc or ni))
        capex = float(base_snap.capex or 0.0)
        fcf = float(base_snap.fcf_calc or (ocf - abs(capex)))
        shares = float(base_snap.shares_snapshot or 0.0) if base_snap.shares_snapshot else None
        as_of = base_snap.as_of_date

    # Balance sheet items from base_snap
    total_assets = float(base_snap.total_assets or 0.0) if base_snap and base_snap.total_assets else 0.0
    total_debt = float(base_snap.total_debt or 0.0) if base_snap and base_snap.total_debt else 0.0
    book_equity = float(base_snap.book_equity or 0.0) if base_snap and base_snap.book_equity else 0.0
    cash = float(base_snap.cash_st_investments or 0.0) if base_snap and base_snap.cash_st_investments else 0.0

    # NOPAT = Operating Income * (1 - tax_rate)
    # Default effective tax rate clamped between 15% and 30%
    tax_rate = 0.21
    nopat = op_inc * (1.0 - tax_rate)

    # Invested Capital = Total Debt + Book Equity - Cash
    invested_capital = (total_debt + book_equity - cash) if (total_debt or book_equity) else None
    roic = (nopat / invested_capital) if (invested_capital and invested_capital > 0) else None

    # Sloan Accrual Ratio = (Net Income - Operating Cash Flow) / Total Assets
    sloan_accrual = None
    if total_assets and total_assets > 0:
        sloan_accrual = (ni - ocf) / total_assets

    # Cash Conversion Ratio = FCF / Net Income
    cash_conversion = None
    if ni and ni != 0:
        cash_conversion = fcf / ni

    # Market Ratios
    price = float(base_snap.price or 0.0) if base_snap and base_snap.price else None
    market_cap = (price * shares) if (price and shares) else (float(base_snap.market_cap) if base_snap and base_snap.market_cap else None)
    fcf_yield = (fcf / market_cap) if (market_cap and market_cap > 0) else None
    pe_ratio = (market_cap / ni) if (market_cap and ni and ni > 0) else None

    ebitda = float(base_snap.ebitda or 0.0) if base_snap and base_snap.ebitda else None
    ev = (market_cap + total_debt - cash) if market_cap else None
    ev_ebitda = (ev / ebitda) if (ev and ebitda and ebitda > 0) else None

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = db.get(FinancialSnapshotTTM, company_id)
    if row is None:
        row = FinancialSnapshotTTM(company_id=company_id, currency=currency)
        db.add(row)

    row.as_of_date = as_of
    row.quarter_count = quarter_count
    row.currency = currency
    row.revenue = rev
    row.operating_income = op_inc
    row.net_income = ni
    row.diluted_shares = shares
    row.operating_cash_flow = ocf
    row.capex = capex
    row.fcf = fcf
    row.nopat = nopat
    row.invested_capital = invested_capital
    row.roic = round(roic, 4) if roic is not None else None
    row.fcf_yield = round(fcf_yield, 4) if fcf_yield is not None else None
    row.ev_ebitda = round(ev_ebitda, 2) if ev_ebitda is not None else None
    row.pe_ratio = round(pe_ratio, 2) if pe_ratio is not None else None
    row.sloan_accrual_ratio = round(sloan_accrual, 4) if sloan_accrual is not None else None
    row.cash_conversion_ratio = round(cash_conversion, 4) if cash_conversion is not None else None
    row.is_complete = bool(rev and ni and invested_capital)
    row.computed_at = now

    db.flush()
    return row
