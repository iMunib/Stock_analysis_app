"""SEC Form 4 Insider Tracking API (Wave 7 Epic 16)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company
from app.services.ids import normalize_company_id
from app.services.insider_engine import get_insider_activity

router = APIRouter(prefix="/api/v1", tags=["insiders"])


@router.get("/companies/{company_id}/insiders")
def insiders(company_id: str, pure_mode: bool = Query(default=False, description="Filings-only pure mode"), db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    activity = get_insider_activity(db, company)
    # pure_mode flag is informational - we already return filings-only (no editorial noise)
    activity["pure_mode"] = pure_mode
    return activity


@router.get("/insiders/cluster")
def cluster(ids: str = Query(..., description="Comma-separated company IDs"), db: Session = Depends(get_db)):
    cids = [normalize_company_id(c.strip()) or c.strip() for c in ids.split(",") if c.strip()]
    if not 1 <= len(cids) <= 10:
        raise HTTPException(status_code=400, detail="Provide 1-10 company IDs")
    results = []
    for cid in cids:
        company = db.get(Company, cid)
        if not company:
            continue
        act = get_insider_activity(db, company)
        results.append({"company_id": cid, "ticker": company.ticker, "cluster": act["cluster"], "filings_count": len(act["filings"])})
    # Sort by cluster buy true first
    results.sort(key=lambda x: x["cluster"]["cluster_buy"], reverse=True)
    return {"count": len(results), "items": results}