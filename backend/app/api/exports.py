"""Export Suite API (Wave 6 Epic 13).

Routes for structured research memos, factsheet PDF data, batch CSV, and raw JSON dumps.
All exports are local, deterministic, currency-tagged, and carry disclaimers.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company
from app.services.ids import normalize_company_id
from app.services.export_service import generate_batch_csv, generate_journal_export, generate_raw_dump, generate_research_memo

router = APIRouter(prefix="/api/v1", tags=["exports"])


@router.get("/companies/{company_id}/export/memo")
def export_memo(company_id: str, format: str = Query(default="markdown", pattern="^(markdown|json)$"), db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    memo = generate_research_memo(db, cid)
    if format == "markdown":
        return PlainTextResponse(content=memo["markdown"], media_type="text/markdown", headers={"Content-Disposition": f'attachment; filename="{cid}-research-memo.md"'})
    return memo


@router.get("/companies/{company_id}/export/raw")
def export_raw(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    return generate_raw_dump(db, cid)


@router.get("/export/batch")
def export_batch(ids: str = Query(..., description="Comma-separated company IDs (2-8)"), format: str = Query(default="csv", pattern="^(csv|json)$"), db: Session = Depends(get_db)):
    cids = [normalize_company_id(c.strip()) or c.strip() for c in ids.split(",") if c.strip()]
    if not 1 <= len(cids) <= 20:
        raise HTTPException(status_code=400, detail="Provide 1-20 company IDs")
    if format == "csv":
        csv_text = generate_batch_csv(db, cids)
        return PlainTextResponse(content=csv_text, media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="batch-export.csv"'})
    # json
    dumps = [generate_raw_dump(db, cid) for cid in cids if db.get(Company, cid)]
    return {"count": len(dumps), "items": dumps, "disclaimer": "Personal research software, not investment advice."}


@router.get("/export/journal")
def export_journal(company_id: str | None = None, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id if company_id else None
    return generate_journal_export(db, cid)


@router.get("/portfolio/export/review")
def export_portfolio_review(db: Session = Depends(get_db)):
    # Annual decision journal audit + portfolio summary
    from app.services.portfolio_engine import portfolio_summary
    summary = portfolio_summary(db)
    journal = generate_journal_export(db)
    return {
        "generated_at": journal["generated_at"],
        "portfolio_summary": summary,
        "journal": journal,
        "disclaimer": "Personal research software, not investment advice. Portfolio tracking and alerts run locally.",
    }


@router.get("/companies/{company_id}/export/factsheet")
def export_factsheet(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    # Factsheet data is the same as raw dump but structured for print CSS
    raw = generate_raw_dump(db, cid)
    memo = generate_research_memo(db, cid)
    return {
        "company_id": cid,
        "factsheet": raw,
        "memo_markdown": memo["markdown"],
        "print_note": "CSS @media print guarantees no clipped tables, clean page breaks, and provenance headers.",
        "disclaimer": "Personal research software, not investment advice.",
    }
