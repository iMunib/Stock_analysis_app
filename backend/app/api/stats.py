"""Stats endpoint: import status and coverage."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company, DataQualityFlag, FinancialSnapshot, ImportRun, Placement
from app.schemas import ImportInfoOut, StatsOut

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_session)):
    companies = db.query(Company).count()
    snapshots = db.query(FinancialSnapshot).count()
    flags = db.query(DataQualityFlag).count()
    placements = db.query(Placement).count()
    runs = db.query(ImportRun).count()

    usd = db.query(Company).filter(Company.currency == "USD").count()
    cad = db.query(Company).filter(Company.currency == "CAD").count()

    def _nonnull(attr: str) -> int:
        return db.query(FinancialSnapshot).filter(getattr(FinancialSnapshot, attr).isnot(None)).count()

    coverage = {
        "Revenue": _nonnull("revenue"),
        "Net_Income": _nonnull("net_income"),
        "Total_Debt": _nonnull("total_debt"),
        "Gross_Profit": _nonnull("gross_profit"),
        "FCF_Calc": _nonnull("fcf_calc"),
        "ROE_Calc": _nonnull("roe_calc"),
        "Market_Cap": _nonnull("market_cap"),
        "CET1_Ratio": _nonnull("cet1_ratio"),
    }

    last_run = db.execute(select(ImportRun).order_by(ImportRun.id.desc()).limit(1)).scalars().first()
    last_import = (
        ImportInfoOut(
            last_import_at=last_run.imported_at,
            source_filename=last_run.source_filename,
            source_mtime=last_run.source_mtime,
            fixture=last_run.fixture,
        )
        if last_run
        else None
    )

    return StatsOut(
        companies=companies,
        financial_snapshots=snapshots,
        data_quality_flags=flags,
        placements=placements,
        import_runs=runs,
        by_currency={"USD": usd, "CAD": cad},
        coverage=coverage,
        last_import=last_import,
    )
