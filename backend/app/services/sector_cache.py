"""Materialized Sector Summary Cache (Master Directive WS2).

Provides sub-25ms responses for /api/v1/sectors/{sheet}/snapshot by pre-computing
and materializing sector counts, medians (composite, PE, PB, ROE), signal histograms,
and top/bottom rankings into the `sector_cache_summaries` table.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import DISCLAIMER
from app.models import Company, FinancialSnapshot, Score, SectorCacheSummary
from app.services.scoring import METHOD_VERSION


def _median(vals: list[float]) -> float | None:
    cleaned = sorted(v for v in vals if v is not None and v == v)
    if not cleaned:
        return None
    n = len(cleaned)
    return cleaned[n // 2] if n % 2 else (cleaned[n // 2 - 1] + cleaned[n // 2]) / 2


def compute_sector_metrics(
    db: Session,
    sheet: str,
    currency: str,
) -> dict[str, Any]:
    """Compute full snapshot payload for one sheet + currency."""
    cur = currency.upper()
    stmt = (
        select(Company, Score)
        .outerjoin(Score, Score.company_id == Company.company_id)
        .where(
            (func.lower(Company.custom_industry_sheet) == sheet.lower())
            | (func.lower(Company.gics_sector) == sheet.removeprefix("GICS_").lower())
        )
        .where(Company.currency == cur)
    )
    rows = list(db.execute(stmt).all())

    seen: set[str] = set()
    uniq: list[tuple[Company, Score | None]] = []
    for c, s in rows:
        if c.company_id not in seen:
            seen.add(c.company_id)
            uniq.append((c, s))

    hist: dict[str, int] = {}
    composites: list[float] = []
    for _c, s in uniq:
        if s is not None and s.composite is not None:
            composites.append(s.composite)
            hist[s.signal or "unknown"] = hist.get(s.signal or "unknown", 0) + 1
        else:
            hist["score_missing"] = hist.get("score_missing", 0) + 1

    scored = [(c, s) for c, s in uniq if s is not None and s.composite is not None]
    scored.sort(key=lambda cs: cs[1].composite, reverse=True)

    def _entry(c: Company, s: Score) -> dict[str, Any]:
        return {
            "company_id": c.company_id,
            "name": c.name,
            "composite": s.composite,
            "signal": s.signal,
        }

    company_ids = [c.company_id for c, _ in uniq]
    pe_list: list[float] = []
    pb_list: list[float] = []
    roe_list: list[float] = []

    if company_ids:
        snaps = db.execute(
            select(FinancialSnapshot).where(
                FinancialSnapshot.company_id.in_(company_ids),
                FinancialSnapshot.period_type == "FY",
            )
        ).scalars().all()

        by_comp: dict[str, list[FinancialSnapshot]] = {}
        for snap in snaps:
            by_comp.setdefault(snap.company_id, []).append(snap)

        for cid in company_ids:
            c_snaps = by_comp.get(cid, [])
            dated = sorted((r for r in c_snaps if r.fiscal_year is not None), key=lambda r: r.fiscal_year, reverse=True)
            seed_row = next((r for r in c_snaps if r.fiscal_year is None), None)
            active = dated[0] if dated else seed_row
            if active:
                pe = active.pe_calc if active.pe_calc is not None else (seed_row.pe_calc if seed_row else None)
                pb = active.pb_calc if active.pb_calc is not None else (seed_row.pb_calc if seed_row else None)
                roe = active.roe_calc if active.roe_calc is not None else (seed_row.roe_calc if seed_row else None)
                if pe is not None:
                    pe_list.append(pe)
                if pb is not None:
                    pb_list.append(pb)
                if roe is not None:
                    roe_list.append(roe)

    return {
        "sheet": sheet,
        "currency": cur,
        "companies": len(uniq),
        "scored": len(scored),
        "signal_histogram": hist,
        "median_composite": _median(composites),
        "median_pe": _median(pe_list),
        "median_pb": _median(pb_list),
        "median_roe": _median(roe_list),
        "top": [_entry(c, s) for c, s in scored[:10]],
        "bottom": [_entry(c, s) for c, s in scored[-10:][::-1]],
        "method_version": METHOD_VERSION,
        "disclaimer": DISCLAIMER,
    }


def materialize_sector_cache(db: Session) -> int:
    """Materialize cache for all sheets/sectors and currencies.

    Returns the number of sector summary rows updated.
    """
    sheets_query = db.execute(
        select(Company.custom_industry_sheet).where(Company.custom_industry_sheet.is_not(None)).distinct()
    ).scalars().all()
    gics_query = db.execute(
        select(Company.gics_sector).where(Company.gics_sector.is_not(None)).distinct()
    ).scalars().all()

    all_sheets = set(sheets_query)
    for gics in gics_query:
        if gics:
            all_sheets.add(gics)
            all_sheets.add(f"GICS_{gics}")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    updated_count = 0

    for sheet in sorted(all_sheets):
        if not sheet:
            continue
        for cur in ("USD", "CAD"):
            metrics = compute_sector_metrics(db, sheet, cur)
            if metrics["companies"] == 0:
                continue

            existing = db.execute(
                select(SectorCacheSummary).where(
                    SectorCacheSummary.sector_name == sheet,
                    SectorCacheSummary.currency == cur,
                )
            ).scalar_one_or_none()

            if existing is None:
                existing = SectorCacheSummary(
                    sector_name=sheet,
                    currency=cur,
                )
                db.add(existing)

            existing.company_count = metrics["companies"]
            existing.scored_count = metrics["scored"]
            existing.median_composite = metrics["median_composite"]
            existing.median_pe = metrics["median_pe"]
            existing.median_pb = metrics["median_pb"]
            existing.median_roe = metrics["median_roe"]
            existing.signal_distribution_json = metrics["signal_histogram"]
            existing.top_json = metrics["top"]
            existing.bottom_json = metrics["bottom"]
            existing.updated_at = now
            updated_count += 1

    db.commit()
    return updated_count


def get_cached_sector_snapshot(
    db: Session,
    sheet: str,
    currency: str,
) -> dict[str, Any]:
    """Retrieve sector snapshot directly from cache (<25ms).

    Falls back to on-demand computation and caching if cache miss.
    """
    cur = currency.upper()
    cached = db.execute(
        select(SectorCacheSummary).where(
            func.lower(SectorCacheSummary.sector_name) == sheet.lower(),
            SectorCacheSummary.currency == cur,
        )
    ).scalar_one_or_none()

    if cached is not None:
        return {
            "sheet": sheet,
            "currency": cur,
            "companies": cached.company_count,
            "scored": cached.scored_count,
            "signal_histogram": cached.signal_distribution_json or {},
            "median_composite": cached.median_composite,
            "median_pe": cached.median_pe,
            "median_pb": cached.median_pb,
            "median_roe": cached.median_roe,
            "top": cached.top_json or [],
            "bottom": cached.bottom_json or [],
            "method_version": METHOD_VERSION,
            "disclaimer": DISCLAIMER,
        }

    # Cache miss: compute, store, and return
    metrics = compute_sector_metrics(db, sheet, cur)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    new_entry = SectorCacheSummary(
        sector_name=sheet,
        currency=cur,
        company_count=metrics["companies"],
        scored_count=metrics["scored"],
        median_composite=metrics["median_composite"],
        median_pe=metrics["median_pe"],
        median_pb=metrics["median_pb"],
        median_roe=metrics["median_roe"],
        signal_distribution_json=metrics["signal_histogram"],
        top_json=metrics["top"],
        bottom_json=metrics["bottom"],
        updated_at=now,
    )
    db.add(new_entry)
    db.commit()
    return metrics
