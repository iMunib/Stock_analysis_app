"""REST API routes for Forensic Accounting, Reverse DCF Valuation, and Screener Presets."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company, FinancialSnapshot, FinancialSnapshotTTM, Score, ScreenerPreset, ValuationReverseDCF
from app.services.ids import normalize_company_id
from app.services.screener_engine import ensure_system_presets, run_screener_query
from app.services.ttm_engine import compute_and_store_ttm
from app.services.valuation_engine import compute_and_store_reverse_dcf

router = APIRouter(prefix="/api/v1", tags=["forensics"])


# --- Schemas ---

class ScreenerRunIn(BaseModel):
    currency: str | None = None
    sector: str | None = None
    industry: str | None = None
    signal: str | None = None
    composite_min: float | None = None
    exclude_banks: bool = False
    roic_min: float | None = None
    ev_ebitda_max: float | None = None
    fcf_yield_min: float | None = None
    sloan_accrual_min: float | None = None
    sloan_accrual_max: float | None = None
    cash_conversion_min: float | None = None
    cash_conversion_max: float | None = None
    expectations_gap_min: float | None = None
    expectations_gap_max: float | None = None
    flag_logic: str = "AND"
    sort_by: str = "composite"
    sort_dir: str = "desc"
    limit: int = 100
    offset: int = 0


class FcfVsNiYear(BaseModel):
    fiscal_year: int
    net_income: float | None
    fcf: float | None


class ForensicsOut(BaseModel):
    company_id: str
    currency: str
    sloan_accrual_ratio: float | None
    sloan_signal: str  # "green", "red", "neutral", "insufficient_data"
    cash_conversion_ratio: float | None
    cash_conversion_signal: str  # "weak", "healthy", "insufficient_data"
    roic: float | None
    fcf_yield: float | None
    nopat: float | None
    invested_capital: float | None
    fcf_vs_ni_history: list[FcfVsNiYear]


class ValuationOut(BaseModel):
    company_id: str
    status: str
    current_share_price: float | None
    diluted_shares: float | None
    net_debt: float | None
    baseline_fcf: float | None
    wacc: float
    terminal_growth_rate: float
    market_implied_growth_10y: float | None
    historical_5y_cagr: float | None
    expectations_gap: float | None
    sensitivity_matrix: dict[str, Any] | None


class DeleteCompanyOut(BaseModel):
    ok: bool
    company_id: str
    message: str


# --- Endpoints ---

@router.get("/companies/{company_id}/forensics", response_model=ForensicsOut)
def get_company_forensics(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    # Ensure TTM snapshot exists
    ttm = db.get(FinancialSnapshotTTM, cid)
    if not ttm:
        ttm = compute_and_store_ttm(db, cid)
        db.commit()

    # 5-year FCF vs Net Income history from annual snapshots
    annuals = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == cid,
            FinancialSnapshot.fiscal_year.is_not(None),
            FinancialSnapshot.period_type == "FY",
        ).order_by(FinancialSnapshot.fiscal_year.asc())
    ).scalars().all()

    fcf_vs_ni = [
        FcfVsNiYear(
            fiscal_year=a.fiscal_year,
            net_income=a.net_income,
            fcf=a.fcf_calc,
        )
        for a in annuals
        if a.fiscal_year is not None
    ]

    sloan = ttm.sloan_accrual_ratio
    sloan_signal = "insufficient_data"
    if sloan is not None:
        if sloan > 0.10:
            sloan_signal = "red"  # Aggressive accounting
        elif sloan < -0.10:
            sloan_signal = "green"  # Conservative accounting
        else:
            sloan_signal = "neutral"

    ccer = ttm.cash_conversion_ratio
    ccer_signal = "insufficient_data"
    if ccer is not None:
        ccer_signal = "weak" if ccer < 0.70 else "healthy"

    return ForensicsOut(
        company_id=cid,
        currency=ttm.currency,
        sloan_accrual_ratio=sloan,
        sloan_signal=sloan_signal,
        cash_conversion_ratio=ccer,
        cash_conversion_signal=ccer_signal,
        roic=ttm.roic,
        fcf_yield=ttm.fcf_yield,
        nopat=ttm.nopat,
        invested_capital=ttm.invested_capital,
        fcf_vs_ni_history=fcf_vs_ni,
    )


@router.get("/companies/{company_id}/valuation", response_model=ValuationOut)
def get_company_valuation(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    # Ensure Reverse DCF exists
    dcf = db.get(ValuationReverseDCF, cid)
    if not dcf:
        dcf = compute_and_store_reverse_dcf(db, cid)
        db.commit()

    return ValuationOut(
        company_id=cid,
        status=dcf.status,
        current_share_price=dcf.current_share_price,
        diluted_shares=dcf.diluted_shares,
        net_debt=dcf.net_debt,
        baseline_fcf=dcf.baseline_fcf,
        wacc=dcf.wacc,
        terminal_growth_rate=dcf.terminal_growth_rate,
        market_implied_growth_10y=dcf.market_implied_growth_10y,
        historical_5y_cagr=dcf.historical_5y_cagr,
        expectations_gap=dcf.expectations_gap,
        sensitivity_matrix=dcf.sensitivity_matrix_json,
    )


@router.delete("/companies/{company_id}", response_model=DeleteCompanyOut)
def delete_company(company_id: str, hard: bool = Query(False), db: Session = Depends(get_db)):
    """Removes a company from the active research desk. Defaults to soft deletion."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    if hard:
        db.delete(company)
        db.commit()
        return DeleteCompanyOut(ok=True, company_id=cid, message=f"Permanently deleted {cid} from database.")

    company.is_deleted = True
    db.commit()
    return DeleteCompanyOut(ok=True, company_id=cid, message=f"Removed {cid} from active research desk.")


@router.post("/companies/{company_id}/restore", response_model=DeleteCompanyOut)
def restore_company(company_id: str, db: Session = Depends(get_db)):
    """Restores a previously removed company back to the active research desk."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    company.is_deleted = False
    db.commit()
    return DeleteCompanyOut(ok=True, company_id=cid, message=f"Restored {cid} to active research desk.")


@router.get("/screener/presets")
def get_screener_presets(db: Session = Depends(get_db)):
    """Lists institutional deep-value and forensic screener presets."""
    presets = ensure_system_presets(db)
    return [
        {
            "id": p.id,
            "name": p.name,
            "criteria": p.criteria_json,
            "is_system": p.is_system_preset,
        }
        for p in presets
    ]


@router.post("/screener/run")
def run_screener(body: ScreenerRunIn, db: Session = Depends(get_db)):
    """Runs a multi-metric deep-value forensic screener query."""
    criteria = body.model_dump(exclude_none=True)
    return run_screener_query(db, criteria, limit=body.limit, offset=body.offset)
