"""Background job worker: one daemon thread, claims one queued job at a time.

Owns its own SQLAlchemy session (never shares a request session). Never raises
out of the thread — failures land in status=failed with the error text.
Progress is updated per ticker during backfills.
"""
from __future__ import annotations

import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select

from app.config import REFRESH_ENABLED, REFRESH_INTERVAL_HOURS
from app.db import SessionLocal
from app.jobs.backfill import ingest_ticker
from app.models import Job
from app.services import jobs as jobsvc
from app.providers.edgar import bucket_state

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
                print("[worker] periodic refresh_universe enqueued", flush=True)
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
                jobsvc.finish(db, job.id, ok=True, provider_stats=bucket_state())
            except Exception as exc:  # noqa: BLE001 - job failures are data, not crashes
                traceback.print_exc()
                jobsvc.finish(db, job.id, ok=False, error=f"{exc.__class__.__name__}: {exc}", provider_stats=bucket_state())
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
            from app.providers.registry import ProviderRegistry

            registry = ProviderRegistry()
            ingest_ticker(db, str(payload.get("ticker") or ""), registry, refresh=bool(payload.get("refresh")))
            jobsvc.set_progress(db, job_id, 1, 1)
        else:
            raise ValueError(f"unknown job kind: {kind}")

    def _run_backfill(self, db, job_id: str, payload: dict[str, Any]) -> None:
        from app.providers.registry import ProviderRegistry
        from app.services.mapping import _universe_rows

        mode = payload.get("mode", "sample")
        limit = int(payload.get("limit") or 5)
        refresh = bool(payload.get("refresh"))
        registry = ProviderRegistry()

        if mode == "sample":
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
                print(f"[job {job_id}] ticker {ticker} failed: {exc}", flush=True)
            jobsvc.set_progress(db, job_id, i, len(targets))
