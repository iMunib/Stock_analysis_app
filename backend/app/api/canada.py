"""Canada Market & Tax-Account API (Wave 7 Epic 15)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company, FinancialSnapshot
from app.services.canadian_tax_engine import get_account_placement_guide, get_canadian_industry_medians, get_canadian_metrics, get_dual_listed_identity
from app.services.ids import normalize_company_id

router = APIRouter(prefix="/api/v1/canada", tags=["canada"])


@router.get("/companies/{company_id}/tax-placement")
def tax_placement(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    guide = get_account_placement_guide(company)
    guide["disclaimer"] = "Personal research software, not investment advice. Price momentum is market sentiment context, not an intrinsic verdict. Insider transactions are filed historical facts."
    return guide


@router.get("/companies/{company_id}/canadian-metrics")
def canadian_metrics(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    snap = db.query(FinancialSnapshot).filter(FinancialSnapshot.company_id == cid).order_by(FinancialSnapshot.fiscal_year.desc().nullslast()).first()
    metrics = get_canadian_metrics(company, snap)
    metrics["disclaimer"] = "Personal research software, not investment advice."
    return metrics


@router.get("/companies/{company_id}/dual-listed")
def dual_listed(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    return get_dual_listed_identity(company)


@router.get("/industry/{industry}/medians")
def industry_medians(industry: str, currency: str = "CAD", db: Session = Depends(get_db)):
    # Enforce CAD purity for Canadian industry medians
    if currency.upper() != "CAD":
        raise HTTPException(status_code=400, detail="Canadian industry medians are pure CAD only (currency=CAD)")
    return get_canadian_industry_medians(db, industry, currency="CAD")
