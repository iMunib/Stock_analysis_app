"""Company endpoints (Phase 1: read-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company, DataQualityFlag, FinancialSnapshot, Placement
from app.schemas import CompanyDetailOut, CompanyListOut, CompanyOut, FlagOut, PlacementOut, SnapshotOut

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def _latest_snapshot(db: Session, company_id: str) -> FinancialSnapshot | None:
    """Latest snapshot = the FY row; order by fiscal_year desc (all NULL in Phase 1),
    then by as_of_date desc, then by id desc so re-imports win deterministically."""
    stmt = (
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == company_id)
        .order_by(
            FinancialSnapshot.fiscal_year.desc().nullslast(),
            FinancialSnapshot.as_of_date.desc().nullslast(),
            FinancialSnapshot.id.desc(),
        )
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


@router.get("", response_model=CompanyListOut)
def list_companies(
    q: str | None = Query(default=None, description="substring on name or ticker"),
    sector: str | None = Query(default=None, description="GICS sector"),
    industry: str | None = Query(default=None, description="custom industry sheet"),
    country: str | None = Query(default=None, description="US or CA"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    stmt = select(Company).where(Company.is_deleted == False)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Company.name.ilike(like)) | (Company.ticker.ilike(like)))
    if sector:
        stmt = stmt.where(Company.gics_sector == sector.strip())
    if industry:
        stmt = stmt.where(Company.custom_industry_sheet == industry.strip())
    if country:
        stmt = stmt.where(Company.country == country.strip().upper())

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.order_by(Company.company_id).limit(limit).offset(offset)).scalars().all()
    return CompanyListOut(
        total=total,
        limit=limit,
        offset=offset,
        items=[CompanyOut.model_validate(c) for c in rows],
    )


@router.get("/{company_id}", response_model=CompanyDetailOut)
def get_company(company_id: str, db: Session = Depends(get_session)):
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    snap = _latest_snapshot(db, company.company_id)
    flags = db.execute(
        select(DataQualityFlag).where(DataQualityFlag.company_id == company.company_id)
    ).scalars().all()
    placements = db.execute(
        select(Placement).where(Placement.company_id == company.company_id)
    ).scalars().all()
    detail = CompanyDetailOut.model_validate(company)
    detail.flags = [FlagOut.model_validate(f) for f in flags]
    detail.placements = [PlacementOut.model_validate(p) for p in placements]
    detail.latest_snapshot = SnapshotOut.model_validate(snap) if snap else None
    return detail
