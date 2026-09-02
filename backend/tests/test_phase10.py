"""Phase 10 tests: secrets hygiene, llm status/free latch, narration cache, refresh job."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK
from app.db import SessionLocal
from app.main import app
from app.models import Score
from app.services import jobs as jobsvc
from app.services.job_worker import JobWorker
from app.services.llm import free_latch, llm_status


@pytest.fixture(scope="module")
def scored():
    with TestClient(app) as c:
        r = c.post("/api/v1/scores/recompute", json={"universe": "seed"})
        assert r.status_code == 200
        yield c


# ---------- secrets hygiene ----------

def test_env_example_has_placeholders_only():
    from pathlib import Path

    p = Path(__file__).resolve().parents[2] / ".env.example"
    text = p.read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY=" in text
    for line in text.splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            assert line.split("=", 1)[1].strip() in ("", "***"), "no real key in .env.example"


def test_gitignore_covers_env():
    from pathlib import Path

    p = Path(__file__).resolve().parents[2] / ".gitignore"
    text = p.read_text(encoding="utf-8")
    for needle in (".env", ".env.local", ".env.*", "!.env.example", "playwright-report/", "test-results/"):
        assert needle in text, f".gitignore missing {needle}"


def test_llm_status_never_contains_key(scored):
    r = scored.get("/api/v1/llm/status")
    assert r.status_code == 200
    body = r.json()
    assert body["free_latch"] is True
    assert "configured" in body and "model" in body and "fallback" in body
    raw = r.text
    assert "sk-" not in raw.lower()
    assert OPENROUTER_MODEL in body["model"]


# ---------- free latch ----------

def test_free_latch_refuses_non_free():
    assert free_latch("nvidia/nemotron-3-ultra-550b-a55b:free") is True
    assert free_latch("openai/gpt-4o") is False
    assert free_latch("minimax/minimax-m3:free") is True
    assert free_latch("") is False


def test_llm_status_unconfigured_without_key(monkeypatch):
    import app.services.llm as l

    monkeypatch.setattr(l, "OPENROUTER_API_KEY", None)
    s = l.llm_status("nvidia/nemotron-3-ultra-550b-a55b:free", "minimax/minimax-m3:free")
    assert s["configured"] is False


# ---------- narration: refused / unavailable / cache ----------

def test_narrate_refuses_non_free_model(monkeypatch, scored):
    import app.config as cfg
    import app.services.llm as l

    monkeypatch.setattr(l, "OPENROUTER_API_KEY", "test-key-not-real")
    calls = {"n": 0}

    def _boom(model, facts, timeout=45.0):
        calls["n"] += 1
        raise ValueError(f"refusing non-free model: {model}")

    monkeypatch.setattr(l, "_chat", _boom)
    # a non-:free default would be refused before any HTTP call
    assert free_latch("openai/gpt-4o") is False
    try:
        l._chat("openai/gpt-4o", {})
    except ValueError as exc:
        assert "refusing non-free model" in str(exc)
    assert calls["n"] == 1  # the ValueError path, never an HTTP attempt


def test_narrate_company_unconfigured_returns_facts(scored, monkeypatch):
    import app.services.llm as l

    monkeypatch.setattr(l, "OPENROUTER_API_KEY", None)
    r = scored.post("/api/v1/companies/US:AAPL:US/narrate")
    assert r.status_code == 503
    body = r.json()["detail"]
    assert body["narration_unavailable"] is True
    # facts are still returned so the UI stays informative
    assert body["facts"]["identity"]["company_id"] == "US:AAPL:US"
    assert "OPENROUTER_API_KEY missing" in body["reason"]


def test_narrate_company_cache_hit_skips_http(scored, monkeypatch):
    import app.services.llm as l
    import app.services.narration as n

    monkeypatch.setattr(l, "OPENROUTER_API_KEY", "test-key-not-real")
    called = {"http": 0}

    def _fake_chat(model, facts, timeout=45.0):
        called["http"] += 1
        return f"Test narration from {model}."

    monkeypatch.setattr(l, "_chat", _fake_chat)
    r1 = scored.post("/api/v1/companies/US:AAPL:US/narrate")
    assert r1.status_code == 200
    assert r1.json()["narration"].startswith("Test narration from")
    r2 = scored.post("/api/v1/companies/US:AAPL:US/narrate")
    assert r2.status_code == 200
    assert r2.json().get("cached") is True
    assert called["http"] == 1, "second call must hit the SQLite cache, not HTTP"


def test_narrate_unknown_company_404(scored):
    assert scored.post("/api/v1/companies/US:NOPE:US/narrate").status_code == 404


def test_narrate_sector_all(scored, monkeypatch):
    import app.services.llm as l

    monkeypatch.setattr(l, "OPENROUTER_API_KEY", "test-key-not-real")
    monkeypatch.setattr(l, "_chat", lambda model, facts, timeout=45.0: "Sector narration.")
    r = scored.post("/api/v1/sectors/Banks/narrate?currency=ALL")
    assert r.status_code == 200
    body = r.json()
    assert body["narration"] == "Sector narration."
    assert body["facts"]["companies"] > 0
    assert body["facts"]["currencies"] == ["CAD", "USD"]


# ---------- refresh job ----------

def test_refresh_job_202_and_409(scored):
    r1 = scored.post("/api/v1/jobs/refresh", json={"mode": "sample", "limit": 1})
    assert r1.status_code == 202
    assert r1.json()["kind"] == "refresh_universe"
    r2 = scored.post("/api/v1/jobs/refresh", json={"mode": "sample", "limit": 1})
    assert r2.status_code == 409


def test_refresh_job_runs_backfill_then_recompute(scored, monkeypatch):
    from app.models import Job

    recomputed = {"n": 0}

    def _fake_recompute(db, company_id=None):
        recomputed["n"] += 1

    monkeypatch.setattr("app.services.scoring_service.recompute", _fake_recompute)
    monkeypatch.setattr("app.services.job_worker.ingest_ticker", lambda db, t, r, refresh=False: None)

    # drain any active refresh jobs from earlier tests
    db = SessionLocal()
    db.query(Job).filter(Job.kind == "refresh_universe").update({"status": "cancelled"})
    db.commit()

    job = jobsvc.enqueue(db, "refresh_universe", {"mode": "sample", "limit": 1})
    db.close()

    worker = JobWorker()
    assert worker.process_one() is True

    db = SessionLocal()
    try:
        row = jobsvc.get_job(db, job.id)
        assert row.status == "succeeded"
        assert recomputed["n"] >= 1
    finally:
        db.close()


def test_no_secret_in_narrate_responses(scored, monkeypatch):
    import app.services.llm as l

    monkeypatch.setattr(l, "OPENROUTER_API_KEY", "sk-test-secret-12345")
    monkeypatch.setattr(l, "_chat", lambda model, facts, timeout=45.0: "Hello.")
    r = scored.post("/api/v1/companies/US:MMM:US/narrate")
    assert "sk-test-secret-12345" not in r.text
    failed = scored.post("/api/v1/sectors/Nope/narrate?currency=USD")
    assert failed.status_code in (404, 503)
    assert "sk-test-secret-12345" not in failed.text
