"""Backtesting & Factor Decay API - Epic 21 (Wave 8)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.backtest_engine import (
    check_overfitting,
    get_factor_decay,
    get_signal_follow_through,
    get_survivorship_doc,
)

router = APIRouter(prefix="/api/v1/backtesting", tags=["backtesting"])


@router.get("/factor-decay")
def factor_decay():
    return get_factor_decay()


@router.get("/survivorship")
def survivorship():
    return get_survivorship_doc()


@router.get("/signal-follow-through")
def signal_follow_through(db: Session = Depends(get_db)):
    return get_signal_follow_through(db)


@router.post("/overfitting-check")
def overfitting_check(criteria: dict[str, Any]):
    return check_overfitting(criteria)