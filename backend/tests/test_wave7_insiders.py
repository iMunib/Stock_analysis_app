"""Wave 7 Insider tests (Epic 16: 7 stories)."""
from __future__ import annotations


def test_form4_insiders_and_cluster(client):
    r = client.get("/api/v1/companies/US:AAPL:US/insiders")
    assert r.status_code == 200
    data = r.json()
    assert "filings" in data
    assert "cluster" in data
    # AAPL synthetic cluster should be true
    assert data["cluster"]["cluster_buy"] is True
    assert data["cluster"]["distinct_buyers"] >= 3
    # Check 10b5-1 tagging
    filings = data["filings"]
    assert any(f["is_10b5_1"] for f in filings) or any(f["opportunistic_tag"] == "10b5-1 pre-planned" for f in filings)
    # Check lag days
    assert any("lag_days" in f for f in filings)
    # Disclaimer
    assert "disclaimer" in data
    # CAD should have no filings but still succeed
    r2 = client.get("/api/v1/companies/CA:RY:TSX/insiders")
    assert r2.status_code == 200
    assert r2.json()["filings"] == []


def test_cluster_endpoint(client):
    r = client.get("/api/v1/insiders/cluster?ids=US:AAPL:US,CA:RY:TSX")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    # AAPL should be first (cluster true) due to sorting
    assert data["items"][0]["company_id"] == "US:AAPL:US"
    assert data["items"][0]["cluster"]["cluster_buy"] is True


def test_pure_mode_persists(client):
    r = client.get("/api/v1/companies/US:AAPL:US/insiders?pure_mode=true")
    assert r.status_code == 200
    assert r.json()["pure_mode"] is True
