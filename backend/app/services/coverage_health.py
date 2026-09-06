"""Universe Data Coverage & Health Audit Service (Wave 1: US-0466).

Produces a complete data integrity & health audit matrix across all 720 universe constituents:
- Total coverage across 720 universe names (S&P 500 US + TSX 220 CAD).
- Seed workbook completeness vs external provider backfill counts.
- Per-pillar completeness breakdown by sector (Quality, Value, Growth, Risk).
- Total count and percentage of NULL fields across all snapshots.
"""
from __future__ import annotations

from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot, Score


def compute_universe_health(db: Session) -> dict[str, Any]:
    """Audit the complete universe data coverage, seed completeness, and NULL statistics."""
    # 1. Total Universe Counts
    companies = list(db.execute(
        select(Company).where(Company.is_deleted == False)
    ).scalars().all())

    total_companies = len(companies)
    us_count = sum(1 for c in companies if c.currency == "USD")
    ca_count = sum(1 for c in companies if c.currency == "CAD")

    # 2. Score and Pillar Coverage
    scores = list(db.execute(select(Score)).scalars().all())
    score_by_id = {s.company_id: s for s in scores}

    quality_complete = sum(1 for s in scores if s.quality is not None)
    value_complete = sum(1 for s in scores if s.value is not None)
    growth_complete = sum(1 for s in scores if s.growth is not None)
    risk_complete = sum(1 for s in scores if s.risk is not None)
    composite_complete = sum(1 for s in scores if s.composite is not None)

    # 3. Seed vs Provider Backfill Audit
    snaps = list(db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.period_type == "FY")
    ).scalars().all())

    seed_snaps = [s for s in snaps if s.fiscal_year is None or (s.source and "Owner" in s.source)]
    provider_snaps = [s for s in snaps if s.fiscal_year is not None and (s.source and "Owner" not in s.source)]

    # 4. Sector-by-Sector Breakdown
    by_sector: dict[str, list[Company]] = {}
    for c in companies:
        sec = c.gics_sector or "Unclassified"
        by_sector.setdefault(sec, []).append(c)

    sector_breakdown: list[dict[str, Any]] = []
    for sec, comp_list in sorted(by_sector.items(), key=lambda x: x[0]):
        n_sec = len(comp_list)
        q_count = sum(1 for c in comp_list if score_by_id.get(c.company_id) and score_by_id[c.company_id].quality is not None)
        v_count = sum(1 for c in comp_list if score_by_id.get(c.company_id) and score_by_id[c.company_id].value is not None)
        g_count = sum(1 for c in comp_list if score_by_id.get(c.company_id) and score_by_id[c.company_id].growth is not None)
        r_count = sum(1 for c in comp_list if score_by_id.get(c.company_id) and score_by_id[c.company_id].risk is not None)
        cov_list = [score_by_id[c.company_id].coverage for c in comp_list if score_by_id.get(c.company_id) and score_by_id[c.company_id].coverage is not None]
        avg_cov = (sum(cov_list) / len(cov_list)) if cov_list else 0.0

        sector_breakdown.append({
            "sector": sec,
            "company_count": n_sec,
            "quality_pct": round(q_count / n_sec * 100, 1) if n_sec else 0,
            "value_pct": round(v_count / n_sec * 100, 1) if n_sec else 0,
            "growth_pct": round(g_count / n_sec * 100, 1) if n_sec else 0,
            "risk_pct": round(r_count / n_sec * 100, 1) if n_sec else 0,
            "average_pillars": round(avg_cov, 2),
        })

    # 5. NULL Fields Statistics across key columns
    monitored_cols = [
        "revenue", "net_income", "diluted_eps", "gross_profit",
        "operating_cash_flow", "capex", "fcf_calc", "total_debt",
        "cash_st_investments", "total_assets", "total_liabilities",
        "book_equity", "ebit", "ebitda", "interest_expense", "roe_calc", "pe_calc"
    ]
    total_inspected = len(snaps) * len(monitored_cols)
    null_counts: dict[str, int] = {col: 0 for col in monitored_cols}

    for s in snaps:
        for col in monitored_cols:
            if getattr(s, col, None) is None:
                null_counts[col] += 1

    total_nulls = sum(null_counts.values())
    null_pct = round(total_nulls / total_inspected * 100, 2) if total_inspected else 0.0

    top_missing = sorted(
        [{"field": col, "missing_count": cnt, "pct": round(cnt / len(snaps) * 100, 1)} for col, cnt in null_counts.items()],
        key=lambda x: x["missing_count"],
        reverse=True,
    )

    return {
        "universe_summary": {
            "total_companies": total_companies,
            "us_names": us_count,
            "canadian_names": ca_count,
            "seed_target": 720,
            "coverage_verified": total_companies >= 720,
        },
        "provenance_summary": {
            "total_snapshot_rows": len(snaps),
            "seed_workbook_rows": len(seed_snaps),
            "provider_backfill_rows": len(provider_snaps),
            "seed_completeness_pct": round(len(seed_snaps) / total_companies * 100, 1) if total_companies else 100.0,
        },
        "pillar_completeness": {
            "quality": {"count": quality_complete, "pct": round(quality_complete / total_companies * 100, 1) if total_companies else 0},
            "value": {"count": value_complete, "pct": round(value_complete / total_companies * 100, 1) if total_companies else 0},
            "growth": {"count": growth_complete, "pct": round(growth_complete / total_companies * 100, 1) if total_companies else 0},
            "risk": {"count": risk_complete, "pct": round(risk_complete / total_companies * 100, 1) if total_companies else 0},
            "composite": {"count": composite_complete, "pct": round(composite_complete / total_companies * 100, 1) if total_companies else 0},
        },
        "sector_breakdown": sector_breakdown,
        "null_data_audit": {
            "total_cells_audited": total_inspected,
            "total_null_cells": total_nulls,
            "null_percentage": null_pct,
            "honest_null_policy": "NULL fields are preserved as explicit honest gaps; never imputed or replaced with zero.",
            "top_missing_fields": top_missing[:6],
        },
    }
