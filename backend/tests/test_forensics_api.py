"""Tests for Forensics, Valuation, Soft-deletion, and Screener Presets."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client(imported_db):
    # imported_db ensures the database is initialized and imported
    return TestClient(app)


def test_forensics_and_valuation_endpoints(client):
    cid = "US:AAPL:US"

    # 1. Test Forensics endpoint
    resp = client.get(f"/api/v1/companies/{cid}/forensics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == cid
    assert data["currency"] == "USD"
    assert data["sloan_signal"] in ("green", "red", "neutral", "insufficient_data")
    assert data["cash_conversion_signal"] in ("healthy", "weak", "insufficient_data")
    assert "fcf_vs_ni_history" in data

    # 2. Test Valuation endpoint
    resp_val = client.get(f"/api/v1/companies/{cid}/valuation")
    assert resp_val.status_code == 200
    val_data = resp_val.json()
    assert val_data["company_id"] == cid
    assert val_data["status"] in ("converged", "dcf_unviable_negative_fcf")
    assert val_data["wacc"] == 0.09
    assert val_data["terminal_growth_rate"] == 0.025

    # 3. Test Deletion endpoint (soft-delete)
    resp_del = client.delete(f"/api/v1/companies/{cid}")
    assert resp_del.status_code == 200
    assert resp_del.json()["ok"] is True

    # Search should exclude it
    resp_search = client.get("/api/v1/search?q=AAPL")
    assert resp_search.status_code == 200
    assert not any(item["company_id"] == cid for item in resp_search.json()["items"])

    # 4. Test Restore endpoint
    resp_res = client.post(f"/api/v1/companies/{cid}/restore")
    assert resp_res.status_code == 200
    assert resp_res.json()["ok"] is True

    # Search should now find it again
    resp_search2 = client.get("/api/v1/search?q=AAPL")
    assert resp_search2.status_code == 200
    assert any(item["company_id"] == cid for item in resp_search2.json()["items"])


def test_screener_presets_and_run(client):
    # Presets
    resp_presets = client.get("/api/v1/screener/presets")
    assert resp_presets.status_code == 200
    presets = resp_presets.json()
    assert len(presets) >= 3
    preset_ids = [p["id"] for p in presets]
    assert "buffett_burry_deep_value" in preset_ids
    assert "forensic_red_flags" in preset_ids

    # Screener run
    resp_run = client.post(
        "/api/v1/screener/run",
        json={"currency": "USD", "limit": 10, "offset": 0},
    )
    assert resp_run.status_code == 200
    res = resp_run.json()
    assert "items" in res
    assert "count" in res
