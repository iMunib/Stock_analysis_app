"""Multi-Metric Screener Engine with Institutional Presets and Dynamic Querying.

Filters across companies, financial_snapshots_ttm, valuation_reverse_dcf, and scores.
Respects strict currency rules and soft deletion.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Company, FinancialPenmanAnalysis, FinancialSnapshotTTM, Score, ScreenerPreset, ValuationReverseDCF

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
    {
        "id": "spus_halal_compounders",
        "name": "SPUS Halal Compounders",
        "criteria": {
            "universe": "SPUS",
            "composite_min": 6.5,
            "altman_zone": "Safe",
            "roic_min": 0.15,
        },
    },
    {
        "id": "qqq_secular_leaders",
        "name": "QQQ Secular Leaders",
        "criteria": {
            "universe": "QQQ",
            "fcf_yield_min": 0.02,
            "roic_min": 0.18,
        },
    },
    {
        "id": "deep_value_graham",
        "name": "Deep Value & Graham Floors",
        "criteria": {
            "universe": "VONV",
            "ev_ebitda_max": 12.0,
        },
    },
    {
        "id": "forensic_clean_sheet",
        "name": "Forensic Clean Sheet",
        "criteria": {
            "eqr_min": 80,
            "sloan_accrual_max": 0.05,
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
        else:
            row.name = p["name"]
            row.criteria_json = p["criteria"]
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
            Company.universe_tags,
            Score.composite,
            Score.signal,
            Score.percentiles_json,
            FinancialSnapshotTTM.roic,
            FinancialSnapshotTTM.fcf_yield,
            FinancialSnapshotTTM.ev_ebitda,
            FinancialSnapshotTTM.pe_ratio,
            FinancialSnapshotTTM.sloan_accrual_ratio,
            FinancialSnapshotTTM.cash_conversion_ratio,
            FinancialSnapshotTTM.eqr,
            ValuationReverseDCF.market_implied_growth_10y,
            ValuationReverseDCF.historical_5y_cagr,
            ValuationReverseDCF.expectations_gap,
            ValuationReverseDCF.status.label("dcf_status"),
            FinancialPenmanAnalysis.rnoa,
            FinancialPenmanAnalysis.flev,
        )
        .outerjoin(Score, Score.company_id == Company.company_id)
        .outerjoin(FinancialSnapshotTTM, FinancialSnapshotTTM.company_id == Company.company_id)
        .outerjoin(ValuationReverseDCF, ValuationReverseDCF.company_id == Company.company_id)
        .outerjoin(FinancialPenmanAnalysis, FinancialPenmanAnalysis.company_id == Company.company_id)
        .where(Company.is_deleted == False)
    )

    # Index / ETF Universe filter
    universe = criteria.get("universe")
    if universe and universe != "ALL":
        u_upper = universe.upper()
        if u_upper == "SP500":
            stmt = stmt.where(or_(Company.in_sp500 == True, Company.universe_tags.like('%"SP500"%')))
        elif u_upper in ("TSX", "TSX_COMPOSITE", "S&P/TSX"):
            stmt = stmt.where(or_(Company.in_tsx_composite == True, Company.universe_tags.like('%"TSX"%'), Company.country == "CA"))
        else:
            stmt = stmt.where(Company.universe_tags.like(f"%{u_upper}%"))

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
        if criteria.get("eqr_min") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.eqr >= float(criteria["eqr_min"]))
        if criteria.get("eqr_max") is not None:
            stmt = stmt.where(FinancialSnapshotTTM.eqr <= float(criteria["eqr_max"]))
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
        "eqr": FinancialSnapshotTTM.eqr,
        "expectations_gap": ValuationReverseDCF.expectations_gap,
        "name": Company.name,
        "ticker": Company.ticker,
    }.get(sort_by, Score.composite)

    order_expr = sort_col.desc().nullslast() if sort_dir == "desc" else sort_col.asc().nullslast()
    stmt = stmt.order_by(order_expr)

    # Execute
    results = db.execute(stmt.limit(limit * 2).offset(offset)).all()

    from app.services.distress_engine import compute_distress

    items = []
    for r in results:
        pcts = r.percentiles_json or {}
        tsy = pcts.get("total_shareholder_yield")
        val_pcts = [pcts[k] for k in ("pe_ratio", "ev_to_ebitda", "pb_ratio") if pcts.get(k) is not None]
        val_pct = round(sum(val_pcts) / len(val_pcts), 1) if val_pcts else None
        qual_pcts = [pcts[k] for k in ("roe", "roic_or_rnoa", "fcf_margin") if pcts.get(k) is not None]
        qual_pct = round(sum(qual_pcts) / len(qual_pcts), 1) if qual_pcts else None

        try:
            distress = compute_distress(db, r.company_id)
            altman_z = distress.get("active_z")
            altman_zone = distress.get("zone")
        except Exception:  # noqa: BLE001
            altman_z = None
            altman_zone = "Unknown"

        # Apply newly added screener criteria filters:
        if criteria.get("altman_zone") and criteria["altman_zone"] != "ALL":
            if altman_zone != criteria["altman_zone"]:
                continue
        if criteria.get("tsy_min") is not None:
            if tsy is None or tsy < float(criteria["tsy_min"]):
                continue
        if criteria.get("value_pct_min") is not None:
            if val_pct is None or val_pct < float(criteria["value_pct_min"]):
                continue
        if criteria.get("quality_pct_min") is not None:
            if qual_pct is None or qual_pct < float(criteria["quality_pct_min"]):
                continue

        items.append({
            "company_id": r.company_id,
            "ticker": r.ticker,
            "name": r.name,
            "currency": r.currency,
            "gics_sector": r.gics_sector,
            "custom_industry": r.custom_industry_sheet,
            "universe_tags": r.universe_tags or [],
            "composite": r.composite,
            "signal": r.signal,
            "roic": r.roic,
            "rnoa": r.rnoa,
            "flev": r.flev,
            "altman_z": altman_z,
            "altman_zone": altman_zone,
            "total_shareholder_yield": tsy,
            "value_percentile": val_pct,
            "quality_percentile": qual_pct,
            "fcf_yield": r.fcf_yield,
            "ev_ebitda": r.ev_ebitda,
            "pe_ratio": r.pe_ratio,
            "sloan_accrual_ratio": r.sloan_accrual_ratio,
            "cash_conversion_ratio": r.cash_conversion_ratio,
            "eqr": r.eqr,
            "market_implied_growth_10y": r.market_implied_growth_10y,
            "historical_5y_cagr": r.historical_5y_cagr,
            "expectations_gap": r.expectations_gap,
            "dcf_status": r.dcf_status,
        })
        if len(items) >= limit:
            break

    return {
        "items": items,
        "count": len(items),
        "limit": limit,
        "offset": offset,
    }
