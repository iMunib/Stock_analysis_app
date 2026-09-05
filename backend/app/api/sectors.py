"""Sector endpoints (Phase 1: read-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company, PeerBenchmark
from app.schemas import SectorCountOut, SectorsOut

router = APIRouter(prefix="/api/v1", tags=["sectors"])


@router.get("/sectors", response_model=SectorsOut)
def list_sectors(db: Session = Depends(get_session)):
    def _counts(column) -> list[SectorCountOut]:
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
        return sorted(merged.values(), key=lambda s: s.name)

    return SectorsOut(
        custom_industries=_counts(Company.custom_industry_sheet),
        gics_sectors=_counts(Company.gics_sector),
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
