"""Sector endpoints (Phase 1: read-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company
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
