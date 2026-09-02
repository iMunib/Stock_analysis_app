"""Backfill job CLI + shared runner. CLI: python -m app.jobs.backfill

Note: since Phase 6A the HTTP endpoint enqueues async jobs (see app/api/jobs.py);
this module keeps the direct runners used by the worker and the CLI.
"""
from __future__ import annotations

import argparse
from collections import defaultdict

from sqlalchemy import select

from app.db import SessionLocal
from app.models import FinancialSnapshot
from app.providers.registry import ProviderRegistry
from app.services.ingest import get_or_create_company, ingest_price, ingest_statements
from app.services.mapping import build_ref, resolve


def ingest_ticker(db, query: str, registry: ProviderRegistry, refresh: bool = False) -> dict:
    result = resolve(query)
    ref = build_ref(result)
    company = get_or_create_company(
        db, ref.company_id, ref.ticker, ref.country, ref.currency, name=result.name,
    )
    statements = registry.fetch_annual_statements(ref)
    counts = ingest_statements(db, company, statements, refresh=refresh)
    quote = registry.fetch_price(ref)
    price_ok = ingest_price(db, company, quote)
    db.commit()
    years = sorted(
        (y for (y,) in db.execute(
            select(FinancialSnapshot.fiscal_year)
            .where(FinancialSnapshot.company_id == ref.company_id,
                   FinancialSnapshot.fiscal_year.isnot(None))
        ).all() if y is not None),
        reverse=True,
    )
    by_source: dict[str, int] = defaultdict(int)
    for stmt in statements:
        by_source[stmt.source] += 1
    return {
        "company_id": ref.company_id,
        "in_universe": result.in_universe,
        "provider_rows_by_source": dict(by_source),
        "db_fiscal_years": years,
        "year_count": len(years),
        "counts": counts,
        "price_filled": price_ok,
    }


def run_backfill(mode: str = "sample", limit: int = 5, refresh: bool = False) -> list[dict]:
    """Sample = AAPL, MSFT, RY.TO. All = whole universe (rate-limited, limit caps)."""
    registry = ProviderRegistry()
    if mode == "sample":
        targets = ["AAPL", "MSFT", "RY.TO"]
        if limit and limit > 3:
            targets = targets + ["XOM", "SHOP.TO"][: limit - 3]
        out = []
        db = SessionLocal()
        try:
            for t in targets:
                out.append(ingest_ticker(db, t, registry, refresh=refresh))
        finally:
            db.close()
        return out
    if mode == "all":
        from app.services.mapping import _universe_rows

        by_id, _ = _universe_rows()
        ids = sorted(by_id.keys())[:limit] if limit else sorted(by_id.keys())
        out = []
        db = SessionLocal()
        try:
            for i, cid in enumerate(ids, 1):
                parts = cid.split(":")
                query = parts[1] + (".TO" if parts[0] == "CA" else "")
                try:
                    out.append(ingest_ticker(db, query, registry, refresh=refresh))
                except Exception as exc:  # noqa: BLE001
                    out.append({"company_id": cid, "error": str(exc)})
                if i % 25 == 0:
                    print(f"[backfill] {i}/{len(ids)}", flush=True)
        finally:
            db.close()
        return out
    raise ValueError(f"unknown mode: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="sample", choices=["sample", "all"])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    for row in run_backfill(mode=args.mode, limit=args.limit, refresh=args.refresh):
        print(row, flush=True)
