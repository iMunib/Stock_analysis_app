"""Phase 2 API: financials history, ticker resolve/ingest, backfill, coverage."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company, FinancialSnapshot
from app.providers.registry import ProviderRegistry
from app.schemas import SnapshotOut
from app.services import jobs as jobsvc
from app.services.ingest import get_or_create_company, ingest_price, ingest_statements
from app.services.mapping import MappingError, build_ref, resolve

router = APIRouter(prefix="/api/v1", tags=["phase2"])

# NOTE: POST /api/v1/jobs/backfill is owned by app.api.jobs (Phase 6A: async, 202+poll).
# This module deliberately does NOT define that path, so there is no route shadowing.

_registry = ProviderRegistry()


class IngestBody(BaseModel):
    ticker: str = Field(min_length=1, max_length=32)
    refresh: bool = False


class BackfillBody(BaseModel):
    mode: str = Field(default="sample", pattern="^(sample|all)$")
    limit: int = Field(default=5, ge=1, le=750)
    refresh: bool = False


@router.get("/companies/{company_id}/financials")
def company_financials(
    company_id: str,
    years: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_session),
):
    """Annual rows newest first. Includes the seed latest-FY row (fiscal_year NULL)."""
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    rows = db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == company_id, FinancialSnapshot.period_type == "FY")
        .order_by(
            FinancialSnapshot.fiscal_year.desc().nullslast(),
            FinancialSnapshot.id.desc(),
        )
        .limit(years)
    ).scalars().all()
    return {
        "company_id": company_id,
        "count": len(rows),
        "items": [SnapshotOut.model_validate(r).model_dump(mode="json") for r in rows],
    }


@router.get("/tickers/resolve")
def tickers_resolve(q: str = Query(min_length=1, max_length=64)):
    try:
        result = resolve(q)
    except MappingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "q": q,
        "company_id": result.company_id,
        "ticker": result.ticker,
        "country": result.country,
        "currency": result.currency,
        "yahoo_symbol": result.yahoo_symbol,
        "cik": result.cik,
        "in_universe": result.in_universe,
        "name": result.name,
    }


@router.post("/tickers/ingest", status_code=202, description="Enqueue an ingest job (async 202 + poll).")
def tickers_ingest(body: IngestBody, db: Session = Depends(get_session)):
    q = body.ticker.strip()
    company_id = None
    try:
        res = resolve(q)
        company_id = res.company_id
    except MappingError as exc:
        msg = str(exc)
        if "LISTING_AMBIGUOUS" in msg:
            raise HTTPException(status_code=400, detail="Multiple listings. Pick US ADR or HK/TSX (show choices).")
    except Exception:
        pass

    job = jobsvc.enqueue(
        db,
        "ingest",
        payload={"ticker": body.ticker, "refresh": body.refresh},
        company_id=company_id,
    )
    return {
        "job_id": job.id,
        "status": job.status,
        "kind": job.kind,
        "step": job.step,
        "message": job.message,
        "company_id": job.company_id,
        "error_code": job.error_code,
    }


from app.jobs.backfill import run_backfill  # noqa: F401  (CLI + worker share these runners)


@router.get("/coverage")
def coverage(db: Session = Depends(get_session)):
    total = db.query(Company).count()
    us = db.query(Company).filter(Company.country == "US").count()
    ca = db.query(Company).filter(Company.country == "CA").count()

    per_company = db.execute(
        select(FinancialSnapshot.company_id, func.count(FinancialSnapshot.fiscal_year))
        .where(FinancialSnapshot.fiscal_year.isnot(None))
        .group_by(FinancialSnapshot.company_id)
    ).all()
    companies_with_history = len(per_company)
    years_min = db.execute(select(func.min(FinancialSnapshot.fiscal_year))).scalar_one_or_none()
    years_max = db.execute(select(func.max(FinancialSnapshot.fiscal_year))).scalar_one_or_none()
    ge5 = sum(1 for _, n in per_company if n >= 5)

    last_import = db.execute(
        select(Company.imported_at).order_by(Company.imported_at.desc()).limit(1)
    ).scalar_one_or_none()

    fixture_flag = bool(
        db.query(Company).filter(Company.extraction_status == "FIXTURE").count()
    )
    return {
        "companies": total,
        "us": us,
        "ca": ca,
        "companies_with_history": companies_with_history,
        "pct_with_5plus_fy": round(100.0 * ge5 / total, 1) if total else 0.0,
        "years_min": years_min,
        "years_max": years_max,
        "fixture_flag": fixture_flag,
        "note": "History counts exclude the seed latest-FY row (fiscal_year NULL).",
    }
