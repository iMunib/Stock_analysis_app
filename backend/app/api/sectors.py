"""Sector endpoints (Phase 1: read-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company, PeerBenchmark, SectorCacheSummary
from app.schemas import SectorCountOut, SectorsOut

router = APIRouter(prefix="/api/v1", tags=["sectors"])


@router.get("/sectors", response_model=SectorsOut)
def list_sectors(db: Session = Depends(get_session)):
    # Pre-load cached sector composite medians
    cache_rows = db.execute(select(SectorCacheSummary)).scalars().all()
    cache_map: dict[tuple[str, str], float | None] = {}
    for cr in cache_rows:
        if cr.sector_name and cr.currency:
            cache_map[(cr.sector_name.strip().lower(), cr.currency.strip().upper())] = cr.median_composite

    def _counts(column, is_gics: bool = False) -> list[SectorCountOut]:
        rows = db.execute(
            select(column, Company.currency, func.count())
            .group_by(column, Company.currency)
            .order_by(column)
        ).all()
        merged: dict[str, SectorCountOut] = {}
        for name, currency, count in rows:
            if name is None:
                continue
            entry = merged.setdefault(name, SectorCountOut(name=name, count=0))
            entry.count += count
            if currency == "USD":
                entry.usd += count
            elif currency == "CAD":
                entry.cad += count

        for entry in merged.values():
            name_lower = entry.name.strip().lower()
            keys_to_try = [name_lower]
            if is_gics:
                keys_to_try.extend([f"gics_{name_lower}", f"gics_{name_lower.replace(' ', '_')}"])
            else:
                keys_to_try.append(name_lower.replace(' ', '_'))

            m_usd = None
            m_cad = None
            for k in keys_to_try:
                if (k, "USD") in cache_map and cache_map[(k, "USD")] is not None:
                    m_usd = cache_map[(k, "USD")]
                    break
            for k in keys_to_try:
                if (k, "CAD") in cache_map and cache_map[(k, "CAD")] is not None:
                    m_cad = cache_map[(k, "CAD")]
                    break

            entry.median_composite_usd = m_usd
            entry.median_composite_cad = m_cad
            valid_meds = [m for m in (m_usd, m_cad) if m is not None]
            entry.median_composite_all = (sum(valid_meds) / len(valid_meds)) if valid_meds else None

        # Consolidate fragmented custom industries 86 → ~40 (WS7)
        if not is_gics:
            try:
                from app.services.industry_consolidation import consolidate_sheet
            except Exception:
                def consolidate_sheet(s):  # type: ignore
                    return s
            consolidated: dict[str, SectorCountOut] = {}
            for name, entry in merged.items():
                cons = consolidate_sheet(name) or name
                if cons not in consolidated:
                    consolidated[cons] = SectorCountOut(name=cons, count=0)
                target = consolidated[cons]
                target.count += entry.count
                target.usd += entry.usd
                target.cad += entry.cad
                # Merge medians conservatively: average of available medians
                # Keep already computed medians if target empty, else average
                if entry.median_composite_usd is not None:
                    if target.median_composite_usd is None:
                        target.median_composite_usd = entry.median_composite_usd
                    else:
                        target.median_composite_usd = (target.median_composite_usd + entry.median_composite_usd) / 2
                if entry.median_composite_cad is not None:
                    if target.median_composite_cad is None:
                        target.median_composite_cad = entry.median_composite_cad
                    else:
                        target.median_composite_cad = (target.median_composite_cad + entry.median_composite_cad) / 2
            for ent in consolidated.values():
                valid = [m for m in (ent.median_composite_usd, ent.median_composite_cad) if m is not None]
                ent.median_composite_all = (sum(valid) / len(valid)) if valid else None
            return sorted(consolidated.values(), key=lambda s: s.name)
        return sorted(merged.values(), key=lambda s: s.name)

    return SectorsOut(
        custom_industries=_counts(Company.custom_industry_sheet, is_gics=False),
        gics_sectors=_counts(Company.gics_sector, is_gics=True),
    )


@router.get("/benchmarks")
def list_benchmarks(
    peer_group: str | None = None,
    currency: str | None = None,
    metric: str | None = None,
    db: Session = Depends(get_session),
):
    """Query 3NF normalized peer benchmarks."""
    stmt = select(PeerBenchmark)
    if peer_group:
        stmt = stmt.where(PeerBenchmark.peer_group_name == peer_group.strip())
    if currency:
        stmt = stmt.where(PeerBenchmark.currency == currency.strip().upper())
    if metric:
        stmt = stmt.where(PeerBenchmark.metric_name == metric.strip())
    rows = db.execute(stmt.order_by(PeerBenchmark.peer_group_name, PeerBenchmark.metric_name)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "peer_group_name": r.peer_group_name,
                "currency": r.currency,
                "metric_name": r.metric_name,
                "p10": r.p10,
                "p25": r.p25,
                "median": r.median,
                "p75": r.p75,
                "p90": r.p90,
                "count": r.count,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ],
    }
