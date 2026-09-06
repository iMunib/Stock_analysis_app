"""Wave 7 Canada tests (Epic 15: 36 stories)."""
from __future__ import annotations


def test_canadian_tax_placement_guide(client):
    r = client.get("/api/v1/canada/companies/CA:RY:TSX/tax-placement")
    assert r.status_code == 200
    data = r.json()
    assert "guides" in data
    assert "TFSA" in data["guides"]
    assert "RRSP" in data["guides"]
    assert "FHSA" in data["guides"]
    # Check withholding notes
    assert "15%" in data["guides"]["TFSA"]["withholding"]
    assert "0%" in data["guides"]["RRSP"]["withholding"] or "exempt" in data["guides"]["RRSP"]["withholding"].lower()
    assert "disclaimer" in data


def test_canadian_metrics_reit_and_prefs(client):
    r = client.get("/api/v1/canada/companies/CA:RY:TSX/canadian-metrics")
    assert r.status_code == 200
    data = r.json()
    assert "currency" in data
    # CAD company should have CAD currency
    assert data["currency"] == "CAD"
    # REIT flag may be false for banks, but structure should exist
    assert "is_reit" in data


def test_dual_listed_identity(client):
    r = client.get("/api/v1/canada/companies/CA:RY:TSX/dual-listed")
    assert r.status_code == 200
    data = r.json()
    assert data["is_dual_listed"] is True
    assert data["cad_ticker"] == "RY.TO"
    # Single-listed should be false
    r2 = client.get("/api/v1/canada/companies/US:AAPL:US/dual-listed")
    assert r2.status_code == 200
    assert r2.json()["is_dual_listed"] is False


def test_txs_industry_medians_pure_cad(client):
    # Use an industry that exists for CAD
    r = client.get("/api/v1/canada/industry/Banks/medians?currency=CAD")
    assert r.status_code == 200
    data = r.json()
    assert data["currency"] == "CAD"
    assert "median_composite" in data
    # CAD purity enforcement
    r2 = client.get("/api/v1/canada/industry/Banks/medians?currency=USD")
    assert r2.status_code == 400
