"""Sector Rotation API - Epic 20 (Wave 8)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.sector_rotation_engine import (
    get_barrier_proxy,
    get_cycle_tag,
    get_sector_histogram,
    get_sector_rotation,
)

router = APIRouter(prefix="/api/v1/sectors", tags=["sector-rotation"])


@router.get("/rotation")
def rotation(currency: str = Query(default="ALL", pattern="^(ALL|USD|CAD|all|usd|cad)$"), db: Session = Depends(get_db)):
    return get_sector_rotation(db, currency.upper())


@router.get("/{sheet}/cycle-tag")
def cycle_tag(sheet: str):
    return get_cycle_tag(sheet)


@router.get("/{sheet}/barrier")
def barrier(sheet: str, currency: str = Query(default="USD", pattern="^(USD|CAD|ALL)$"), db: Session = Depends(get_db)):
    cur = currency.upper()
    if cur == "ALL":
        cur = "USD"
    return get_barrier_proxy(db, sheet, cur)


@router.get("/{sheet}/histogram")
def histogram(sheet: str, currency: str = Query(default="ALL"), metric: str = Query(default="composite"), db: Session = Depends(get_db)):
    cur = currency.upper() if currency else "ALL"
    return get_sector_histogram(db, sheet, cur, metric)