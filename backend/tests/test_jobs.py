"""Phase 6A tests: async job queue. Network-free (worker disabled, runners monkeypatched)."""
from __future__ import annotations

import os

import pytest

from app.db import SessionLocal
from app.models import Job
from app.services import jobs as jobsvc
from app.services.job_worker import JobWorker


@pytest.fixture()
def jobs_client(client):
    """TestClient whose lifespan started with JOBS_WORKER_DISABLED=1 (see conftest):
    the queue is driven manually via JobWorker.process_one()."""
    return client


@pytest.fixture()
def clean_queue():
    """Purge jobs left by earlier tests: process_one claims the OLDEST queued
    job, so queue isolation between tests is required for deterministic runs."""
    db = SessionLocal()
    try:
        db.query(Job).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_enqueue_and_job_row(jobs_client):
    r = jobs_client.post("/api/v1/jobs/backfill", json={"mode": "sample", "limit": 1})
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "queued"
    assert body["job_id"]

    g = jobs_client.get(f"/api/v1/jobs/{body['job_id']}")
    assert g.status_code == 200
    job = g.json()
    assert job["kind"] == "backfill"
    assert job["payload"]["mode"] == "sample"
    assert job["progress_done"] == 0


def test_second_backfill_409(jobs_client, clean_queue):
    r1 = jobs_client.post("/api/v1/jobs/backfill", json={"mode": "sample", "limit": 1})
    assert r1.status_code == 202
    r2 = jobs_client.post("/api/v1/jobs/backfill", json={"mode": "sample", "limit": 1})
    assert r2.status_code == 409


def test_worker_processes_fake_job_to_succeeded(jobs_client, clean_queue, monkeypatch):
    """Monkeypatch the backfill runner so no network happens; worker must finish green
    with progress_done == progress_total and provider_stats attached."""
    called = {"tickers": []}

    def _fake_ingest(db, ticker, registry, refresh=False):
        called["tickers"].append(ticker)

    monkeypatch.setattr("app.services.job_worker.ingest_ticker", _fake_ingest)

    db = SessionLocal()
    job = jobsvc.enqueue(db, "backfill", {"mode": "all", "limit": 3})
    db.close()

    worker = JobWorker()
    assert worker.process_one() is True

    db = SessionLocal()
    try:
        row = jobsvc.get_job(db, job.id)
        assert row.status == "succeeded"
        assert row.progress_done == row.progress_total == 3
        assert set(jobsvc.provider_stats_of(row).keys()) >= {"tokens_remaining", "last_token_wait_ms"}
    finally:
        db.close()
    assert len(called["tickers"]) == 3


def test_worker_failure_marks_failed(jobs_client, clean_queue, monkeypatch):
    """Runner-level failures (not per-ticker, which are swallowed by design)
    must land in status=failed with the error text."""

    def _boom(self, db, job_id, payload):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(JobWorker, "_run_backfill", _boom)

    db = SessionLocal()
    job = jobsvc.enqueue(db, "backfill", {"mode": "sample", "limit": 1})
    db.close()

    worker = JobWorker()
    assert worker.process_one() is True

    db = SessionLocal()
    try:
        row = jobsvc.get_job(db, job.id)
        assert row.status == "failed"
        assert "provider exploded" in (row.error or "")
    finally:
        db.close()


def test_recent_jobs_shape(jobs_client):
    r = jobs_client.get("/api/v1/jobs?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["items"], list)
    assert body["method_version"] == "v1"


def test_job_404(jobs_client):
    assert jobs_client.get("/api/v1/jobs/nope").status_code == 404

