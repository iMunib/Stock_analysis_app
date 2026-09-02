"""Stats endpoint: import status and coverage."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from pathlib import Path

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


@router.get("/system/health/telemetry")
def system_telemetry(db: Session = Depends(get_session)):
    """Trust sprint E2: local observability for migration state, freshness and job health."""
    from datetime import datetime as _dt

    from alembic.config import Config as _AlembicConfig
    from alembic.script import ScriptDirectory as _ScriptDirectory
    from sqlalchemy import text as _text

    from app.config import DATABASE_URL as _DB_URL

    # Migration revision vs head
    cfg = _AlembicConfig(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "alembic"))
    head = _ScriptDirectory.from_config(cfg).get_current_head()
    try:
        stamped = db.execute(_text("SELECT version_num FROM alembic_version")).scalars().first()
        schema_verified = stamped == head
        migration_revision = stamped
    except Exception:
        stamped = None
        schema_verified = False
        migration_revision = None

    # Price staleness: share of companies whose seed/annual price as_of is older than 7 days
    from app.models import Company as _Company, FinancialSnapshot as _FS, FinancialSnapshotTTM as _TTM, Job as _Job

    now = _dt.utcnow()
    stale_price = 0
    total_priced = 0
    seed_rows = db.execute(
        select(_FS).where(_FS.fiscal_year.is_(None), _FS.price.isnot(None))
    ).scalars().all()
    for s in seed_rows:
        if s.as_of_date is None:
            continue
        total_priced += 1
        if (_dt.utcnow().date() - s.as_of_date).days > 7:
            stale_price += 1

    low_conf_roic = (
        db.query(_TTM)
        .filter(_TTM.roic_confidence == "low")
        .count()
    )
    job_counts: dict[str, int] = {}
    for status, n in db.execute(_text("SELECT status, COUNT(*) FROM jobs GROUP BY status")).fetchall():
        job_counts[str(status)] = int(n)

    telemetry = {
        "migration_revision": migration_revision,
        "alembic_head": head,
        "schema_verified": schema_verified,
        "stale_price_count": stale_price,
        "priced_companies": total_priced,
        "low_confidence_roic_count": low_conf_roic,
        "job_counts_by_status": job_counts,
        "provider_error_rates": _provider_error_rates(db),
        "database_url_kind": "sqlite" if _DB_URL.startswith("sqlite") else "other",
    }
    void(_Company)
    return telemetry


def _provider_error_rates(db) -> dict:
    """Error rate per provider from the job provider_stats blobs (best-effort)."""
    from collections import defaultdict

    from app.models import Job

    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"ok": 0, "error": 0})
    jobs = db.query(Job).order_by(Job.id.desc()).limit(50).all()
    for j in jobs:
        stats = j.provider_stats_json or {}
        if not isinstance(stats, dict):
            continue
        for provider, entry in stats.items():
            if not isinstance(entry, dict):
                continue
            bucket = totals.setdefault(str(provider), {"ok": 0, "error": 0})
            bucket["ok"] += int(entry.get("ok") or entry.get("fetched") or 0)
            bucket["error"] += int(entry.get("error") or entry.get("errors") or 0)
    return {
        p: (round(v["error"] / (v["ok"] + v["error"]), 4) if (v["ok"] + v["error"]) else None)
        for p, v in totals.items()
    }


def void(_x) -> None:
    return None