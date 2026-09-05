"""Bulk EDGAR + Yahoo backfill for the full universe.

Usage inside Docker container:
  python -m app.jobs.bulk_backfill [--limit N] [--refresh] [--sample]

SEC tickers cache must be pre-loaded at /app/data/sec_tickers_cache.json.
Skips companies that already have >= 3 years of dated history (unless --refresh).
After ingest, recomputes scores for all companies.
"""
from __future__ import annotations

import argparse
import time
from collections import defaultdict

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Company, FinancialSnapshot
from app.providers.registry import ProviderRegistry
from app.services.ingest import ingest_price, ingest_statements
from app.services.mapping import cik_for_unknown_us, yahoo_symbol_for
from app.services.scoring_service import recompute


def _needs_backfill(db, company_id: str, threshold: int = 3, refresh: bool = False) -> bool:
    if refresh:
        return True
    count = db.execute(
        select(func.count()).select_from(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.isnot(None),
            FinancialSnapshot.revenue.isnot(None),
        )
    ).scalar() or 0
    return count < threshold


def _resolve_cik(company: Company) -> int | None:
    if company.cik:
        return company.cik
    if company.country != "US":
        return None
    cik, _ = cik_for_unknown_us(company.ticker or "")
    return cik


def run_bulk_backfill(limit=None, refresh=False, sample=False, history_threshold=3):
    registry = ProviderRegistry()
    db = SessionLocal()
    try:
        query = select(Company).order_by(Company.company_id)
        if sample:
            query = query.limit(10)
        all_companies = db.execute(query).scalars().all()

        targets = [c for c in all_companies if _needs_backfill(db, c.company_id, history_threshold, refresh)]
        if limit:
            targets = targets[:limit]

        total = len(targets)
        print(f"[bulk_backfill] {total} companies to process", flush=True)

        stats = {"processed": 0, "ingested": 0, "skipped": 0, "errors": [], "by_source": defaultdict(int)}

        for i, company in enumerate(targets, 1):
            cid = company.company_id
            ticker = company.ticker or ""
            country = company.country or "US"

            cik = _resolve_cik(company)
            if cik and company.cik != cik:
                company.cik = cik
                db.flush()

            # CA tickers in DB already include .TO suffix (e.g. "AAV.TO").
            # yahoo_symbol_for expects bare tickers, so strip .TO before calling.
            bare_ticker = ticker
            if country == "CA" and ticker.upper().endswith(".TO"):
                bare_ticker = ticker[:-3]  # Remove .TO suffix
            yahoo_sym = yahoo_symbol_for(bare_ticker, country)

            from app.providers.base import CompanyRef
            ref = CompanyRef(
                company_id=cid, ticker=ticker, country=country,
                currency=company.currency or "USD",
                yahoo_symbol=yahoo_sym, cik=cik,
            )

            try:
                stmts = registry.fetch_annual_statements(ref)
                if stmts:
                    counts = ingest_statements(db, company, stmts, refresh=refresh)
                    quote = registry.fetch_price(ref)
                    if quote:
                        ingest_price(db, company, quote)
                    db.commit()
                    for stmt in stmts:
                        stats["by_source"][stmt.source] += 1
                    if counts.get("created", 0) > 0 or counts.get("filled_seed_nulls", 0) > 0:
                        stats["ingested"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    stats["skipped"] += 1

                stats["processed"] += 1
                if i % 10 == 0 or i == total:
                    print(f"[bulk_backfill] {i}/{total} -- ingested:{stats['ingested']} skipped:{stats['skipped']}", flush=True)
                time.sleep(0.1)

            except Exception as exc:
                db.rollback()
                err = f"{cid}: {exc}"
                stats["errors"].append(err)
                print(f"[bulk_backfill] ERROR {err}", flush=True)

        print("[bulk_backfill] Recomputing all scores...", flush=True)
        try:
            score_result = recompute(db)
            print(f"[bulk_backfill] Scores: {score_result}", flush=True)
        except Exception as exc:
            print(f"[bulk_backfill] Score recompute error: {exc}", flush=True)

        stats["by_source"] = dict(stats["by_source"])
        return stats
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--threshold", type=int, default=3)
    args = parser.parse_args()

    result = run_bulk_backfill(limit=args.limit, refresh=args.refresh, sample=args.sample, history_threshold=args.threshold)
    print("\n=== BULK BACKFILL COMPLETE ===")
    print(f"Processed: {result['processed']}")
    print(f"Ingested:  {result['ingested']}")
    print(f"Skipped:   {result['skipped']}")
    print(f"Errors:    {len(result['errors'])}")
    for e in result['errors'][:20]:
        print(f"  - {e}")
    print(f"By source: {result['by_source']}")
