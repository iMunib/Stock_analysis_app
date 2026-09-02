"""Multi-Metric Screener Engine with Institutional Presets and Dynamic Querying.

Filters across companies, financial_snapshots_ttm, valuation_reverse_dcf, and scores.
Respects strict currency rules and soft deletion.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshotTTM, Score, ScreenerPreset, ValuationReverseDCF

SYSTEM_PRESETS = [
    {
        "id": "buffett_burry_deep_value",
        "name": "Buffett-Burry Deep Value",
        "criteria": {
            "roic_min": 0.15,
            "ev_ebitda_max": 10.0,
            "fcf_yield_min": 0.07,
            "sloan_accrual_max": 0.05,
        },
    },
    {
        "id": "forensic_red_flags",
        "name": "Forensic Red Flags",
        "criteria": {
            "sloan_accrual_min": 0.10,
            "cash_conversion_max": 0.60,
            "flag_logic": "OR",
        },
    },
    {
        "id": "discounted_compounders",
        "name": "Discounted Compounders",
        "criteria": {
            "roic_min": 0.18,
            "expectations_gap_max": -0.04,
        },
    },
]


def ensure_system_presets(db: Session) -> list[ScreenerPreset]:
    """Ensures default institutional system presets are in the database."""
    presets = []
    for p in SYSTEM_PRESETS:
        row = db.get(ScreenerPreset, p["id"])
        if row is None:
            row = ScreenerPreset(
                id=p["id"],
                name=p["name"],
                criteria_json=p["criteria"],
                is_system_preset=True,
            )
            db.add(row)
        presets.append(row)
    db.commit()
    return presets


def run_screener_query(
    db: Session,
    criteria: dict[str, Any],
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Executes dynamic multi-parameter forensic screener query."""
    ensure_system_presets(db)

    # Base query: join Company with Score, TTM, and Reverse DCF
    stmt = (
        select(
            Company.company_id,
            Company.ticker,
            Company.name,
            Company.currency,
            Company.gics_sector,
            Company.custom_industry_sheet,
            Score.composite,
            Score.signal,
            FinancialSnapshotTTM.roic,
            FinancialSnapshotTTM.fcf_yield,
            FinancialSnapshotTTM.ev_ebitda,
            FinancialSnapshotTTM.pe_ratio,
            FinancialSnapshotTTM.sloan_accrual_ratio,
            FinancialSnapshotTTM.cash_conversion_ratio,
            ValuationReverseDCF.market_implied_growth_10y,
            ValuationReverseDCF.historical_5y_cagr,
            ValuationReverseDCF.expectations_gap,
            ValuationReverseDCF.status.label("dcf_status"),
        )
        .outerjoin(Score, Score.company_id == Company.company_id)
        .outerjoin(FinancialSnapshotTTM, FinancialSnapshotTTM.company_id == Company.company_id)
        .outerjoin(ValuationReverseDCF, ValuationReverseDCF.company_id == Company.company_id)
        .where(Company.is_deleted == False)
    )

    # Currency filter
    currency = criteria.get("currency")
    if currency and currency.upper() in ("USD", "CAD"):
        stmt = stmt.where(Company.currency == currency.upper())

    # Sector / Industry
    sector = criteria.get("sector")
    if sector:
        stmt = stmt.where(Company.gics_sector == sector)
    industry = criteria.get("industry")
    if industry:
        stmt = stmt.where(Company.custom_industry_sheet == industry)

    # Exclude banks
    if criteria.get("exclude_banks"):
        stmt = stmt.where(
            Company.custom_industry_sheet != "Banks",
            Company.gics_sector != "Financials",
        )

    # Signal
    signal = criteria.get("signal")
    if signal:
        stmt = stmt.where(Score.signal == signal)

    # Minimum composite
    composite_min = criteria.get("composite_min")
    if composite_min is not None:
        stmt = stmt.where(Score.composite >= float(composite_min))

    # Forensic bounds
    flag_logic = criteria.get("flag_logic", "AND")
    if flag_logic == "OR" and (criteria.get("sloan_accrual_min") is not None or criteria.get("cash_conversion_max") is not None):
        or_clauses = []
        if criteria.get("sloan_accrual_min") is not None:
            or_clauses.append(FinancialSnapshotTTM.sloan_accrual_ratio >= float(criteria["sloan_accrual_min"]))
        if criteria.get("cash_conversion_max") is not None:
            or_clauses.append(FinancialSnapshotTTM.cash_conversion_ratio <= float(criteria["cash_conversion_max"]))
        if or_clauses:
            stmt = stmt.where(or_(*or_clauses))
    else:
        # Standard AND filters
        if criteria.get("roic_min") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.roic >= float(criteria["roic_min"]))
        if criteria.get("ev_ebitda_max") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.ev_ebitda <= float(criteria["ev_ebitda_max"]))
        if criteria.get("fcf_yield_min") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.fcf_yield >= float(criteria["fcf_yield_min"]))
        if criteria.get("sloan_accrual_max") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.sloan_accrual_ratio <= float(criteria["sloan_accrual_max"]))
        if criteria.get("sloan_accrual_min") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.sloan_accrual_ratio >= float(criteria["sloan_accrual_min"]))
        if criteria.get("cash_conversion_min") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.cash_conversion_ratio >= float(criteria["cash_conversion_min"]))
        if criteria.get("cash_conversion_max") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.cash_conversion_ratio <= float(criteria["cash_conversion_max"]))
        if criteria.get("expectations_gap_max") is not None:
            stmt = stmt.where(ValuationReverseDCF.expectations_gap <= float(criteria["expectations_gap_max"]))
        if criteria.get("expectations_gap_min") is not None:
            stmt = stmt.where(ValuationReverseDCF.expectations_gap >= float(criteria["expectations_gap_min"]))

    # Sort
    sort_by = criteria.get("sort_by", "composite")
    sort_dir = criteria.get("sort_dir", "desc")
    sort_col = {
        "composite": Score.composite,
        "roic": FinancialSnapshotTTM.roic,
        "sloan_accrual": FinancialSnapshotTTM.sloan_accrual_ratio,
        "cash_conversion": FinancialSnapshotTTM.cash_conversion_ratio,
        "expectations_gap": ValuationReverseDCF.expectations_gap,
        "name": Company.name,
        "ticker": Company.ticker,
    }.get(sort_by, Score.composite)

    order_expr = sort_col.desc().nullslast() if sort_dir == "desc" else sort_col.asc().nullslast()
    stmt = stmt.order_by(order_expr)

    # Execute
    results = db.execute(stmt.limit(limit).offset(offset)).all()

    items = []
    for r in results:
        items.append({
            "company_id": r.company_id,
            "ticker": r.ticker,
            "name": r.name,
            "currency": r.currency,
            "gics_sector": r.gics_sector,
            "custom_industry": r.custom_industry_sheet,
            "composite": r.composite,
            "signal": r.signal,
            "roic": r.roic,
            "fcf_yield": r.fcf_yield,
            "ev_ebitda": r.ev_ebitda,
            "pe_ratio": r.pe_ratio,
            "sloan_accrual_ratio": r.sloan_accrual_ratio,
            "cash_conversion_ratio": r.cash_conversion_ratio,
            "market_implied_growth_10y": r.market_implied_growth_10y,
            "historical_5y_cagr": r.historical_5y_cagr,
            "expectations_gap": r.expectations_gap,
            "dcf_status": r.dcf_status,
        })

    return {
        "items": items,
        "count": len(items),
        "limit": limit,
        "offset": offset,
    }
