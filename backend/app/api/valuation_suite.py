"""Valuation Suite API (Wave 4 Epic 10).

Endpoints deliver assumption-explicit, range-based valuations in native currency.
All models are hypothetical outputs, never blended into the locked composite.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company
from app.services.ids import normalize_company_id

router = APIRouter(prefix="/api/v1", tags=["valuation_suite"])


@router.get("/companies/{company_id}/valuation/guided")
def guided_valuation(
    company_id: str,
    revenue_growth: float | None = Query(default=None, ge=-0.5, le=0.5),
    operating_margin: float | None = Query(default=None, ge=-0.5, le=0.8),
    wacc: float | None = Query(default=None, ge=0.02, le=0.25),
    terminal_g: float | None = Query(default=None, ge=0.0, le=0.05),
    years: int = Query(default=5, ge=3, le=10),
    risk_free: float = Query(default=0.04, ge=0.0, le=0.1),
    erp: float = Query(default=0.05, ge=0.0, le=0.1),
    beta: float | None = Query(default=None, ge=0.2, le=3.0),
    db: Session = Depends(get_db),
):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    from app.services.valuation_engine import compute_guided_dcf

    try:
        return compute_guided_dcf(
            db, cid,
            revenue_growth=revenue_growth,
            operating_margin=operating_margin,
            wacc=wacc,
            terminal_g=terminal_g,
            years=years,
            risk_free=risk_free,
            erp=erp,
            beta=beta,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as exc:
        return {
            "company_id": cid,
            "status": "insufficient_data",
            "message": f"Guided DCF unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:400],
        }


@router.get("/companies/{company_id}/valuation/epv")
def epv_valuation(company_id: str, wacc: float | None = Query(default=None, ge=0.02, le=0.25), db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    try:
        from app.services.epv_engine import compute_epv
        from app.services.valuation_engine import DEFAULT_WACC
        return compute_epv(db, cid, wacc=wacc if wacc is not None else DEFAULT_WACC)
    except Exception as exc:
        return {"company_id": cid, "status": "insufficient_data", "message": f"EPV unavailable: {exc.__class__.__name__}", "detail": str(exc)[:400]}


@router.get("/companies/{company_id}/valuation/ddm")
def ddm_valuation(company_id: str, wacc: float | None = Query(default=None, ge=0.02, le=0.25), db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    try:
        from app.services.dividend_discount_engine import compute_ddm
        from app.services.valuation_engine import DEFAULT_WACC
        return compute_ddm(db, cid, wacc=wacc if wacc is not None else DEFAULT_WACC)
    except Exception as exc:
        return {"company_id": cid, "status": "insufficient_data", "message": f"DDM unavailable: {exc.__class__.__name__}", "detail": str(exc)[:400]}


@router.get("/companies/{company_id}/valuation/residual-income")
def residual_income_valuation(company_id: str, wacc: float | None = Query(default=None, ge=0.02, le=0.25), db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    try:
        from app.services.dividend_discount_engine import compute_residual_income
        from app.services.valuation_engine import DEFAULT_WACC
        return compute_residual_income(db, cid, wacc=wacc if wacc is not None else DEFAULT_WACC)
    except Exception as exc:
        return {"company_id": cid, "status": "insufficient_data", "message": f"Residual Income unavailable: {exc.__class__.__name__}", "detail": str(exc)[:400]}


@router.get("/companies/{company_id}/valuation/decomposition")
def decomposition(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    try:
        from app.services.valuation_engine import decompose_implied_growth
        return decompose_implied_growth(db, cid)
    except Exception as exc:
        return {"company_id": cid, "status": "insufficient_data", "message": f"Decomposition unavailable: {exc.__class__.__name__}", "detail": str(exc)[:400]}


@router.get("/companies/{company_id}/valuation/normalized")
def normalized_earnings(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    try:
        from app.services.valuation_engine import compute_normalized_earnings
        return compute_normalized_earnings(db, cid)
    except Exception as exc:
        return {"company_id": cid, "status": "insufficient_data", "message": f"Normalized earnings unavailable: {exc.__class__.__name__}", "detail": str(exc)[:400]}


@router.get("/valuation/rank")
def valuation_rank(ids: str = Query(..., description="Comma-separated company IDs"), db: Session = Depends(get_db)):
    cids = [c.strip() for c in ids.split(",") if c.strip()]
    if not 2 <= len(cids) <= 8:
        raise HTTPException(status_code=400, detail="Provide 2–8 company IDs")
    from app.services.valuation_engine import compute_guided_dcf

    ranked = []
    for cid in cids:
        norm = normalize_company_id(cid) or cid
        company = db.get(Company, norm)
        if not company:
            continue
        dcf = compute_guided_dcf(db, norm)
        if dcf.get("status") != "computed" or dcf.get("per_share") is None or dcf.get("price") is None:
            # Use available data but mark insufficient
            discount = None
        else:
            per = dcf["per_share"]
            price = dcf["price"]
            discount = round((per - price) / per * 100.0, 1) if per else None
        ranked.append({
            "company_id": norm,
            "ticker": company.ticker,
            "name": company.name,
            "currency": company.currency,
            "per_share": dcf.get("per_share"),
            "price": dcf.get("price"),
            "discount_pct": discount,
            "terminal_heavy": dcf.get("terminal_heavy"),
            "status": dcf.get("status"),
        })
    # Sort by discount descending (most undervalued first)
    ranked.sort(key=lambda x: (x["discount_pct"] if x["discount_pct"] is not None else -999), reverse=True)
    return {"count": len(ranked), "ranked": ranked}


@router.get("/valuation/compare")
def valuation_compare(ids: str = Query(..., description="Comma-separated 2 company IDs"), db: Session = Depends(get_db)):
    cids = [c.strip() for c in ids.split(",") if c.strip()]
    if len(cids) != 2:
        raise HTTPException(status_code=400, detail="Provide exactly 2 company IDs for side-by-side")
    from app.services.valuation_engine import compute_guided_dcf
    from app.services.epv_engine import compute_epv
    from app.services.dividend_discount_engine import compute_ddm

    out = []
    for cid in cids:
        norm = normalize_company_id(cid) or cid
        company = db.get(Company, norm)
        if not company:
            raise HTTPException(status_code=404, detail=f"Company {cid} not found")
        out.append({
            "company_id": norm,
            "ticker": company.ticker,
            "name": company.name,
            "currency": company.currency,
            "guided": compute_guided_dcf(db, norm),
            "epv": compute_epv(db, norm),
            "ddm": compute_ddm(db, norm),
        })
    return {"count": 2, "items": out}
