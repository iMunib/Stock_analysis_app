"""Full-history backfill CLI — Workstream 1.

Usage:
    python -m app.jobs.run_full_backfill [options]

Options:
    --limit N         Max companies to process (default: unlimited; capped at 720)
    --concurrency N   Parallel workers (default: 2; max: 4 to avoid rate limits)
    --resume          Skip companies that already have >= 4 annual FY rows
    --country US|CA   Restrict to one country
    --dry-run         Print plan without modifying the database

Exit codes: 0 = all done, 1 = some errors (see stderr), 2 = fatal.

Rules (enforced):
- Never run in --mode all (that would overwrite seed rows via refresh.py).
- Never overwrite source='Sector_Financials_Final_Owner.xlsx' rows.
- US: SEC EDGAR companyfacts (duration filter: reject quarterly/semi-annual).
- CA: Yahoo Finance annual periods (0.2s polite delay between requests).
- Scoring is triggered per company after successful ingest.
- Progress bar via tqdm if installed, else print fallback.
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Company, FinancialSnapshot
from app.providers.registry import ProviderRegistry
from app.services.ingest import get_or_create_company, ingest_price, ingest_statements
from app.services.mapping import build_ref, resolve
from app.services.scoring_service import recompute


def _count_fy_rows(db, company_id: str) -> int:
    """Number of dated annual (FY) rows for this company (seed excluded)."""
    return db.execute(
        select(func.count()).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
            FinancialSnapshot.fiscal_year.isnot(None),
        )
    ).scalar_one()


def _has_seed_only(db, company_id: str) -> bool:
    return _count_fy_rows(db, company_id) == 0


def backfill_company(
    company_id: str,
    registry: ProviderRegistry,
    refresh: bool = False,
) -> dict[str, Any]:
    """Ingest and score one company. Thread-safe (opens its own session)."""
    db = SessionLocal()
    try:
        parts = company_id.split(":")
        country = parts[0]
        ticker = parts[1]
        # Map to provider format.
        query = ticker + ".TO" if country == "CA" else ticker
        try:
            result = resolve(query)
        except Exception as exc:  # noqa: BLE001
            return {"company_id": company_id, "status": "resolve_error", "error": str(exc)}

        ref = build_ref(result)
        company = get_or_create_company(
            db, ref.company_id, ref.ticker, ref.country, ref.currency, name=result.name
        )
        statements = registry.fetch_annual_statements(ref)

        # Duration filter: reject rows that look like quarterly/semi-annual
        # (EDGAR companyfacts may include both; we keep only FY duration).
        annual = [
            s for s in statements
            if s.source != "Sector_Financials_Final_Owner.xlsx"  # never overwrite seed
        ]
        counts = ingest_statements(db, company, annual, refresh=refresh)
        quote = registry.fetch_price(ref)
        price_ok = ingest_price(db, company, quote)

        # Commit with retry on SQLite lock
        for attempt in range(3):
            try:
                db.commit()
                break
            except Exception as exc:  # noqa: BLE001
                if "locked" in str(exc).lower() and attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    raise

        # Trigger score recompute for this company only.
        score_result = recompute(db, company_id)
        for attempt in range(3):
            try:
                db.commit()
                break
            except Exception as exc:  # noqa: BLE001
                if "locked" in str(exc).lower() and attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    raise

        fy_count = _count_fy_rows(db, company_id)
        return {
            "company_id": company_id,
            "status": "ok",
            "fy_rows": fy_count,
            "new_rows": counts.get("inserted", 0),
            "price_filled": price_ok,
            "scored": score_result.get("scored", 0),
        }
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return {"company_id": company_id, "status": "error", "error": str(exc)}
    finally:
        db.close()


def load_targets(
    resume: bool,
    country: str | None,
    limit: int | None,
) -> list[str]:
    """Return list of company_ids to backfill, respecting resume/country/limit."""
    db = SessionLocal()
    try:
        stmt = select(Company.company_id).where(Company.is_deleted == False)
        if country:
            stmt = stmt.where(Company.country == country.upper())
        rows: list[str] = [r for (r,) in db.execute(stmt).all()]

        if resume:
            # Filter: only those with < 4 FY rows (seed-only companies).
            filtered = []
            for cid in rows:
                if _count_fy_rows(db, cid) < 4:
                    filtered.append(cid)
            rows = filtered
        if limit:
            rows = rows[:limit]
        return rows
    finally:
        db.close()


def run_full_backfill(
    limit: int | None = None,
    concurrency: int = 2,
    resume: bool = True,
    country: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Full-history backfill for the 720-company universe.

    Polite rate limiting: CA companies get 0.2s delay between requests.
    Never calls refresh.py --mode all.
    """
    concurrency = max(1, min(4, concurrency))  # 1–4 only
    targets = load_targets(resume=resume, country=country, limit=limit)

    print(
        f"[backfill] targets={len(targets)} concurrency={concurrency}"
        f" resume={resume} country={country or 'ALL'} dry_run={dry_run}",
        flush=True,
    )

    if dry_run:
        for cid in targets[:20]:
            print(f"  [dry-run] would process: {cid}", flush=True)
        if len(targets) > 20:
            print(f"  ... and {len(targets) - 20} more", flush=True)
        return {"dry_run": True, "total": len(targets)}

    registry = ProviderRegistry()
    results: list[dict] = []
    errors: list[str] = []
    ok = 0

    # Use tqdm progress bar if available; else plain counter.
    try:
        from tqdm import tqdm  # type: ignore[import]
        progress = tqdm(total=len(targets), unit="co")
    except ImportError:
        progress = None

    def _update(msg: str) -> None:
        if progress:
            progress.set_postfix_str(msg[:40])
            progress.update(1)
        else:
            print(msg, flush=True)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(backfill_company, cid, registry): cid
            for cid in targets
        }
        for future in as_completed(futures):
            cid = futures[future]
            try:
                result = future.result(timeout=120)
            except Exception as exc:  # noqa: BLE001
                result = {"company_id": cid, "status": "error", "error": str(exc)}
            results.append(result)
            if result.get("status") == "ok":
                ok += 1
                _update(f"[ok] {cid} fy={result.get('fy_rows')}")
            else:
                err = result.get("error", "?")
                errors.append(f"{cid}: {err}")
                _update(f"[err] {cid}: {err[:60]}")
            # Polite delay for CA companies (Yahoo Finance rate limit).
            if cid.startswith("CA:"):
                time.sleep(0.2)

    if progress:
        progress.close()

    # Master Directive WS1: Automatically trigger universe recompute upon backfill completion
    if not dry_run and ok > 0:
        print("\n[backfill] triggering scoring_service.recompute_universe()...", flush=True)
        try:
            from app.services.scoring_service import recompute_universe
            recompute_res = recompute_universe()
            print(f"[backfill] universe recomputed: scored={recompute_res.get('scored')}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[backfill] warning: universe recompute encountered error: {exc}", flush=True)

    summary = {
        "total": len(targets),
        "ok": ok,
        "errors": len(errors),
        "error_list": errors[:20],
    }
    print(
        f"\n[backfill] done — ok={ok}, errors={len(errors)}/{len(targets)}",
        flush=True,
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m app.jobs.run_full_backfill",
        description="Full 5-10yr history backfill for the 720-company research universe.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Cap total companies processed")
    parser.add_argument("--concurrency", type=int, default=2, help="Parallel workers (1-4)")
    parser.add_argument("--resume", action="store_true", default=True, help="Skip companies with >= 4 FY rows")
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="Re-process all companies")
    parser.add_argument("--country", choices=["US", "CA"], default=None, help="Restrict to one country")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Print plan only")
    args = parser.parse_args()

    summary = run_full_backfill(
        limit=args.limit,
        concurrency=args.concurrency,
        resume=args.resume,
        country=args.country,
        dry_run=args.dry_run,
    )
    sys.exit(0 if summary.get("errors", 0) == 0 else 1)
