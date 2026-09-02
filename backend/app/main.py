"""FastAPI application. Phase 1: read-only research API over the imported seed."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.companies import router as companies_router
from app.api.phase2 import router as phase2_router
from app.api.phase3 import router as phase3_router
from app.api.phase4 import router as phase4_router
from app.api.sectors import router as sectors_router
from app.api.stats import router as stats_router
from app.config import APP_NAME, APP_VERSION, DISCLAIMER
from app.db import engine
from app.schemas import DisclaimerOut, StatsOut

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Personal equity-research API over a frozen local workbook snapshot. "
        f"{DISCLAIMER}"
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(companies_router)
app.include_router(sectors_router)
app.include_router(stats_router)
app.include_router(phase2_router)
app.include_router(phase3_router)
app.include_router(phase4_router)


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
