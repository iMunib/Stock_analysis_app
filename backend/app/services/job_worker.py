"""Background job worker: one daemon thread, claims one queued job at a time.

Owns its own SQLAlchemy session (never shares a request session). Never raises
out of the thread - failures land in status=failed with the error text.
Progress is updated per ticker during backfills.
"""
from __future__ import annotations

import logging
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select

from app.config import REFRESH_ENABLED, REFRESH_INTERVAL_HOURS
from app.db import SessionLocal
from app.jobs.backfill import ingest_ticker
from app.models import Company, Job
from app.services import jobs as jobsvc
from app.providers.edgar import bucket_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=False,
)
logger = logging.getLogger("job_worker")

_POLL_SECONDS = 1.0


class JobWorker(threading.Thread):
    def __init__(self, poll_seconds: float = _POLL_SECONDS):
        super().__init__(name="job-worker", daemon=True)
        self.poll_seconds = poll_seconds
        self._stop = threading.Event()
        self._next_refresh_check = 0.0  # monotonic ts for the periodic refresh probe

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:  # pragma: no cover - loop body exercised via process_one
        while not self._stop.is_set():
            processed = False
            try:
                processed = self.process_one()
                self._maybe_enqueue_periodic_refresh()
            except Exception:  # absolutely never die
                traceback.print_exc()
            if not processed:
                self._stop.wait(self.poll_seconds)

    def _maybe_enqueue_periodic_refresh(self) -> None:
        """Stage C: optional timer (REFRESH_ENABLED=1). Enqueues a sample refresh if no
        job finished within REFRESH_INTERVAL_HOURS (default 168 = weekly). Off by default."""
        if not REFRESH_ENABLED:
            return
        now = time.monotonic()
        if now < self._next_refresh_check:
            return
        self._next_refresh_check = now + 3600.0  # probe hourly
        db = SessionLocal()
        try:
            last_finished = db.execute(
                select(Job.finished_at).order_by(Job.finished_at.desc()).limit(1)
            ).scalar_one_or_none()
            cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=REFRESH_INTERVAL_HOURS)
            recent = last_finished is not None and last_finished >= cutoff
            active = jobsvc.has_active(db, "refresh_universe")
            if not recent and not active:
                jobsvc.enqueue(db, "refresh_universe", {"mode": "sample", "limit": 5, "recompute": True})
                logger.info("periodic refresh_universe enqueued")
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        finally:
            db.close()

    def process_one(self) -> bool:
        """Claim and run at most one queued job. Returns True if one was run."""
        db = SessionLocal()
        try:
            job = jobsvc.claim_oldest_queued(db)
            if job is None:
                return False
            try:
                self._run_job(db, job.id, job.kind, jobsvc.payload_of(job))
                db.refresh(job)
                if job.status == "failed" or job.step == "failed":
                    jobsvc.finish(db, job.id, ok=False, error=job.error, provider_stats=bucket_state())
                else:
                    jobsvc.finish(db, job.id, ok=True, provider_stats=bucket_state())
            except Exception as exc:  # noqa: BLE001 - job failures are data, not crashes
                traceback.print_exc()
                jobsvc.finish(db, job.id, ok=False, error=f"{exc.__class__.__name__}: {exc}", provider_stats=bucket_state(), error_code="INTERNAL")
            return True
        finally:
            db.close()

    # ---- job runners -------------------------------------------------

    def _run_job(self, db, job_id: str, kind: str, payload: dict[str, Any]) -> None:
        if kind == "backfill":
            self._run_backfill(db, job_id, payload)
        elif kind == "refresh_universe":
            # Phase 10C: backfill sample/limit tickers, then recompute the seed universe.
            self._run_backfill(db, job_id, payload)
            from app.services.scoring_service import recompute

            recompute(db)
        elif kind == "recompute":
            from app.services.scoring_service import recompute

            recompute(db, company_id=payload.get("company_id"))
            jobsvc.set_progress(db, job_id, 1, 1)
        elif kind == "ingest":
            self._run_ingest_state_machine(db, job_id, payload)
        else:
            raise ValueError(f"unknown job kind: {kind}")

    def _run_ingest_state_machine(self, db, job_id: str, payload: dict[str, Any]) -> None:
        from app.providers.registry import ProviderRegistry
        from app.services.mapping import resolve, build_ref, MappingError
        from app.services.ingest import get_or_create_company, ingest_statements, ingest_price
        from app.services.scoring_service import recompute
        from app.models import Score

        ticker_query = str(payload.get("ticker") or "").strip()
        refresh = bool(payload.get("refresh"))

        # Step 1: resolve
        jobsvc.set_step(db, job_id, step="resolve", message=f"Resolving ticker '{ticker_query}'...")
        try:
            res = resolve(ticker_query)
            ref = build_ref(res)
        except MappingError as exc:
            msg = str(exc)
            if "LISTING_AMBIGUOUS" in msg:
                jobsvc.fail_job(db, job_id, error_code="LISTING_AMBIGUOUS", message="Multiple listings. Pick US ADR or HK/TSX (show choices).")
                return
            jobsvc.fail_job(db, job_id, error_code="SYMBOL_NOT_FOUND", message="We could not find that ticker. Try AMD, BABA, SHOP.TO, or KITS.TO.")
            return
        except Exception as exc:
            jobsvc.fail_job(db, job_id, error_code="INTERNAL", message=f"Error resolving ticker: {exc}")
            return

        company_id = ref.company_id
        company = get_or_create_company(db, ref.company_id, ref.ticker, ref.country, ref.currency, name=res.name)
        if ref.cik and not company.cik:
            company.cik = ref.cik
        db.commit()
        jobsvc.set_step(db, job_id, step="resolve", message=f"Resolved to {company_id} ({res.name or ref.ticker})", company_id=company_id)

        # Step 2: filings
        jobsvc.set_step(db, job_id, step="filings", message=f"Fetching annual filings for {ref.ticker}...", company_id=company_id)
        registry = ProviderRegistry()
        try:
            statements = registry.fetch_annual_statements(ref)
            counts = ingest_statements(db, company, statements, refresh=refresh)
            db.commit()
        except TimeoutError:
            jobsvc.fail_job(db, job_id, error_code="PROVIDER_TIMEOUT", message="Data source timed out. Retry.", company_id=company_id)
            return
        except RuntimeError as exc:
            if "back-off" in str(exc).lower() or "rate" in str(exc).lower():
                jobsvc.fail_job(db, job_id, error_code="RATE_LIMIT", message="Source is busy. Wait a minute and retry.", company_id=company_id)
                return
            jobsvc.fail_job(db, job_id, error_code="INTERNAL", message=f"Error fetching filings: {exc}", company_id=company_id)
            return
        except Exception as exc:
            jobsvc.fail_job(db, job_id, error_code="INTERNAL", message=f"Error fetching filings: {exc}", company_id=company_id)
            return

        num_statements = len(statements)
        filing_desc = getattr(company, "filing_type", "annual") or "annual"
        rep_cur = company.reporting_currency or ref.currency
        jobsvc.set_step(db, job_id, step="filings", message=f"Fetched {num_statements} FY statements ({filing_desc}, {rep_cur})", company_id=company_id)

        # Step 3: prices_shares
        jobsvc.set_step(db, job_id, step="prices_shares", message=f"Pulling price and shares for {ref.ticker} from Yahoo...", company_id=company_id)
        try:
            quote = registry.fetch_price(ref)
            ingest_price(db, company, quote)
            db.commit()
        except Exception as exc:
            logger.warning("price fetch error for %s: %s", ref.ticker, exc)

        # Step 4: sector_peers
        jobsvc.set_step(db, job_id, step="sector_peers", message=f"Finding peers and assigning sector for {ref.ticker}...", company_id=company_id)
        if not company.gics_sector:
            company.gics_sector = "Unknown"
        if not company.custom_industry_sheet:
            company.custom_industry_sheet = company.gics_sector
        db.commit()

        # Step 5: score & TTM & forensic metrics
        jobsvc.set_step(db, job_id, step="score", message=f"Computing Math v1 score, TTM, and peer rankings for {ref.ticker}...", company_id=company_id)
        from app.services.calculation_pipeline import run_company_pipeline
        try:
            run_company_pipeline(db, company_id, refresh=refresh, fetch_live=False)
        except Exception as exc:
            logger.warning("pipeline computation error for %s: %s", company_id, exc)
            recompute(db, company_id=company_id)
            try:
                from app.services.ttm_engine import compute_and_store_ttm
                compute_and_store_ttm(db, company_id)
                db.commit()
            except Exception:
                pass
        score_row = db.get(Score, company_id)

        # Step 6: done / partial check
        warning_code = None
        if num_statements == 0:
            warning_code = "NO_STATEMENTS"
            msg = "Listed, but no annual statements. We stored the price only."
        elif score_row is not None and score_row.coverage is not None and score_row.coverage < 4:
            warning_code = "SCORE_PARTIAL"
            msg = f"Saved, but some pillars missing ({score_row.coverage}/4 scored). See 'What is missing'."
        else:
            msg = f"Successfully ingested and scored {company_id}."

        jobsvc.set_step(db, job_id, step="done", message=msg, company_id=company_id, error_code=warning_code)
        jobsvc.set_progress(db, job_id, 1, 1)

    def _run_backfill(self, db, job_id: str, payload: dict[str, Any]) -> None:
        from app.providers.registry import ProviderRegistry
        from app.services.mapping import _universe_rows

        mode = payload.get("mode", "sample")
        limit = int(payload.get("limit") or 5)
        refresh = bool(payload.get("refresh"))
        registry = ProviderRegistry()

        if mode == "company":
            # Trust sprint C: refresh a single company's price + statements, then
            # recompute TTM/reverse-DCF provenance locally. No re-ingest of the seed.
            cid = str(payload.get("company_id") or "").strip()
            if not cid:
                jobsvc.fail_job(db, job_id, error_code="BAD_REQUEST", message="company_id required for mode=company")
                return
            company = db.get(Company, cid)
            if company is None:
                jobsvc.fail_job(db, job_id, error_code="COMPANY_NOT_FOUND", message=f"unknown company_id: {cid}")
                return
            ticker = company.ticker or cid.split(":")[1]
            targets = [ticker + (".TO" if (company.country or "") == "CA" else "")]
        elif mode == "sample":
            targets = ["AAPL", "MSFT", "RY.TO"]
            if limit > 3:
                targets += ["XOM", "SHOP.TO"][: limit - 3]
        else:
            by_id, _ = _universe_rows()
            ids = sorted(by_id.keys())[:limit] if limit else sorted(by_id.keys())
            targets = [p[1] + (".TO" if p[0] == "CA" else "") for p in (cid.split(":") for cid in ids)]

        jobsvc.set_progress(db, job_id, 0, len(targets))
        for i, ticker in enumerate(targets, 1):
            try:
                ingest_ticker(db, ticker, registry, refresh=refresh)
            except Exception as exc:  # noqa: BLE001 - one bad ticker must not fail the job
                db.rollback()
                logger.warning("[job %s] ticker %s failed: %s", job_id, ticker, exc)
            jobsvc.set_progress(db, job_id, i, len(targets))