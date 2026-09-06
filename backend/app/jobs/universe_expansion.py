"""Universe Expansion Job: Ingest and calculate Russell 1000, TSX, and Micro-Cap Equities.

Adds curated, institutional-grade equities:
1. Prominent Russell 1000 mid/large-cap equities not in S&P 500 (PLTR, SNOW, CRWD, APP, TTD, HOOD, MSTR, CELH, SMCI, etc.).
2. Top liquid Toronto (TSX) equities (CLS.TO, BBD-B.TO, MDA.TO, K.TO, CCO.TO, IVN.TO, DSG.TO, etc.).
3. High-quality Micro/Small-Cap operating companies (INOD, HROW, POWI, XPEL, etc.).

Runs the complete calculation pipeline (3NF statements, derived metrics, Altman Z, Beneish M, Reverse DCF, scores).
Tags all companies in the universe with their respective cohort tags.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Company, DerivedMetric, FinancialSnapshot, Score
from app.services.calculation_pipeline import run_company_pipeline
from app.services.etf_resolver import sync_universe_tags
from app.services.peer_engine import populate_peer_benchmarks
from app.services.scoring_service import recompute

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=False,
)
logger = logging.getLogger("universe_expansion")

# Curated Russell 1000 prominent mid/large cap equities
RUSSELL_1000_TARGETS = [
    "PLTR", "SNOW", "CRWD", "APP", "TTD", "HOOD", "MSTR", "CELH", "SMCI", "DELL",
    "APO", "KKR", "COIN", "PINS", "NET", "DDOG", "MDB", "DASH", "DKNG", "VRT",
    "GEV", "ARM", "SYM", "TOST", "CAVA", "RBLX", "DUOL", "AFRM", "SOFI", "BILL",
    "PATH", "S", "ZS", "TEAM", "HUBS", "ESTC", "MNDY", "IOT", "CFLT", "GTLB",
    "OKTA", "ALNY", "VKTX", "CRSP", "AXON",
]

# Top liquid Toronto (TSX) equities
TSX_TARGETS = [
    "CLS.TO", "BBD-B.TO", "MDA.TO", "K.TO", "CCO.TO", "IVN.TO", "DSG.TO", "LUN.TO",
    "ATRL.TO", "WSP.TO", "STN.TO", "OTEX.TO", "LSPD.TO", "RBA.TO", "FTT.TO", "CAE.TO",
    "TIH.TO", "ATS.TO", "FM.TO", "TFII.TO", "CPX.TO", "POW.TO", "DOL.TO", "GIB-A.TO",
    "NTR.TO",
]

# Quality Micro and Small-Cap equities with active SEC filings
MICROCAP_TARGETS = [
    "HROW", "INOD", "POWI", "XPEL", "ACMR", "TMDX", "PRCT", "PLMR", "CRSR", "AUDC",
]


def expand_and_populate_universe(db: Session, max_per_category: int | None = None) -> dict[str, Any]:
    """Ingests, parses statements, calculates derived metrics, and tags all expanded universe constituents."""
    logger.info("Starting universe expansion pipeline...")

    all_targets = [
        ("RUSSELL1000", RUSSELL_1000_TARGETS[:max_per_category] if max_per_category else RUSSELL_1000_TARGETS),
        ("TSX", TSX_TARGETS[:max_per_category] if max_per_category else TSX_TARGETS),
        ("MICROCAP", MICROCAP_TARGETS[:max_per_category] if max_per_category else MICROCAP_TARGETS),
    ]

    results = {"ingested": 0, "already_present": 0, "errors": 0, "details": []}

    for category, tickers in all_targets:
        logger.info("Processing category: %s (%d tickers)...", category, len(tickers))
        for ticker in tickers:
            try:
                clean_sym = ticker.replace(".TO", "").replace(".TSX", "").upper()
                comp = db.execute(
                    select(Company).where(
                        (Company.ticker == ticker)
                        | (Company.ticker == clean_sym)
                        | (Company.ticker == f"{clean_sym}.TO")
                    )
                ).scalars().first()

                has_complete_data = False
                if comp:
                    snap_count = db.execute(
                        select(FinancialSnapshot).where(FinancialSnapshot.company_id == comp.company_id)
                    ).scalars().all()
                    if len(snap_count) >= 3:
                        has_complete_data = True

                if has_complete_data and comp is not None:
                    logger.info("Ticker %s already complete in DB (%s). Ensuring metrics...", ticker, comp.company_id)
                    run_company_pipeline(db, comp.company_id, refresh=False, fetch_live=False, recompute_score=False)
                    results["already_present"] += 1
                else:
                    logger.info("Ingesting new / incomplete ticker: %s...", ticker)
                    res = run_company_pipeline(db, ticker, refresh=True, fetch_live=True, recompute_score=False)
                    results["ingested"] += 1
                    results["details"].append({"ticker": ticker, "status": "ingested", "cid": res.get("company_id")})

                db.commit()
            except Exception as exc:
                logger.warning("Failed processing ticker %s: %s", ticker, exc)
                results["errors"] += 1
                results["details"].append({"ticker": ticker, "status": "error", "error": str(exc)})
                db.rollback()

    # Step 2: Synchronize universe cohort tags
    logger.info("Synchronizing universe cohort tags across all companies...")
    tag_counts = sync_universe_tags(db)
    logger.info("Universe tags synchronized: %s", tag_counts)
    results["tags"] = tag_counts

    # Step 3: Recompute global scores & percentile distributions
    logger.info("Recomputing global scores and peer rankings...")
    score_res = recompute(db)
    results["scores"] = score_res
    logger.info("Score recompute finished: %s", score_res)

    # Step 4: Populate 3NF peer benchmarks
    logger.info("Populating 3NF peer benchmarks...")
    bm_count = populate_peer_benchmarks(db)
    results["benchmarks"] = bm_count
    logger.info("Peer benchmarks populated: %d rows", bm_count)

    return results


def main():
    db = SessionLocal()
    try:
        res = expand_and_populate_universe(db)
        print(f"Universe expansion complete: {res}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
