"""Company endpoints (Phase 1: read-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company, DataQualityFlag, DerivedMetric, FinancialSnapshot, FinancialStatement, PeerBenchmark, Placement
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


@router.get("/{company_id}/statements")
def get_company_statements(
    company_id: str,
    limit: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_session),
):
    """Retrieve 3NF normalized financial statements (uncomputed accounting items)."""
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    rows = db.execute(
        select(FinancialStatement)
        .where(FinancialStatement.company_id == company_id)
        .order_by(FinancialStatement.fiscal_year.desc().nullslast(), FinancialStatement.id.desc())
        .limit(limit)
    ).scalars().all()
    return {
        "company_id": company_id,
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "fiscal_year": r.fiscal_year,
                "period_type": r.period_type,
                "as_of_date": r.as_of_date.isoformat() if r.as_of_date else None,
                "period_end": r.period_end.isoformat() if r.period_end else None,
                "currency": r.currency,
                "source": r.source,
                "revenue": r.revenue,
                "gross_profit": r.gross_profit,
                "ebit": r.ebit,
                "ebitda": r.ebitda,
                "net_income": r.net_income,
                "diluted_eps": r.diluted_eps,
                "operating_cash_flow": r.operating_cash_flow,
                "capex": r.capex,
                "free_cash_flow": r.free_cash_flow,
                "total_debt": r.total_debt,
                "cash_st_investments": r.cash_st_investments,
                "book_equity": r.book_equity,
                "total_assets": r.total_assets,
                "total_liabilities": r.total_liabilities,
                "cet1_ratio": r.cet1_ratio,
                "nim_fy2025": r.nim_fy2025,
            }
            for r in rows
        ],
    }


@router.get("/{company_id}/derived-metrics")
def get_company_derived_metrics(
    company_id: str,
    limit: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_session),
):
    """Retrieve 3NF normalized derived metrics and valuation ratios."""
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    rows = db.execute(
        select(DerivedMetric)
        .where(DerivedMetric.company_id == company_id)
        .order_by(DerivedMetric.fiscal_year.desc().nullslast(), DerivedMetric.id.desc())
        .limit(limit)
    ).scalars().all()
    return {
        "company_id": company_id,
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "fiscal_year": r.fiscal_year,
                "period_type": r.period_type,
                "as_of_date": r.as_of_date.isoformat() if r.as_of_date else None,
                "price": r.price,
                "market_cap": r.market_cap,
                "pe_calc": r.pe_calc,
                "pb_calc": r.pb_calc,
                "ev_calc": r.ev_calc,
                "ev_to_ebitda_calc": r.ev_to_ebitda_calc,
                "grossmargin_calc": r.grossmargin_calc,
                "fcfmargin_calc": r.fcfmargin_calc,
                "roe_calc": r.roe_calc,
                "roa_calc": r.roa_calc,
                "roic_calc": r.roic_calc,
                "fcf_calc": r.fcf_calc,
                "netdebt_calc": r.netdebt_calc,
                "altman_z": r.altman_z,
                "beneish_m_score": r.beneish_m_score,
                "sloan_accrual_ratio": r.sloan_accrual_ratio,
                "revenue_cagr_3y": r.revenue_cagr_3y,
                "revenue_cagr_5y": r.revenue_cagr_5y,
                "eps_cagr_3y": r.eps_cagr_3y,
                "eps_cagr_5y": r.eps_cagr_5y,
                "fcf_cagr_5y": r.fcf_cagr_5y,
            }
            for r in rows
        ],
    }


@router.get("/{company_id}/benchmarks")
def get_company_benchmarks(
    company_id: str,
    db: Session = Depends(get_session),
):
    """Retrieve 3NF normalized peer benchmarks for the company's sector and custom industry."""
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    cur = (company.currency or "USD").upper()
    groups = [g for g in (company.gics_sector, company.custom_industry_sheet) if g]
    rows = db.execute(
        select(PeerBenchmark)
        .where(
            PeerBenchmark.currency == cur,
            PeerBenchmark.peer_group_name.in_(groups),
        )
        .order_by(PeerBenchmark.peer_group_name, PeerBenchmark.metric_name)
    ).scalars().all()
    return {
        "company_id": company_id,
        "currency": cur,
        "groups": groups,
        "count": len(rows),
        "items": [
            {
                "peer_group_name": r.peer_group_name,
                "currency": r.currency,
                "metric_name": r.metric_name,
                "p10": r.p10,
                "p25": r.p25,
                "median": r.median,
                "p75": r.p75,
                "p90": r.p90,
                "count": r.count,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ],
    }


@router.get("/{company_id}/piotroski")
def get_company_piotroski(
    company_id: str,
    db: Session = Depends(get_session),
):
    """Retrieve 9-point Piotroski F-Score fundamental accounting analysis."""
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    try:
        from app.services.piotroski_engine import compute_piotroski_f_score
        return compute_piotroski_f_score(db, company_id)
    except Exception as exc:
        # Safe fallback - never 500 (frozen contract: honest null + flag)
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "f_score": None,
            "components": None,
            "message": f"Piotroski unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:300],
        }


@router.get("/{company_id}/dupont")
def get_company_dupont(
    company_id: str,
    db: Session = Depends(get_session),
):
    """Retrieve multi-year 3-stage and 5-stage DuPont ROE decomposition."""
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    try:
        from app.services.dupont_engine import compute_dupont_analysis
        return compute_dupont_analysis(db, company_id)
    except Exception as exc:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "dupont_3_stage": None,
            "dupont_5_stage": None,
            "message": f"DuPont unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:300],
        }


@router.get("/{company_id}/peer-matrix")
def get_company_peer_matrix(
    company_id: str,
    db: Session = Depends(get_session),
):
    """Retrieve 4-pillar percentile rankings against sector peer cohort in identical currency."""
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    try:
        from app.services.peer_engine import compute_peer_comparison_matrix
        return compute_peer_comparison_matrix(db, company_id)
    except Exception as exc:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "matrix": None,
            "message": f"Peer matrix unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:300],
        }
