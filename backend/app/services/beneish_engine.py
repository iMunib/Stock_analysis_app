"""Beneish M-Score 8-Variable Forensic Earnings Manipulation Engine (Master Directive WS2).

Implements the standard 8-variable Beneish (1999) manipulation detection model:
1. DSRI: Days Sales in Receivables Index
2. GMI: Gross Margin Index
3. AQI: Asset Quality Index
4. SGI: Sales Growth Index
5. DEPI: Depreciation Index
6. SGAI: Sales, General & Administrative Expenses Index
7. LVGI: Leverage Index
8. TATA: Total Accruals to Total Assets

Formula:
M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.037*TATA + 0.0327*LVGI

Thresholds:
- M > -1.78: High probability of earnings manipulation (Manipulator / Red Flag)
- M <= -1.78: Low probability of manipulation (Non-manipulator / Clean)

Excludes financial institutions (Banks, Insurers) where asset-liability structures
render standard corporate accrual ratios invalid.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.penman_engine import is_financial_institution


def _safe_div(num: float | None, denom: float | None, default: float = 1.0) -> float:
    if num is None or denom is None or abs(denom) < 1e-9:
        return default
    return num / denom


def compute_beneish_m_score(db: Session, company_id: str, strict: bool = False) -> dict[str, Any]:
    """Computes the 8-variable Beneish M-Score and manipulation classification."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    # Financial institutions exclusion
    if is_financial_institution(company):
        return {
            "company_id": company_id,
            "status": "financial_institution_excluded",
            "data_available": False,
            "beneish_score": None,
            "m_score": None,
            "is_manipulator": False,
            "zone": "Excluded",
            "threshold": -1.78,
            "variables": None,
            "message": "Financial institutions excluded from Beneish M-Score analysis.",
            "interpretation": "Financial institution - excluded from industrial accrual models.",
        }

    # Fetch chronologically sorted annual snapshots with non-null financials
    snaps = db.execute(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
        .order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()

    # Prioritize dated annual statements with revenue
    dated = [s for s in snaps if s.fiscal_year is not None and s.revenue is not None and s.revenue > 0]
    if len(dated) < 2:
        # Check if we have at least one dated and one seed snapshot
        all_snaps = [s for s in snaps if s.revenue is not None and s.revenue > 0]
        if len(all_snaps) < 2:
            return {
                "company_id": company_id,
                "status": "insufficient_data",
                "data_available": False,
                "beneish_score": None,
                "m_score": None,
                "is_manipulator": False,
                "zone": "Insufficient Data",
                "threshold": -1.78,
                "variables": None,
                "message": "Requires at least 2 consecutive fiscal periods to compute Beneish indices.",
                "interpretation": "Insufficient historical statements on file.",
            }
        dated = all_snaps

    # Current period t (latest) and previous period t-1
    t = dated[-1]
    t_prev = dated[-2]

    rev_t = t.revenue or 1.0
    rev_prev = t_prev.revenue or 1.0

    gp_t = t.gross_profit if t.gross_profit is not None else (rev_t - (t.ebit or 0.0) * 0.7)
    gp_prev = t_prev.gross_profit if t_prev.gross_profit is not None else (rev_prev - (t_prev.ebit or 0.0) * 0.7)

    ta_t = t.total_assets or (t.book_equity or 1.0) * 2.0
    ta_prev = t_prev.total_assets or (t_prev.book_equity or 1.0) * 2.0

    ni_t = t.net_income if t.net_income is not None else 0.0
    cfo_t = t.operating_cash_flow if t.operating_cash_flow is not None else ni_t

    ebit_t = t.ebit if t.ebit is not None else 0.0
    ebit_prev = t_prev.ebit if t_prev.ebit is not None else 0.0

    ebitda_t = t.ebitda if t.ebitda is not None else ebit_t * 1.2
    ebitda_prev = t_prev.ebitda if t_prev.ebitda is not None else ebit_prev * 1.2

    debt_t = t.total_debt or 0.0
    debt_prev = t_prev.total_debt or 0.0

    # 1. DSRI (Days Sales in Receivables Index)
    # Genuine formula: (Receivables_t / Sales_t) / (Receivables_{t-1} / Sales_{t-1})
    ar_t = getattr(t, "accounts_receivable", None)
    ar_prev = getattr(t_prev, "accounts_receivable", None)
    has_genuine_ar = (ar_t is not None and ar_prev is not None and rev_t > 0 and rev_prev > 0)
    if has_genuine_ar:
        rec_to_rev_t = ar_t / rev_t
        rec_to_rev_prev = ar_prev / rev_prev
        dsri = _safe_div(rec_to_rev_t, rec_to_rev_prev, 1.0)
    else:
        rec_to_rev_t = 0.14
        rec_to_rev_prev = 0.14
        dsri = 1.0

    # 2. GMI (Gross Margin Index)
    gm_t = _safe_div(gp_t, rev_t, 0.35)
    gm_prev = _safe_div(gp_prev, rev_prev, 0.35)
    gmi = _safe_div(gm_prev, gm_t, 1.0)

    # 3. AQI (Asset Quality Index)
    # Genuine formula: Non-Current Assets = Total Assets - Current Assets - Net PP&E
    ca_t_raw = getattr(t, "current_assets", None)
    ca_prev_raw = getattr(t_prev, "current_assets", None)
    ppe_t_raw = getattr(t, "ppe_net", None)
    ppe_prev_raw = getattr(t_prev, "ppe_net", None)
    has_genuine_aqi = (
        ca_t_raw is not None and ca_prev_raw is not None and
        ppe_t_raw is not None and ppe_prev_raw is not None and
        ta_t > 0 and ta_prev > 0
    )

    if has_genuine_aqi:
        ca_t = ca_t_raw
        ca_prev = ca_prev_raw
        ppe_t = ppe_t_raw
        ppe_prev = ppe_prev_raw
        nca_t = max(0.0, ta_t - ca_t - ppe_t)
        nca_prev = max(0.0, ta_prev - ca_prev - ppe_prev)
        aqi = _safe_div(nca_t / ta_t, nca_prev / ta_prev, 1.0)
    else:
        ca_t = ca_t_raw or (t.cash_st_investments or 0.0) + 0.35 * max(0.0, ta_t - (t.cash_st_investments or 0.0))
        ca_prev = ca_prev_raw or (t_prev.cash_st_investments or 0.0) + 0.35 * max(0.0, ta_prev - (t_prev.cash_st_investments or 0.0))
        ppe_t = ppe_t_raw or max(0.0, ta_t - ca_t) * 0.7
        ppe_prev = ppe_prev_raw or max(0.0, ta_prev - ca_prev) * 0.7
        non_ca_t = 1.0 - _safe_div(ca_t + ppe_t, ta_t, 0.8)
        non_ca_prev = 1.0 - _safe_div(ca_prev + ppe_prev, ta_prev, 0.8)
        aqi = _safe_div(max(0.01, non_ca_t), max(0.01, non_ca_prev), 1.0)

    # 4. SGI (Sales Growth Index)
    sgi = _safe_div(rev_t, rev_prev, 1.0)

    # 5. DEPI (Depreciation Index)
    dep_t = getattr(t, "depreciation_amortization", None) or max(0.0, ebitda_t - ebit_t)
    dep_prev = getattr(t_prev, "depreciation_amortization", None) or max(0.0, ebitda_prev - ebit_prev)
    dep_rate_t = _safe_div(dep_t, dep_t + ppe_t, 0.08)
    dep_rate_prev = _safe_div(dep_prev, dep_prev + ppe_prev, 0.08)
    depi = _safe_div(dep_rate_prev, dep_rate_t, 1.0)

    # 6. SGAI (SG&A Expenses Index)
    sga_t_raw = getattr(t, "sga_expense", None)
    sga_prev_raw = getattr(t_prev, "sga_expense", None)
    if sga_t_raw is not None and sga_prev_raw is not None and rev_t > 0 and rev_prev > 0:
        sga_ratio_t = sga_t_raw / rev_t
        sga_ratio_prev = sga_prev_raw / rev_prev
        sgai = _safe_div(sga_ratio_t, sga_ratio_prev, 1.0)
    else:
        sga_t = sga_t_raw or max(0.0, gp_t - ebit_t)
        sga_prev = sga_prev_raw or max(0.0, gp_prev - ebit_prev)
        sga_ratio_t = _safe_div(sga_t, rev_t, 0.20)
        sga_ratio_prev = _safe_div(sga_prev, rev_prev, 0.20)
        sgai = _safe_div(sga_ratio_t, sga_ratio_prev, 1.0)

    # 7. LVGI (Leverage Index)
    lev_t = _safe_div(debt_t, ta_t, 0.30)
    lev_prev = _safe_div(debt_prev, ta_prev, 0.30)
    lvgi = _safe_div(lev_t, lev_prev, 1.0)

    # 8. TATA (Total Accruals to Total Assets)
    tata = _safe_div(ni_t - cfo_t, ta_t, 0.0)

    data_available = bool(has_genuine_ar and has_genuine_aqi)
    if strict and not data_available:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "data_available": False,
            "beneish_score": None,
            "m_score": None,
            "is_manipulator": False,
            "zone": "Insufficient Data",
            "threshold": -1.78,
            "variables": None,
            "message": "Required genuine historical line items (accounts receivable, current assets, net PP&E) are absent.",
            "interpretation": "Insufficient genuine statement lines on file.",
        }

    # Clamp index variables to robust domain (prevent wild infinity / negative distortions)
    dsri = max(0.1, min(5.0, dsri))
    gmi = max(0.1, min(5.0, gmi))
    aqi = max(0.1, min(5.0, aqi))
    sgi = max(0.1, min(5.0, sgi))
    depi = max(0.1, min(5.0, depi))
    sgai = max(0.1, min(5.0, sgai))
    lvgi = max(0.1, min(5.0, lvgi))
    tata = max(-1.0, min(1.0, tata))

    # 8-Variable Beneish M-Score Formula
    m_score = (
        -4.84
        + 0.920 * dsri
        + 0.528 * gmi
        + 0.404 * aqi
        + 0.892 * sgi
        + 0.115 * depi
        - 0.172 * sgai
        + 4.037 * tata
        + 0.0327 * lvgi
    )

    m_score_rounded = round(m_score, 2)
    is_manipulator = m_score > -1.78
    zone = "Manipulator" if is_manipulator else "Non-manipulator"
    interp = (
        "High probability of earnings manipulation (M > -1.78). Investigate revenue recognition and accruals."
        if is_manipulator
        else "Low probability of earnings manipulation (M <= -1.78). Normal earnings quality profile."
    )

    return {
        "company_id": company_id,
        "fiscal_year": t.fiscal_year,
        "status": "computed",
        "data_available": data_available,
        "beneish_score": m_score_rounded if data_available else None,
        "m_score": m_score_rounded,
        "is_manipulator": is_manipulator,
        "zone": zone,
        "threshold": -1.78,
        "variables": {
            "dsri": round(dsri, 3),
            "gmi": round(gmi, 3),
            "aqi": round(aqi, 3),
            "sgi": round(sgi, 3),
            "depi": round(depi, 3),
            "sgai": round(sgai, 3),
            "lvgi": round(lvgi, 3),
            "tata": round(tata, 3),
        },
        "interpretation": interp,
        "data_quality_flags": [] if data_available else ["HEURISTIC_LINES_USED"],
    }