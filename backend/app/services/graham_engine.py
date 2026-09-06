"""Graham Intrinsic Value Floors (Master Directive WS4).

Absolute margin-of-safety models from The Intelligent Investor:

    Graham Number = sqrt(22.5 x EPS x BVPS)          (null if EPS<=0 or BVPS<=0)
    NCAV/share    = (Current Assets - Total Liabilities - Preferred) / Shares
    NNWC/share    = (Cash + 0.75xAR + 0.50xInventory - Total Liabilities) / Shares
    Margin of Safety = (Metric - Price) / Price

Current schema has no current-assets/AR/inventory breakdown, so NCAV/NNWC use
a documented conservative proxy when those lines are absent and are marked
`proxy: true` in the payload; they are NULL rather than fabricated whenever a
required total is missing entirely. Graham Number uses only EPS/BVPS/price and
is always exact when EPS and equity are on file.
"""
from __future__ import annotations

import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot


def _proxy_current_assets(snap: FinancialSnapshot) -> float | None:
    """Conservative proxy when the balance-sheet detail is absent:
    current assets ~ cash + 0.35 x (total assets - cash) - i.e. assumes the
    remaining asset base is ~35% current (below-typical, deliberately strict)."""
    ta = snap.total_assets
    cash = snap.cash_st_investments
    if ta is None or cash is None or ta <= 0:
        return None
    return cash + 0.35 * (ta - cash)


def compute_graham(db: Session, company_id: str) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    seed = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_(None),
            FinancialSnapshot.period_type == "FY",
        )
    ).scalar_one_or_none()
    latest = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_not(None),
            FinancialSnapshot.period_type == "FY",
        ).order_by(FinancialSnapshot.fiscal_year.desc())
    ).scalars().first()
    snap = latest or seed
    if snap is not None and (snap.diluted_eps is None or snap.book_equity is None or snap.price is None) and seed is not None:
        snap = seed

    out: dict[str, Any] = {
        "company_id": company_id,
        "currency": company.currency,
        "price": None,
        "graham_number": None,
        "graham_margin_of_safety": None,
        "ncav_per_share": None,
        "ncav_margin_of_safety": None,
        "nnwc_per_share": None,
        "nnwc_margin_of_safety": None,
        "deep_net_net": False,
        "proxy": False,
        "basis_note": ("owner-workbook seed row" if (snap is not None and snap.fiscal_year is None) else None),
        "basis_fiscal_year": snap.fiscal_year if snap else None,
    }
    if snap is None:
        out["reason"] = "no snapshots on file"
        return out

    price = snap.price
    shares = snap.shares_snapshot
    out["price"] = price

    eps = snap.diluted_eps
    bvps = (snap.book_equity / shares) if (snap.book_equity and shares and shares > 0) else None
    if eps is not None and eps > 0 and bvps is not None and bvps > 0:
        gn = math.sqrt(22.5 * eps * bvps)
        out["graham_number"] = round(gn, 2)
        if price:
            out["graham_margin_of_safety"] = round((gn - price) / price, 4)

    # NCAV / NNWC: exact when detail exists; documented proxy otherwise.
    tl = snap.total_liabilities
    ca = getattr(snap, "current_assets", None)
    proxy = False
    if ca is None:
        ca = _proxy_current_assets(snap)
        proxy = True
    if shares and shares > 0 and ca is not None and tl is not None:
        ncav = (ca - tl) / shares
        out["ncav_per_share"] = round(ncav, 2)
        if price:
            out["ncav_margin_of_safety"] = round((ncav - price) / price, 4)
            out["deep_net_net"] = price < ncav
    ar = getattr(snap, "accounts_receivable", None)
    inv = getattr(snap, "inventory", None)
    cash = snap.cash_st_investments
    if shares and shares > 0 and tl is not None and cash is not None and ar is not None and inv is not None:
        nnwc = (cash + 0.75 * ar + 0.50 * inv - tl) / shares
        out["nnwc_per_share"] = round(nnwc, 2)
        if price:
            out["nnwc_margin_of_safety"] = round((nnwc - price) / price, 4)
    out["proxy"] = proxy
    return out