"""Multi-Metric Screener Engine with Institutional Presets and Dynamic Querying.

Filters across companies, financial_snapshots_ttm, valuation_reverse_dcf, and scores.
Respects strict currency rules and soft deletion.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select
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
    {
        "id": "buffett_munger_quality_compounders",
        "name": "Buffett-Munger Quality Compounders",
        "criteria": {
            "roic_min": 0.15,
            "fcf_yield_min": 0.03,
            "sloan_accrual_max": 0.05,
            "eqr_min": 80,
        },
    },
    {
        "id": "graham_deep_value_net_nets",
        "name": "Graham Deep Value Net-Nets & Margins",
        "criteria": {
            "ev_ebitda_max": 10.0,
            "expectations_gap_max": 0.0,
        },
    },
    {
        "id": "cannibal_capital_compounders",
        "name": "Cannibal Capital Return Compounders",
        "criteria": {
            "fcf_yield_min": 0.04,
            "sloan_accrual_max": 0.05,
        },
    },
    {
        "id": "dorsey_wide_moat_franchises",
        "name": "Dorsey Wide Moat Franchises",
        "criteria": {
            "roic_min": 0.18,
            "eqr_min": 80,
        },
    },
    {
        "id": "forensic_red_flag_warning",
        "name": "Forensic Red Flag Early Warning / Short Watch",
        "criteria": {
            "sloan_accrual_min": 0.10,
            "eqr_max": 50,
            "flag_logic": "OR",
        },
    },
    # Certified Literature Presets (Phase 4 Task 4.1):
    {
        "id": "greenblatt_magic_formula",
        "name": "Greenblatt Magic Formula",
        "criteria": {
            "quality_pct_min": 85.0,
            "value_pct_min": 85.0,
        },
    },
    {
        "id": "graham_net_net_bargains",
        "name": "Graham Net-Net Bargains",
        "criteria": {
            "graham_net_net": True,
        },
    },
    {
        "id": "peter_lynch_growth_compounders",
        "name": "Peter Lynch Growth Compounders",
        "criteria": {
            "peg_max": 1.0,
            "roic_min": 0.15,
            "de_max": 0.5,
        },
    },
    {
        "id": "piotroski_high_quality_turnarounds",
        "name": "Piotroski High-Quality Turnarounds",
        "criteria": {
            "f_score_min": 8,
            "altman_zone": "Safe",
        },
    },
    {
        "id": "true_shareholder_yield_leaders",
        "name": "True Shareholder Yield Leaders",
        "criteria": {
            "tsy_min": 6.0,
        },
    },
    {
        "id": "aaoifi_halal_candidates",
        "name": "AAOIFI Halal Candidates",
        "criteria": {
            "halal_candidate": True,
        },
    },
    {
        "id": "sustainable_dividends",
        "name": "Sustainable Dividends (10+ Yrs & Payout < 60%)",
        "criteria": {
            "consecutive_div_years_min": 5,
            "payout_ratio_max": 0.60,
            "composite_min": 5.5,
        },
    },
    {
        "id": "garp_investor",
        "name": "GARP (Growth at Reasonable Price)",
        "criteria": {
            "peg_max": 1.2,
            "fcf_margin_min": 5.0,
            "composite_min": 6.0,
        },
    },
    {
        "id": "novy_marx_gross_profitability",
        "name": "Novy-Marx Gross Profitability",
        "criteria": {
            "gross_profitability_min": 0.25,
            "composite_min": 6.0,
            "exclude_banks": True,
        },
    },
    {
        "id": "fortress_balance_sheet",
        "name": "Retiree Fortress Balance Sheet",
        "criteria": {
            "debt_to_ebitda_max": 3.0,
            "interest_coverage_min": 8.0,
            "exclude_banks": True,
        },
    },
    {
        "id": "boring_great_businesses",
        "name": "Boring Great Businesses",
        "criteria": {
            "roe_min": 15.0,
            "debt_to_ebitda_max": 2.0,
            "altman_safe_only": True,
            "exclude_banks": True,
        },
    },
    {
        "id": "operational_turnarounds",
        "name": "Cash-Flow Positive Turnarounds",
        "criteria": {
            "turnaround_only": True,
        },
    },
    {
        "id": "durable_growth_compounders",
        "name": "Durable Growth Compounders",
        "criteria": {
            "cagr_rev_3y_min": 0.15,
            "has_growth_history": True,
        },
    },
    {
        "id": "contrarian_deep_value",
        "name": "Contrarian Deep Value",
        "criteria": {
            "pe_max": 12.0,
            "composite_min": 5.0,
        },
    },
    {
        "id": "steady_compounders",
        "name": "Steady Compounders (Drawdown Resilient)",
        "criteria": {
            "cagr_rev_3y_min": 0.05,
            "composite_min": 6.5,
            "has_growth_history": True,
        },
    },
    {
        "id": "dorsey_economic_moats",
        "name": "Dorsey Economic Moats",
        "criteria": {
            "roic_min": 0.15,
            "composite_min": 7.0,
            "exclude_banks": True,
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

    # If preset / preset_id is passed, merge preset criteria
    preset_id = criteria.get("preset") or criteria.get("preset_id")
    if preset_id:
        p_row = next((p for p in SYSTEM_PRESETS if p["id"] == preset_id), None)
        if p_row:
            merged = dict(p_row["criteria"])
            merged.update(criteria)
            criteria = merged

    # Subquery to pick only the latest fiscal year of Penman analysis per company
    latest_penman_sub = (
        select(
            FinancialPenmanAnalysis.company_id,
            func.max(FinancialPenmanAnalysis.fiscal_year).label("max_fy"),
        )
        .group_by(FinancialPenmanAnalysis.company_id)
        .subquery()
    )

    latest_penman = (
        select(
            FinancialPenmanAnalysis.company_id,
            FinancialPenmanAnalysis.rnoa,
            FinancialPenmanAnalysis.flev,
        )
        .join(
            latest_penman_sub,
            (FinancialPenmanAnalysis.company_id == latest_penman_sub.c.company_id)
            & (FinancialPenmanAnalysis.fiscal_year == latest_penman_sub.c.max_fy),
        )
        .subquery()
    )

    # Base query: join Company with Score, TTM, Reverse DCF, and latest Penman
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
            latest_penman.c.rnoa,
            latest_penman.c.flev,
        )
        .outerjoin(Score, Score.company_id == Company.company_id)
        .outerjoin(FinancialSnapshotTTM, FinancialSnapshotTTM.company_id == Company.company_id)
        .outerjoin(ValuationReverseDCF, ValuationReverseDCF.company_id == Company.company_id)
        .outerjoin(latest_penman, latest_penman.c.company_id == Company.company_id)
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
        elif u_upper == "SPUS":
            stmt = stmt.where(Company.universe_tags.like('%"SPUS"%'))
        elif u_upper == "QQQ":
            stmt = stmt.where(Company.universe_tags.like('%"QQQ"%'))
        elif u_upper == "VONV":
            stmt = stmt.where(Company.universe_tags.like('%"VONV"%'))
        elif u_upper in ("RUSSELL1000", "RUSSELL_1000"):
            stmt = stmt.where(Company.universe_tags.like('%"RUSSELL1000"%'))
        else:
            stmt = stmt.where(Company.universe_tags.like(f'%"{u_upper}"%'))

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

    # Signal filter (supports 'scored' and 'insufficient_data')
    signal = criteria.get("signal")
    if signal:
        sig_lower = signal.lower()
        if sig_lower == "scored":
            stmt = stmt.where(Score.signal.isnot(None), Score.signal != "insufficient_data", Score.composite.isnot(None))
        elif sig_lower in ("insufficient_data", "gaps", "pending"):
            stmt = stmt.where(or_(Score.signal == "insufficient_data", Score.composite.is_(None)))
        else:
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
    seen_company_ids: set[str] = set()
    for r in results:
        if r.company_id in seen_company_ids:
            continue
        seen_company_ids.add(r.company_id)

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
        if criteria.get("halal_candidate"):
            from app.models import HalalFlag
            hf = db.get(HalalFlag, r.company_id)
            if hf is None or hf.status != "halal_candidate":
                continue
        if criteria.get("graham_net_net"):
            from app.services.graham_engine import compute_graham
            try:
                g = compute_graham(db, r.company_id)
                if not (g.get("deep_net_net") or (g.get("graham_margin_of_safety") and g["graham_margin_of_safety"] > 0.20)):
                    continue
            except Exception:
                continue
        if criteria.get("peg_max") is not None:
            from app.services.archetype_engine import classify_archetype
            try:
                arch = classify_archetype(db, r.company_id)
                peg = arch.get("metrics", {}).get("peg_ratio")
                if peg is None or peg > float(criteria["peg_max"]):
                    continue
            except Exception:
                continue
        if criteria.get("de_max") is not None:
            if r.flev is not None and r.flev > float(criteria["de_max"]):
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
