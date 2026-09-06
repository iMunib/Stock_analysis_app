"""Penman Reformulated Financial Statement Engine (Master Directive WS2).

Decomposes operating performance from financial leverage to neutralize the
buyback/low-equity ROIC distortion (e.g. AAPL-class):

    OA   = Total Assets - Cash & ST Investments
    OL   = Total Liabilities - Total Debt
    NOA  = OA - OL
    NFO  = Total Debt - Cash & ST Investments
    Check: Common Equity (book_equity) == NOA - NFO
    NOPAT = Operating Income x (1 - clamp(tax, 0.15, 0.30))
    RNOA  = NOPAT / NOA
    FLEV  = NFO / Common Equity
    NBC   = Net Interest x (1 - tax) / NFO
    ROE   = RNOA + FLEV x (RNOA - NBC)   (Penman DuPont)

Financial institutions (banks/insurers/credit) are excluded: their balance
sheets do not separate operating from financing activities - tag
`financial_institution_excluded`.

All formulas are deterministic and pure; storage lives in
`financial_penman_analysis` (see migration).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialPenmanAnalysis, FinancialSnapshot

FINANCIAL_CUSTOM_SHEETS = {"banks", "insurance", "credit services", "capital markets"}


def is_financial_institution(company: Company | None, custom_industry_sheet: str | None = None) -> bool:
    sector = (getattr(company, "gics_sector", None) or "").strip().lower()
    custom = (custom_industry_sheet or getattr(company, "custom_industry_sheet", None) or "").strip().lower()
    return sector == "financials" or custom in FINANCIAL_CUSTOM_SHEETS


def clamp_tax_rate(rate: float) -> float:
    return max(0.15, min(0.30, rate))


def compute_penman(snap: FinancialSnapshot) -> dict[str, Any] | None:
    """Pure Penman reformulation for one snapshot. None when data incomplete.

    Requires: total_assets, total_liabilities, total_debt, cash_st_investments,
    book_equity, and operating income (ebit, falling back to net_income).
    """
    ta = snap.total_assets
    tl = snap.total_liabilities
    debt = snap.total_debt
    cash = snap.cash_st_investments
    equity = snap.book_equity

    if ta is None or tl is None or debt is None or cash is None or equity is None:
        return None
    if ta <= 0:
        return None

    oa = ta - cash
    ol = tl - debt
    noa = oa - ol
    nfo = debt - cash

    op_inc = snap.ebit if snap.ebit is not None else snap.net_income
    if op_inc is None:
        return None

    # Effective tax: 21% default clamp (15%-30%); tax expense unavailable on snapshot rows.
    tax_rate = clamp_tax_rate(0.21)
    nopat = op_inc * (1.0 - tax_rate)

    rnoa = (nopat / noa) if noa and noa > 0 else None
    flev = (nfo / equity) if equity and equity != 0 else None
    nbc = None
    if nfo and nfo != 0 and snap.interest_expense is not None:
        nbc = (snap.interest_expense * (1.0 - tax_rate)) / nfo

    roe_operational_spread = None
    if rnoa is not None and nbc is not None and flev is not None:
        roe_operational_spread = rnoa - nbc

    # Identity check: equity == NOA - NFO (tolerance 2% of assets or 1e6 abs)
    identity_ok = None
    expected_equity = noa - nfo
    if expected_equity != 0:
        identity_ok = abs(expected_equity - equity) <= max(0.05 * ta, 1e6)

    # Buyback Distortion Alert (Task 2.4):
    # When headline ROIC/ROE > 30% but FLEV > 2.0 and RNOA < 15%:
    inv_cap = (equity + max(0.0, nfo)) if (equity is not None and nfo is not None) else None
    calc_roic = (nopat / inv_cap) if (inv_cap is not None and inv_cap > 0) else None
    headline_roic = getattr(snap, "roic", None) or snap.roe_calc or calc_roic
    buyback_distortion_alert = None
    if headline_roic is not None and headline_roic > 0.30:
        if flev is not None and flev > 2.0 and rnoa is not None and rnoa < 0.15:
            buyback_distortion_alert = "High ROIC is artificially inflated by debt-funded buybacks."

    leverage_distortion = bool(
        (flev is not None and flev > 2.0 and rnoa is not None and rnoa < 0.15)
        or (flev is not None and flev > 3.0)
        or (equity is not None and ta > 0 and equity < 0.10 * ta)
    )

    return {
        "oa": oa,
        "ol": ol,
        "noa": noa,
        "nfo": nfo,
        "nopat": nopat,
        "rnoa": rnoa,
        "flev": flev,
        "nbc": nbc,
        "roe_operational_spread": roe_operational_spread,
        "identity_ok": identity_ok,
        "leverage_distortion": leverage_distortion,
        "buyback_distortion_alert": buyback_distortion_alert,
        "tax_rate": tax_rate,
    }


def compute_and_store_penman(db: Session, company_id: str) -> list[FinancialPenmanAnalysis]:
    """Materializes Penman analysis for every balance-sheet-complete FY snapshot.

    Falls back to the owner-workbook seed row (which carries the full balance
    sheet: TA/TL/debt/equity/cash/EBIT) when provider FY rows lack total_debt.
    Seed analysis is labeled period_type="SEED" and fiscal_year stays NULL.
    """
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    if is_financial_institution(company):
        # Financial institutions: operating/financing split is not meaningful.
        # Store one exclusion row per company for UI surfacing.
        row = db.query(FinancialPenmanAnalysis).filter_by(company_id=company_id).first()
        if row is None:
            row = FinancialPenmanAnalysis(
                company_id=company_id,
                fiscal_year=None,
                period_type="FY",
                exclusion="financial_institution_excluded",
            )
            db.add(row)
            db.flush()
        return [row]

    snaps = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
    ).scalars().all()

    out: list[FinancialPenmanAnalysis] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    def _materialize(snap: FinancialSnapshot, period_type: str) -> None:
        result = compute_penman(snap)
        if result is None:
            return
        row = db.query(FinancialPenmanAnalysis).filter_by(
            company_id=company_id, fiscal_year=snap.fiscal_year, period_type=period_type
        ).first()
        if row is None:
            row = FinancialPenmanAnalysis(
                company_id=company_id, fiscal_year=snap.fiscal_year, period_type=period_type
            )
            db.add(row)
        row.noa = result["noa"]
        row.nfo = result["nfo"]
        row.nopat = result["nopat"]
        row.rnoa = round(result["rnoa"], 4) if result["rnoa"] is not None else None
        row.flev = round(result["flev"], 4) if result["flev"] is not None else None
        row.nbc = round(result["nbc"], 4) if result["nbc"] is not None else None
        row.roe_operational_spread = (
            round(result["roe_operational_spread"], 4) if result["roe_operational_spread"] is not None else None
        )
        row.identity_ok = result["identity_ok"]
        row.leverage_distortion = result["leverage_distortion"]
        row.exclusion = None
        row.computed_at = now
        out.append(row)

    for snap in snaps:
        if snap.fiscal_year is None:
            continue  # provider seed handling below
        if snap.total_debt is None:
            continue  # incomplete provider balance sheet; seed row covers the company
        _materialize(snap, snap.period_type or "FY")

    # Seed fallback: the owner workbook row always has the full balance sheet.
    seed = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_(None),
            FinancialSnapshot.period_type == "FY",
        )
    ).scalar_one_or_none()
    if seed is not None and seed.total_debt is not None:
        _materialize(seed, "SEED")

    db.flush()
    return out


def latest_penman(db: Session, company_id: str) -> FinancialPenmanAnalysis | None:
    """Most recent analysis row for the company (exclusion rows included)."""
    rows = compute_and_store_penman(db, company_id)
    if not rows:
        return None
    dated = [r for r in rows if r.fiscal_year is not None]
    if not dated:
        return rows[0]
    return max(dated, key=lambda r: r.fiscal_year)