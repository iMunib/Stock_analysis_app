"""Tests for the Ingest State Machine, BABA currency handling, and peer widening.

Network-free: providers are mocked/stubbed. Tests verify the 202 + poll cycle,
state machine steps (resolve -> filings -> prices_shares -> sector_peers -> score -> done),
error catalog mappings, and foreign currency handling.
"""
from __future__ import annotations

import pytest
from app.db import SessionLocal
from app.models import Company, FinancialSnapshot, Job, Score
from app.providers.base import AnnualStatement, PriceQuote
from app.services import jobs as jobsvc
from app.services.job_worker import JobWorker
from app.services.mapping import resolve, MappingError
from app.services.scoring import build_peer_sets
from app.services.fundamentals import compute_snapshot_ratios


@pytest.fixture()
def clean_jobs():
    db = SessionLocal()
    try:
        db.query(Job).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_ticker_resolution_variants():
    # AMD
    r_amd = resolve("AMD")
    assert r_amd.company_id == "US:AMD:US"
    assert r_amd.ticker == "AMD"

    # AMD.US
    r_amd_us = resolve("AMD.US")
    assert r_amd_us.company_id == "US:AMD:US"

    # BABA
    r_baba = resolve("BABA")
    assert r_baba.company_id == "US:BABA:US"
    assert r_baba.ticker == "BABA"

    # KITS.TO
    r_kits = resolve("KITS.TO")
    assert r_kits.company_id == "CA:KITS:TSX"
    assert r_kits.country == "CA"
    assert r_kits.currency == "CAD"

    # CA:KITS:TSX
    r_kits_verbatim = resolve("CA:KITS:TSX")
    assert r_kits_verbatim.company_id == "CA:KITS:TSX"

    # 9988.HK (ambiguous listing early rejection)
    with pytest.raises(MappingError) as exc:
        resolve("9988.HK")
    assert "LISTING_AMBIGUOUS" in str(exc.value)


def test_ingest_endpoint_returns_202_and_polls(client, clean_jobs, monkeypatch):
    """POST /api/v1/tickers/ingest returns 202 immediately. Worker transitions through steps."""
    worker = JobWorker(poll_seconds=0.01)

    # Mock provider registry to avoid live network
    class FakeRegistry:
        def fetch_annual_statements(self, ref):
            return [
                AnnualStatement(
                    fiscal_year=2024,
                    period_end=None,
                    currency="USD",
                    source="mock_sec",
                    fields={"Revenue": 25_000_000_000.0, "Net_Income": 2_000_000_000.0, "Diluted_EPS": 1.25},
                )
            ]

        def fetch_price(self, ref):
            return PriceQuote(
                price=150.0,
                currency="USD",
                as_of=None,
                source="mock_yahoo",
                shares=1_600_000_000.0,
                market_cap=240_000_000_000.0,
                sector="Technology",
                industry="Semiconductors",
            )

    monkeypatch.setattr("app.providers.registry.ProviderRegistry", lambda: FakeRegistry())

    res = client.post("/api/v1/tickers/ingest", json={"ticker": "AMD"})
    assert res.status_code == 202
    data = res.json()
    job_id = data["job_id"]
    assert data["status"] == "queued"
    assert data["step"] == "queued"

    # Drive the worker
    did_run = worker.process_one()
    assert did_run is True

    poll = client.get(f"/api/v1/jobs/{job_id}")
    assert poll.status_code == 200
    pdata = poll.json()
    assert pdata["status"] == "succeeded"
    assert pdata["step"] == "done"
    assert pdata["company_id"] == "US:AMD:US"
    assert pdata["error_code"] == "SCORE_PARTIAL"
    assert "Saved, but some pillars missing" in pdata["message"]


def test_ambiguous_listing_rejected_at_endpoint(client):
    res = client.post("/api/v1/tickers/ingest", json={"ticker": "9988.HK"})
    assert res.status_code == 400
    assert "Multiple listings" in res.json()["detail"]


def test_cny_statement_with_usd_price_currency_mismatch():
    """BABA-class: statement currency CNY, trading price USD. Price ratios stay None."""
    company = Company(
        company_id="US:BABA:US",
        ticker="BABA",
        currency="USD",
        country="US",
        reporting_currency="CNY",
    )
    snap = FinancialSnapshot(
        company_id="US:BABA:US",
        fiscal_year=2024,
        currency="CNY",
        price=85.0,
        price_currency="USD",
        revenue=996_000_000_000.0,
        net_income=72_000_000_000.0,
        diluted_eps=29.0,  # In CNY
        book_equity=1_000_000_000_000.0,  # In CNY
        total_assets=1_800_000_000_000.0,  # In CNY
        shares_snapshot=2_500_000_000.0,
    )

    compute_snapshot_ratios(snap, company)

    # Statement ratios work (both in CNY)
    assert snap.roe_calc is not None
    assert abs(snap.roe_calc - 0.072) < 1e-4
    assert snap.roa_calc is not None
    assert abs(snap.roa_calc - 0.04) < 1e-4

    # Price ratios MUST stay None to prevent cross-border fake PE
    assert snap.pe_calc is None
    assert snap.pb_calc is None
    assert snap.ev_to_ebitda_calc is None


def test_peer_widening_prevents_one_of_one():
    """When a company is the only member in its custom sheet and sector, widen to currency universe."""
    universe = [
        {"company_id": "US:SOLO:US", "currency": "USD", "custom_industry_sheet": "RareIndustry", "gics_sector": "RareSector", "snapshot": {}},
        {"company_id": "US:PEER1:US", "currency": "USD", "custom_industry_sheet": "Tech", "gics_sector": "Tech", "snapshot": {}},
        {"company_id": "US:PEER2:US", "currency": "USD", "custom_industry_sheet": "Finance", "gics_sector": "Finance", "snapshot": {}},
    ]
    members, meta = build_peer_sets(universe)
    ptype, pn = meta["US:SOLO:US"]

    assert ptype == "broad_peer_set"
    assert pn == 3
    assert len(members["US:SOLO:US"]) == 3
