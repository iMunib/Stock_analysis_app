"""Startup pipeline entrypoint for docker-compose and background initialization.

Usage:
    python -m app.jobs.startup_pipeline [--sync-only] [--limit N]

On every docker compose up:
1. Validates and ensures 3NF database schema synchronization.
2. Computes all missing derived metrics (ROIC, Altman Z, Beneish M-Score, multi-year Growth CAGRs, Reverse DCF, Penman) for stocks in the database.
3. Spawns background worker queue tasks to pull latest filings and prices for universe stocks that lack public filings.
"""
from __future__ import annotations

import argparse
import logging
import sys
import threading
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Company, DerivedMetric, FinancialSnapshot, Score
from app.services.calculation_pipeline import populate_missing_metrics, run_company_pipeline

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("startup_pipeline")


def run_startup_sync(limit: int | None = None, sync_only: bool = True, force: bool = False) -> dict[str, int]:
    """Synchronous pass at startup: ensures metrics are computed for all companies in DB."""
    logger.info("Running startup pipeline: computing missing metrics for universe (limit=%s, sync_only=%s, force=%s)...", limit, sync_only, force)
    db = SessionLocal()
    try:
        res = populate_missing_metrics(db, limit=limit, fetch_live=not sync_only, force=force)
        logger.info(
            "Startup metrics check finished: scanned=%d, populated=%d, errors=%d, benchmarks=%d",
            res["scanned"],
            res["populated"],
            res["errors"],
            res.get("benchmarks", 0),
        )
        return res
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Startup pipeline for equity research app")
    parser.add_argument("--limit", type=int, default=None, help="Max companies to compute (default: all)")
    parser.add_argument("--sync-only", action="store_true", default=True, help="Run sync calculations only without network pulls (default: True)")
    parser.add_argument("--fetch-live", dest="sync_only", action="store_false", help="Enable live network pulls for missing filings")
    parser.add_argument("--force", action="store_true", default=False, help="Force recomputation across all companies")
    args = parser.parse_args()

    res = run_startup_sync(limit=args.limit, sync_only=args.sync_only, force=args.force)
    print(f"Startup pipeline completed: {res}", flush=True)


if __name__ == "__main__":
    main()
