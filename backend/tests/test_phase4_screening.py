"""Comprehensive unit tests for Phase 4: Advanced Screening, ETF Cohorts & Peer Benchmarking."""
import pytest
from app.models import Company, FinancialSnapshot
from app.services.screener_engine import ensure_system_presets, run_screener_query
from app.services.etf_resolver import resolve_etf_constituents, get_etf_cohort_top5
from app.services.peer_engine import compute_peer_comparison_matrix


def test_screener_institutional_presets_registered(imported_db):
    """Test that all certified literature presets and institutional presets are registered and seeded."""
    presets = ensure_system_presets(imported_db)
    preset_ids = {p.id for p in presets}
    required_presets = {
        # Institutional presets:
        "buffett_munger_quality_compounders",
        "graham_deep_value_net_nets",
        "cannibal_capital_compounders",
        "dorsey_wide_moat_franchises",
        "forensic_red_flag_warning",
        # Certified Literature Presets (Task 4.1):
        "greenblatt_magic_formula",
        "graham_net_net_bargains",
        "peter_lynch_growth_compounders",
        "piotroski_high_quality_turnarounds",
        "true_shareholder_yield_leaders",
        "aaoifi_halal_candidates",
    }
    assert required_presets <= preset_ids


def test_screener_literature_preset_query(imported_db):
    """Test executing screener queries with literature presets."""
    res_tsy = run_screener_query(imported_db, {"preset": "true_shareholder_yield_leaders"}, limit=10)
    assert "items" in res_tsy
    assert isinstance(res_tsy["items"], list)

    res_greenblatt = run_screener_query(imported_db, {"preset": "greenblatt_magic_formula"}, limit=10)
    assert "items" in res_greenblatt
    assert isinstance(res_greenblatt["items"], list)


def test_screen_endpoint_literature_preset(client):
    """Test /api/v1/screen endpoint with preset filter."""
    resp = client.get("/api/v1/screen?preset=aaoifi_halal_candidates")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    for it in data["items"]:
        assert it.get("halal_status") == "halal_candidate"


def test_etf_constituent_resolution_known_and_unknown():
    """Test resolving ETF constituents with graceful fallback and empty list on unknown."""
    spus = resolve_etf_constituents("SPUS")
    assert isinstance(spus, list)

    unknown = resolve_etf_constituents("UNKNOWN_BASKET_XYZ")
    assert isinstance(unknown, list)
    assert len(unknown) == 0


def test_peer_comparison_matrix_four_pillars(imported_db):
    """Test 4-pillar peer comparison matrix calculation and strict currency isolation."""
    matrix_us = compute_peer_comparison_matrix(imported_db, "US:MSFT:US")
    assert matrix_us["company_id"] == "US:MSFT:US"
    assert "USD" in matrix_us["peer_group"]
    assert "valuation" in matrix_us["pillars"]
    assert "quality" in matrix_us["pillars"]
    assert "financial_health" in matrix_us["pillars"]
    assert "capital_allocation" in matrix_us["pillars"]

    matrix_ca = compute_peer_comparison_matrix(imported_db, "CA:RY:TSX")
    assert matrix_ca["company_id"] == "CA:RY:TSX"
    assert "CAD" in matrix_ca["peer_group"]
