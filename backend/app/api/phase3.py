"""Phase 3 API: scores, rankings, halal flags (read-only + explicit recompute)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company, HalalFlag, Score
from app.services.scoring import DISCLAIMER, METHOD_VERSION

router = APIRouter(prefix="/api/v1", tags=["phase3"])


class RecomputeBody(BaseModel):
    universe: str = Field(default="seed", pattern="^(seed|company_id)$")
    company_id: str | None = Field(default=None, max_length=32)


@router.post("/scores/recompute")
def scores_recompute(body: RecomputeBody, db: Session = Depends(get_session)):
    """CPU-only deterministic recompute. Never hits the network."""
    from app.services.scoring_service import recompute

    if body.universe == "company_id":
        if not body.company_id:
            raise HTTPException(status_code=400, detail="company_id required when universe=company_id")
        if db.get(Company, body.company_id) is None:
            raise HTTPException(status_code=404, detail=f"unknown company_id: {body.company_id}")
        result = recompute(db, company_id=body.company_id)
    else:
        result = recompute(db)
    result["disclaimer"] = DISCLAIMER
    return result


def _score_payload(db: Session, row: Score, hf: HalalFlag | None) -> dict:
    return {
        "company_id": row.company_id,
        "as_of_fy": row.as_of_fy,
        "composite": row.composite,
        "quality": row.quality,
        "value": row.value,
        "growth": row.growth,
        "risk": row.risk,
        "coverage": row.coverage,
        "signal": row.signal,
        "peer_set_type": row.peer_set_type,
        "peer_n": row.peer_n,
        "peer_rank": row.peer_rank,
        "method_version": row.method_version,
        "computed_at": row.computed_at,
        "inputs_json": row.inputs_json,
        "halal": (
            {"status": hf.status, "method": hf.method, "tests": hf.tests_json} if hf else None
        ),
        "disclaimer": DISCLAIMER,
    }


@router.get("/companies/{company_id}/score")
def company_score(company_id: str, db: Session = Depends(get_session)):
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    row = db.get(Score, company_id)
    if row is None:
        raise HTTPException(status_code=404, detail="score not computed yet — POST /api/v1/scores/recompute first")
    hf = db.get(HalalFlag, company_id)
    return _score_payload(db, row, hf)


@router.get("/sectors/{sheet}/rankings")
def sector_rankings(
    sheet: str,
    currency: str = Query(default="USD", pattern="^(USD|CAD|ALL)$"),
    limit: int = Query(default=50, ge=1, le=500),
    halal: str | None = Query(default=None, pattern="^(candidate)$"),
    db: Session = Depends(get_session),
):
    """Ranked table for one sheet (composite desc, NULL last).

    currency=ALL (Phase 9) returns both currencies in one score-only table. Per-row
    money fields (PE/PB/ROE) come from each company's OWN snapshot — never averaged;
    the response carries no money medians at all, so nothing can blend."""
    stmt = (
        select(Score, Company, HalalFlag)
        .join(Company, Company.company_id == Score.company_id)
        .outerjoin(HalalFlag, HalalFlag.company_id == Score.company_id)
        .where(Score.composite.isnot(None))
        .where(
            (func.lower(Company.custom_industry_sheet) == sheet.lower())
            | (func.lower(Company.gics_sector) == sheet.removeprefix("GICS_").lower())
        )
    )
    if currency != "ALL":
        stmt = stmt.where(Company.currency == currency.upper())
    if halal == "candidate":
        stmt = stmt.where(HalalFlag.status == "halal_candidate")
    rows = db.execute(stmt.order_by(Score.composite.desc()).limit(limit)).all()

    from app.services.scoring_service import enrich_with_seed, load_universe

    universe = {u["company_id"]: u for u in load_universe(db)}
    items = []
    for i, (s, c, h) in enumerate(rows):
        entry = universe.get(c.company_id)
        enriched = enrich_with_seed(entry["snapshot"], entry.get("seed_snapshot")) if entry else {}
        items.append(
            {
                "rank": i + 1,
                "company_id": s.company_id,
                "name": c.name,
                "ticker": c.ticker,
                "currency": c.currency,
                "composite": s.composite,
                "signal": s.signal,
                "peer_set_type": s.peer_set_type,
                "peer_rank": s.peer_rank,
                "halal_status": (h.status if h else None),
                "pe_calc": enriched.get("pe_calc"),
                "pb_calc": enriched.get("pb_calc"),
                "roe_calc": enriched.get("roe_calc"),
                "method_version": s.method_version,
            }
        )
    return {
        "sheet": sheet,
        "currency": currency.upper(),
        "count": len(items),
        "items": items,
        "disclaimer": DISCLAIMER,
        "note": "currency=ALL is a score-only table; per-row money fields are native to each company and medians are never blended",
    }


@router.get("/rankings")
def global_rankings(
    scope: str = Query(default="seed", pattern="^(seed)$"),
    currency: str | None = Query(default=None, pattern="^(USD|CAD)$"),
    signal: str | None = Query(default=None, max_length=24),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    halal: str | None = Query(default=None, pattern="^(candidate)$"),
    db: Session = Depends(get_session),
):
    stmt = (
        select(Score, Company, HalalFlag)
        .join(Company, Company.company_id == Score.company_id)
        .outerjoin(HalalFlag, HalalFlag.company_id == Score.company_id)
        .where(Score.composite.isnot(None))
    )
    if currency:
        stmt = stmt.where(Company.currency == currency.upper())
    if signal:
        stmt = stmt.where(Score.signal == signal)
    if halal == "candidate":
        stmt = stmt.where(HalalFlag.status == "halal_candidate")
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.order_by(Score.composite.desc()).limit(limit).offset(offset)).all()
    return {
        "scope": scope,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "rank": offset + i + 1,
                "company_id": s.company_id,
                "name": c.name,
                "country": c.country,
                "currency": c.currency,
                "gics_sector": c.gics_sector,
                "custom_industry_sheet": c.custom_industry_sheet,
                "composite": s.composite,
                "quality": s.quality,
                "value": s.value,
                "growth": s.growth,
                "risk": s.risk,
                "coverage": s.coverage,
                "signal": s.signal,
                "halal_status": (h.status if h else None),
                "method_version": s.method_version,
            }
            for i, (s, c, h) in enumerate(rows)
        ],
        "disclaimer": DISCLAIMER,
    }


@router.get("/scores/summary")
def scores_summary(db: Session = Depends(get_session)):
    """Histogram + coverage diagnostics (also serves the EXIT CHECK)."""
    total = db.query(Score).count()
    nonnull = db.query(Score).filter(Score.composite.isnot(None)).count()
    signal_rows = db.execute(select(Score.signal, func.count()).group_by(Score.signal)).all()
    growth_null = db.query(Score).filter(Score.growth.is_(None), Score.composite.isnot(None)).count()
    return {
        "method_version": METHOD_VERSION,
        "scores_total": total,
        "composite_non_null": nonnull,
        "signal_histogram": {s or "insufficient_data": n for s, n in signal_rows},
        "growth_null_among_scored": growth_null,
        "disclaimer": DISCLAIMER,
    }
