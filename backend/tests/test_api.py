"""API contract tests (Phase 1 surface only)."""
from __future__ import annotations


def test_health_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200


def test_disclaimer_non_empty(client):
    resp = client.get("/api/v1/meta/disclaimer")
    assert resp.status_code == 200
    body = resp.json()
    assert body["disclaimer"].strip()
    assert "not investment advice" in body["disclaimer"].lower()


def test_companies_list_shape(client):
    resp = client.get("/api/v1/companies?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 720
    assert len(body["items"]) == 5
    item = body["items"][0]
    assert item["company_id"]
    assert item["currency"] in ("USD", "CAD")


def test_companies_filters(client):
    r = client.get("/api/v1/companies?country=CA&limit=500")
    body = r.json()
    assert body["total"] == 220
    assert all(i["country"] == "CA" for i in body["items"])

    r = client.get("/api/v1/companies?q=royal")
    body = r.json()
    assert body["total"] >= 1
    assert any("Royal" in (i["name"] or "") for i in body["items"])

    r = client.get("/api/v1/companies?sector=Financials&limit=1")
    assert r.status_code == 200


def test_company_detail_404_and_found(client):
    r = client.get("/api/v1/companies/US:NOPE:US")
    assert r.status_code == 404

    r = client.get("/api/v1/companies/US:MMM:US")
    assert r.status_code == 200
    body = r.json()
    assert body["company_id"] == "US:MMM:US"
    assert body["latest_snapshot"] is not None
    assert body["latest_snapshot"]["revenue"] == 24_948_000_000.0


def test_sectors_counts(client):
    r = client.get("/api/v1/sectors")
    assert r.status_code == 200
    body = r.json()
    custom_total = sum(s["count"] for s in body["custom_industries"])
    gics_total = sum(s["count"] for s in body["gics_sectors"])
    assert custom_total == 720
    assert gics_total == 720
    # Consolidated from 30 fragmented sheets to ~18 cohesive groups (WS7: 86→~40)
    assert 15 <= len(body["custom_industries"]) <= 40
    # Every consolidated group must have at least 8 members for robust percentiles
    assert all(s["count"] >= 8 for s in body["custom_industries"]), "All consolidated groups must have ≥8 members"


def test_stats_companies_720(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["companies"] == 720
    assert body["by_currency"] == {"USD": 500, "CAD": 220}
    assert body["financial_snapshots"] == 720
    assert body["placements"] > 720
    assert body["last_import"]["source_filename"] == "Sector_Financials_Final_Owner.xlsx"
    assert body["coverage"]["Revenue"] > 0


def test_no_scoring_endpoints(client):
    r = client.get("/api/v1/scores")
    assert r.status_code == 404
    r = client.get("/api/v1/scoring")
    assert r.status_code == 404


def test_company_statements_3nf(client):
    r = client.get("/api/v1/companies/US:MMM:US/statements")
    assert r.status_code == 200
    body = r.json()
    assert body["company_id"] == "US:MMM:US"
    assert body["count"] >= 1
    assert "revenue" in body["items"][0]
    assert body["items"][0]["revenue"] == 24_948_000_000.0


def test_company_derived_metrics_3nf(client):
    r = client.get("/api/v1/companies/US:MMM:US/derived-metrics")
    assert r.status_code == 200
    body = r.json()
    assert body["company_id"] == "US:MMM:US"
    assert body["count"] >= 1
    assert "pe_calc" in body["items"][0]

