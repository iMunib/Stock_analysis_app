"""Batch Universe Expansion Job.

Expands the stock universe by ingesting 85+ prominent, high-demand US and Canadian
equities across key sectors:
- Dining & Fast-Casual Compounders (WING, TXRH, SHAK, BROS, DNUT, SG)
- Consumer, Retail, Footwear & Apparel (BOOT, OLLI, FIVE, CHWY, ETSY, W, ELF, BIRK, SN, ONON, YETI, BURL, RH, BBWI, POOL, DKS, YUMC)
- Enterprise Tech, Cloud, AI & Software (TWLO, ZM, CPNG, GFS, UI, ALAB, CACI, DOCN, FROG, NCNO, BLKB, ALRM, WK, RPD, TENB, VRNS)
- Semiconductors & Hardware (RMBS, CRUS, LSCC, SYNA, SITM, POWL, AEIS, SMTC, DIOD)
- Healthcare, MedTech, Diagnostics & Biotech (DXCM, ILMN, NTRA, BMRN, INSM, INSP, PEN, TNDM, PACB, GH, RVMD, KYMR, ARVN, ALKS, NEO)
- Defense, Aerospace, Energy & CleanTech (HEI, BWXT, CW, WWD, BE, LNG, ENPH, RUN, ATI, KTOS, AVAV)
- Financial Exchanges, Brokerages & Industrials Compounders (MKTX, LPLA, SF, EXPO, TREX, WSO, AWI, IBP, RKT)
- Logistics & Transportation (XPO, SAIA, KNX, LSTR)
- TSX Compounders & Digital Assets (HUT.TO, BITF.TO)

Performs:
1. Multi-year statement ingestion from SEC EDGAR (US) and Yahoo Finance (CA).
2. Live quote, shares, and market cap extraction.
3. 3NF normalized metrics derivation (Altman Z, Beneish M, Penman, Reverse DCF, CAGRs, ROIC).
4. Automated GICS sector, industry, and placement assignment.
5. Cohort tagging, universe recomputation, and peer benchmark generation.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Company, DerivedMetric, FinancialSnapshot, Placement, Score
from app.services.calculation_pipeline import run_company_pipeline
from app.services.etf_resolver import sync_universe_tags
from app.services.peer_engine import populate_peer_benchmarks
from app.services.scoring_service import recompute
from app.services.sector_cache import materialize_sector_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=False,
)
logger = logging.getLogger("batch_universe_expansion")

GICS_MAP = {
    "Technology": "Information Technology",
    "Healthcare": "Health Care",
    "Financial Services": "Financials",
    "Consumer Cyclical": "Consumer Discretionary",
    "Consumer Defensive": "Consumer Staples",
    "Communication Services": "Communication Services",
    "Industrials": "Industrials",
    "Energy": "Energy",
    "Basic Materials": "Materials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
}

EXPANSION_TARGETS = [
    # Dining & Fast-Casual (6)
    "WING", "TXRH", "SHAK", "BROS", "DNUT", "SG",
    
    # Consumer, Retail, Footwear & Apparel (17)
    "BOOT", "OLLI", "FIVE", "CHWY", "ETSY", "W", "ELF", "BIRK", "SN", "ONON",
    "YETI", "BURL", "RH", "BBWI", "POOL", "DKS", "YUMC",
    
    # Enterprise Tech, Cloud, AI & Software (16)
    "TWLO", "ZM", "CPNG", "GFS", "UI", "ALAB", "CACI", "DOCN", "FROG", "NCNO",
    "BLKB", "ALRM", "WK", "RPD", "TENB", "VRNS",
    
    # Semiconductors & Electronic Hardware (9)
    "RMBS", "CRUS", "LSCC", "SYNA", "SITM", "POWL", "AEIS", "SMTC", "DIOD",
    
    # Healthcare, MedTech, Diagnostics & Biotech (15)
    "DXCM", "ILMN", "NTRA", "BMRN", "INSM", "INSP", "PEN", "TNDM", "PACB", "GH",
    "RVMD", "KYMR", "ARVN", "ALKS", "NEO",
    
    # Defense, Aerospace, Energy & CleanTech (11)
    "HEI", "BWXT", "CW", "WWD", "BE", "LNG", "ENPH", "RUN", "ATI", "KTOS", "AVAV",
    
    # Financial Exchanges, Brokerages & Industrials Compounders (9)
    "MKTX", "LPLA", "SF", "EXPO", "TREX", "WSO", "AWI", "IBP", "RKT",
    
    # Logistics & Transportation (4)
    "XPO", "SAIA", "KNX", "LSTR",
    
    # TSX Compounders & Digital Assets (2)
    "HUT.TO", "BITF.TO",
    
    # Consumer Brands
    "KTB",
    
    # Reddit & Retail High-Demand Tech/AI/Space/Nuclear/Clean Energy
    "ASTS", "TEM", "RIVN", "JOBY", "ACHR", "LCID", "AI", "SOUN", "PLUG", "LUNR",
    "QS", "CHPT", "ENVX", "MARA", "RIOT", "CLSK", "IREN", "WULF", "CIFR", "CORZ",
    "OKLO", "SMR", "NNE", "FLNC", "EOSE", "ARRY", "SHLS", "SPCE", "PL", "RDW",
    
    # Dining & Restaurant Compounders
    "CAKE", "EAT", "PZZA", "BJRI", "PLAY", "JACK", "BLMN",
    
    # Apparel & Footwear Compounders
    "ANF", "AEO", "URBN", "GAP", "CPRI", "LEVI", "VFC", "PVH",
    
    # Internet, FinTech & Growth
    "SNAP", "MTCH", "ZG", "OPEN", "UPST", "CVNA",
    
    # Financial Exchanges & Consumer Lending
    "CBOE", "NDAQ", "ALLY", "SLM",
    
    # Travel, Leisure & Hospitality
    "RCL", "CCL", "NCLH", "MAR", "HLT", "H", "WH", "TRIP",
]


def assign_sector_and_placements(db: Session, company: Company, ticker: str) -> None:
    """Fetches sector/industry info from Yahoo and updates company & placements."""
    import yfinance as yf
    query_sym = ticker
    if company.country == "CA" and not query_sym.upper().endswith(".TO"):
        query_sym = f"{query_sym}.TO"

    try:
        tk = yf.Ticker(query_sym)
        info = tk.info or {}
        raw_sec = info.get("sector")
        raw_ind = info.get("industry")
        gics = GICS_MAP.get(raw_sec, raw_sec)

        if gics and not company.gics_sector:
            company.gics_sector = gics
        if raw_ind and not company.gics_industry:
            company.gics_industry = raw_ind
        if raw_ind and not company.custom_industry_sheet:
            company.custom_industry_sheet = raw_ind

        # Add placements
        sheets_to_add = []
        if company.gics_sector:
            sheets_to_add.append((company.gics_sector, "GICS"))
        if company.custom_industry_sheet:
            sheets_to_add.append((company.custom_industry_sheet, "Primary"))

        for sheet_name, role in sheets_to_add:
            existing = db.execute(
                select(Placement).where(
                    Placement.company_id == company.company_id,
                    Placement.sheet_name == sheet_name,
                    Placement.placement_role == role,
                )
            ).scalar_one_or_none()
            if not existing:
                db.add(Placement(company_id=company.company_id, sheet_name=sheet_name, placement_role=role))
        db.flush()
    except Exception as exc:
        logger.warning("Failed assigning sector for %s (%s): %s", ticker, company.company_id, exc)


def run_batch_expansion(db: Session, targets: list[str] | None = None) -> dict[str, Any]:
    """Executes ingestion, metric calculation, sector assignment, and universe recalibration."""
    ticker_list = targets or EXPANSION_TARGETS
    total = len(ticker_list)
    logger.info("Starting batch universe expansion for %d tickers...", total)

    stats = {
        "total_targets": total,
        "processed": 0,
        "success": 0,
        "errors": 0,
        "error_details": [],
        "snapshots_added": 0,
        "metrics_added": 0,
    }

    start_time = time.time()

    for idx, ticker in enumerate(ticker_list, 1):
        clean_sym = ticker.replace(".TO", "").replace(".TSX", "").upper()
        logger.info("[%d/%d] Ingesting ticker: %s...", idx, total, ticker)

        try:
            # Check if company already has complete data
            existing_comp = db.execute(
                select(Company).where(
                    (Company.ticker == ticker)
                    | (Company.ticker == clean_sym)
                    | (Company.ticker == f"{clean_sym}.TO")
                )
            ).scalars().first()

            has_complete_data = False
            if existing_comp:
                snaps = db.scalar(
                    select(func.count(FinancialSnapshot.id)).where(FinancialSnapshot.company_id == existing_comp.company_id)
                ) or 0
                if snaps >= 3:
                    has_complete_data = True

            if has_complete_data and existing_comp is not None:
                logger.info("Ticker %s already has %d snapshots in DB (%s). Ensuring derived metrics...", ticker, snaps, existing_comp.company_id)
                res = run_company_pipeline(db, existing_comp.company_id, refresh=False, fetch_live=False, recompute_score=False)
                cid = existing_comp.company_id
                company = existing_comp
            else:
                # Step 1: Run complete calculation pipeline (statement ingest + 3NF metrics derivation)
                res = run_company_pipeline(db, ticker, refresh=True, fetch_live=True, recompute_score=False)
                cid = res.get("company_id")
                if not cid:
                    raise ValueError(f"No company_id returned for {ticker}")
                company = db.get(Company, cid)

            if company is not None:
                # Step 2: Assign sector and placements
                assign_sector_and_placements(db, company, ticker)

            db.commit()

            snap_count = db.scalar(
                select(func.count(FinancialSnapshot.id)).where(FinancialSnapshot.company_id == cid)
            ) or 0
            metric_count = db.scalar(
                select(func.count(DerivedMetric.id)).where(DerivedMetric.company_id == cid)
            ) or 0

            stats["success"] += 1
            stats["snapshots_added"] += snap_count
            stats["metrics_added"] += metric_count
            logger.info("SUCCESS %s (%s): %d snapshots, %d metrics", ticker, cid, snap_count, metric_count)

        except Exception as exc:
            logger.warning("FAILED %s: %s", ticker, exc)
            stats["errors"] += 1
            stats["error_details"].append({"ticker": ticker, "error": str(exc)})
            db.rollback()

        stats["processed"] += 1

    elapsed = round(time.time() - start_time, 2)
    logger.info("Ingestion phase complete in %s seconds. Re-ranking universe...", elapsed)

    # Step 3: Synchronize universe cohort tags
    try:
        logger.info("Synchronizing universe cohort tags...")
        tag_counts = sync_universe_tags(db)
        stats["cohort_tags"] = tag_counts
    except Exception as exc:
        logger.warning("Tag sync error: %s", exc)

    # Step 4: Recompute global scores & peer percentiles across the whole universe
    try:
        logger.info("Recomputing global scores and peer rankings...")
        score_res = recompute(db)
        stats["score_recompute"] = score_res
    except Exception as exc:
        logger.warning("Score recompute error: %s", exc)

    # Step 5: Populate 3NF peer benchmarks
    try:
        logger.info("Populating peer benchmarks...")
        bm_count = populate_peer_benchmarks(db)
        stats["peer_benchmarks"] = bm_count
    except Exception as exc:
        logger.warning("Peer benchmark error: %s", exc)

    # Step 6: Materialize sector cache summaries
    try:
        logger.info("Materializing sector cache summaries...")
        sector_rows = materialize_sector_cache(db)
        stats["sector_cache_rows"] = sector_rows
    except Exception as exc:
        logger.warning("Sector cache error: %s", exc)

    final_company_count = db.scalar(select(func.count(Company.company_id))) or 0
    stats["final_company_count"] = final_company_count
    stats["elapsed_seconds"] = elapsed

    logger.info("Batch universe expansion complete! Final company count: %d", final_company_count)
    return stats


def main():
    db = SessionLocal()
    try:
        results = run_batch_expansion(db)
        print("\n--- BATCH UNIVERSE EXPANSION RESULTS ---")
        print(f"Total Targets: {results['total_targets']}")
        print(f"Success: {results['success']}")
        print(f"Errors: {results['errors']}")
        print(f"Total Snapshots Ingested: {results['snapshots_added']}")
        print(f"Total Metrics Derived: {results['metrics_added']}")
        print(f"Final Universe Size: {results['final_company_count']} companies")
        print(f"Elapsed Time: {results['elapsed_seconds']}s")
    finally:
        db.close()


if __name__ == "__main__":
    main()
