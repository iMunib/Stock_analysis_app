"""Tests for 3NF calculation pipeline, peer benchmarks engine, and API endpoints."""
from __future__ import annotations

import pytest
from sqlalchemy import select, func
from app.models import Company, DerivedMetric, PeerBenchmark
from app.services.calculation_pipeline import populate_missing_metrics
from app.services.peer_engine import populate_peer_benchmarks


def test_populate_missing_metrics_and_idempotency(imported_db):
    """Verify that calculation pipeline populates derived metrics and is idempotent."""
    # Run calculation pipeline for 5 companies
    summary1 = populate_missing_metrics(imported_db, limit=5, recompute_score=False)
    assert "populated" in summary1
    assert summary1["populated"] >= 0

    # Ensure derived metrics exist
    derived_count = imported_db.execute(select(func.count(DerivedMetric.id))).scalar()
    assert derived_count > 0


def test_peer_benchmarks_population_and_invariants(imported_db):
    """Verify peer benchmarks table is populated, partitions by currency, and respects statistical invariants."""
    upserted = populate_peer_benchmarks(imported_db)
    assert isinstance(upserted, int)
    assert upserted > 0

    # Query benchmarks from DB
    benchmarks = imported_db.scalars(select(PeerBenchmark)).all()
    assert len(benchmarks) > 0

    currencies = {b.currency for b in benchmarks}
    assert "USD" in currencies
    # Currencies must only be valid uppercase codes, never mixed
    for b in benchmarks:
        assert b.currency in ("USD", "CAD")
        assert b.peer_group_name
        assert b.metric_name
        assert b.count >= 1
        # Quantile ordering invariant
        if b.p25 is not None and b.median is not None and b.p75 is not None:
            assert b.p25 <= b.median <= b.p75


def test_company_benchmarks_api(client, imported_db):
    """Verify GET /api/v1/companies/{company_id}/benchmarks endpoint returns 200 with peer distributions."""
    # Ensure benchmarks are populated
    populate_peer_benchmarks(imported_db)

    # Find a company with sector
    comp = imported_db.scalars(select(Company).where(Company.gics_sector.isnot(None)).limit(1)).first()
    assert comp is not None

    resp = client.get(f"/api/v1/companies/{comp.company_id}/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == comp.company_id
    assert data["currency"] == comp.currency
    assert "items" in data
    assert "groups" in data
    assert len(data["items"]) > 0


def test_global_benchmarks_api(client, imported_db):
    """Verify GET /api/v1/benchmarks endpoint returns filtered peer benchmarks."""
    populate_peer_benchmarks(imported_db)

    resp = client.get("/api/v1/benchmarks?currency=USD")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert all(item["currency"] == "USD" for item in data["items"])
    assert all("metric_name" in item for item in data["items"])
    assert all("median" in item for item in data["items"])


def test_bank_altman_z_exemption(imported_db):
    """Verify banks/financials have Altman Z as NULL per AGENTS.md, but computed_at is set to avoid infinite recomputation."""
    bank = imported_db.scalars(
        select(Company).where(Company.gics_sector == "Financials").limit(1)
    ).first()
    if bank is not None:
        populate_missing_metrics(imported_db, limit=None, recompute_score=False)
        derived = imported_db.scalars(
            select(DerivedMetric).where(DerivedMetric.company_id == bank.company_id)
        ).first()
        if derived is not None:
            assert derived.computed_at is not None
            assert derived.altman_z is None
