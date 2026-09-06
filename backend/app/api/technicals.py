"""Technical Context API (Wave 7 Epic 17) - 12-1 momentum, SMA, drawdown, beta, valuation-price alignment."""
from __future__ import annotations

from statistics import median
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company, Score
from app.services.ids import normalize_company_id
from app.services.momentum_engine import get_technical_context

router = APIRouter(prefix="/api/v1", tags=["technicals"])


@router.get("/companies/{company_id}/technicals")
def technicals(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    ctx = get_technical_context(db, company)
    # Compute momentum percentile vs sector peers (pure, no composite alteration)
    # Gather sector peers' momentum
    sector = company.gics_sector or company.custom_industry_sheet
    peers = []
    if sector:
        peer_companies = db.execute(select(Company).where((Company.gics_sector == sector) | (Company.custom_industry_sheet == sector))).scalars().all()
        for pc in peer_companies[:30]:  # limit for performance
            try:
                pc_ctx = get_technical_context(db, pc)
                if pc_ctx.get("momentum_12_1") is not None:
                    peers.append(pc_ctx["momentum_12_1"])
            except Exception:
                continue
    percentile = None
    if ctx.get("momentum_12_1") is not None and peers:
        sorted_peers = sorted(peers)
        # Percentile rank: % of peers below current
        less = sum(1 for p in sorted_peers if p < ctx["momentum_12_1"])
        percentile = round(less / len(sorted_peers) * 100, 1) if sorted_peers else None
    ctx["momentum_percentile"] = percentile
    ctx["momentum_percentile_note"] = "Percentile vs sector peers (up to 30) - technical context only, not a scoring pillar."
    # Valuation-price alignment: current price vs DCF/Graham floors if available
    try:
        from app.services.valuation_engine import compute_guided_dcf
        guided = compute_guided_dcf(db, cid)
        if guided.get("status") == "computed" and guided.get("per_share") is not None:
            ctx["valuation_price_alignment"] = {
                "per_share": guided["per_share"],
                "price": guided["price"],
                "discount_pct": guided.get("premium_discount_pct"),
                "zone": "Undervalued" if guided.get("premium_discount_pct") is not None and guided["premium_discount_pct"] < 0 else "Overvalued" if guided.get("premium_discount_pct", 0) > 0 else "Fair",
            }
        else:
            ctx["valuation_price_alignment"] = None
    except Exception:
        ctx["valuation_price_alignment"] = None
    # Ensure disclaimer present
    if "disclaimer" not in ctx:
        ctx["disclaimer"] = "Personal research software, not investment advice. Price momentum is market sentiment context, not an intrinsic verdict. Insider transactions are filed historical facts."
    return ctx


@router.get("/technicals/momentum-rank")
def momentum_rank(ids: str = Query(..., description="Comma-separated company IDs (2-10)"), db: Session = Depends(get_db)):
    cids = [normalize_company_id(c.strip()) or c.strip() for c in ids.split(",") if c.strip()]
    if not 2 <= len(cids) <= 10:
        raise HTTPException(status_code=400, detail="Provide 2-10 company IDs")
    ranked = []
    for cid in cids:
        company = db.get(Company, cid)
        if not company:
            continue
        ctx = get_technical_context(db, company)
        ranked.append({"company_id": cid, "ticker": company.ticker, "momentum_12_1": ctx.get("momentum_12_1"), "currency": company.currency})
    ranked.sort(key=lambda x: (x["momentum_12_1"] is not None, x["momentum_12_1"] or -999), reverse=True)
    return {"count": len(ranked), "ranked": ranked}