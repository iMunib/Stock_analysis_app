"""FastAPI application. Research API over local SQLite (WAL) + async jobs."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Millisecond-precision logging - required for all API requests, background
# workers, and ingestion jobs. Formatter:  %(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s:%(lineno)d] %(message)s
# Datefmt: %Y-%m-%d %H:%M:%S  (asctime already provides H:M:S, msecs adds .SSS)
LOGGING_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
LOGGING_DATEFMT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_FORMAT,
    datefmt=LOGGING_DATEFMT,
    force=True,
)
# Ensure uvicorn loggers also use the same formatter (they may have been configured earlier)
for _lname in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
    _lg = logging.getLogger(_lname)
    if _lg.handlers:
        for _h in _lg.handlers:
            _h.setFormatter(logging.Formatter(LOGGING_FORMAT, datefmt=LOGGING_DATEFMT))
    else:
        _h = logging.StreamHandler()
        _h.setFormatter(logging.Formatter(LOGGING_FORMAT, datefmt=LOGGING_DATEFMT))
        _lg.addHandler(_h)
    _lg.propagate = False

logger = logging.getLogger("app.main")

from app.api.companies import router as companies_router
from app.api.chat import router as chat_router
from app.api.dossier import router as dossier_router
from app.api.financials import router as financials_router
from app.api.forensics import router as forensics_router
from app.api.jobs import router as jobs_router
from app.api.llm_admin import router as llm_admin_router
from app.api.metrics import router as metrics_router
from app.api.screen import router as screen_router
from app.api.sectors import router as sectors_router
from app.api.stats import router as stats_router
from app.api.wave1 import router as wave1_router
from app.api.wave2 import router as wave2_router
from app.api.restatements import router as restatements_router
from app.api.valuation_suite import router as valuation_suite_router
from app.api.portfolio import router as portfolio_router
from app.api.alerts import router as alerts_router
from app.api.exports import router as exports_router
from app.api.canada import router as canada_router
from app.api.insiders import router as insiders_router
from app.api.technicals import router as technicals_router
from app.api.curriculum import router as curriculum_router
from app.api.sector_rotation import router as sector_rotation_router
from app.api.backtesting import router as backtesting_router
from app.api.ops import router as ops_router
from app.api.governance import router as governance_router
from app.config import APP_NAME, APP_VERSION, DISCLAIMER
from app.db import engine
from app.schemas import DisclaimerOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Trust sprint A2: refuse to serve from a DB whose migration stamp is missing,
    # diverged, or behind head. Alembic is the only schema authority; we never
    # create_all or auto-stamp here. Recovery is always manual (see README).
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import text as _text

    from app.db import engine

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    head = ScriptDirectory.from_config(cfg).get_current_head()
    with engine.connect() as conn:
        try:
            rows = conn.execute(_text("SELECT version_num FROM alembic_version")).scalars().all()
        except Exception:
            rows = []
    live = rows[0] if len(rows) == 1 else None
    if len(rows) != 1 or live != head:
        raise RuntimeError(
            "Database migration stamp does not match alembic head."
            f" expected={head!r} found={rows!r}."
            " Recover manually with: cd backend && set DATABASE_URL=sqlite:///../data/app.db"
            " && python -m alembic stamp head  (ONLY if the schema was already created by a"
            " previous create_all boot) or python -m alembic upgrade head."
            " Never let the app stamp or migrate automatically."
        )

    # Phase 6A: one daemon worker thread for async jobs (backfill/ingest/recompute).
    # Tests set JOBS_WORKER_DISABLED=1 to drive JobWorker.process_one() manually.
    import os

    from app.services.job_worker import JobWorker

    if os.environ.get("JOBS_WORKER_DISABLED") != "1":
        worker = JobWorker()
        worker.start()
        app.state.job_worker = worker

        import threading

        def _bg_startup_populate():
            try:
                import time
                time.sleep(1.0)
                from app.db import SessionLocal
                from app.services.calculation_pipeline import populate_missing_metrics
                with SessionLocal() as session:
                    populate_missing_metrics(session, limit=None)
            except Exception:
                pass

        threading.Thread(target=_bg_startup_populate, name="startup-pipeline", daemon=True).start()
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Personal equity-research API over a frozen local workbook snapshot. "
        f"{DISCLAIMER}"
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(companies_router)
app.include_router(chat_router)
app.include_router(screen_router)
app.include_router(forensics_router)
app.include_router(sectors_router)
app.include_router(stats_router)
app.include_router(financials_router)
app.include_router(metrics_router)
app.include_router(dossier_router)
app.include_router(jobs_router)
app.include_router(llm_admin_router)
app.include_router(wave1_router)
app.include_router(wave2_router)
app.include_router(restatements_router)
app.include_router(valuation_suite_router)
app.include_router(portfolio_router)
app.include_router(alerts_router)
app.include_router(exports_router)
app.include_router(canada_router)
app.include_router(insiders_router)
app.include_router(technicals_router)
app.include_router(curriculum_router)
app.include_router(sector_rotation_router)
app.include_router(backtesting_router)
app.include_router(ops_router)
app.include_router(governance_router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:  # pragma: no cover
        return {"status": "degraded", "database": f"error: {exc.__class__.__name__}"}


@app.get("/api/v1/meta/disclaimer", response_model=DisclaimerOut, tags=["meta"])
def disclaimer():
    return DisclaimerOut(disclaimer=DISCLAIMER)