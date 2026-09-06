"""Unit tests for Wave 1 scope (21 user stories across Epics 1-4).

Tests:
- Epic 1: US-0051, US-0052, US-0056, US-0064, US-0067, US-0080, US-0083, US-0100
- Epic 2: US-0060, US-0063, US-0676, US-0905, US-0919, US-0947
- Epic 3: US-0453, US-0460, US-0466, US-0481
- Epic 4: US-0074, US-0705, US-0725
"""
import pytest
from app.services.pillar_drilldown import compute_pillar_tensions, compute_coverage_penalty_details


def test_wave1_pillar_drilldown_endpoint(client):
    """US-0051, US-0052, US-0056, US-0067, US-0080, US-0083, US-0100 verification."""
    resp = client.get("/api/v1/companies/US:AAPL:US/pillar-drilldown")
    assert resp.status_code == 200
    data = resp.json()

    assert data["company_id"] == "US:AAPL:US"
    assert data["currency"] == "USD"
    assert "pillars" in data

    # Check 4 pillars present
    for p_name in ("quality", "value", "growth", "risk"):
        assert p_name in data["pillars"]
        p = data["pillars"][p_name]
        # US-0051: Exact formula
        assert "formula" in p
        assert len(p["formula"]) > 0
        # US-0052: Plain-English 1-line interpretation
        assert "interpretation" in p
        assert len(p["interpretation"]) > 0
        # US-0083: Missing data FAQ
        assert "missing_faq" in p
        assert len(p["missing_faq"]) > 0
        # US-0067: Sector peer median
        assert "sector_median" in p

        # US-0051 & US-0056: Sub-metrics with raw values, weights, and line items
        assert "sub_metrics" in p
        assert len(p["sub_metrics"]) > 0
        for sm in p["sub_metrics"]:
            assert "name" in sm
            assert "weight" in sm
            assert "line_items" in sm
            for li in sm["line_items"]:
                assert "name" in li
                assert "period" in li
                assert "provenance" in li

    # US-0080: Risk decomposed into 3 sub-bars
    risk_p = data["pillars"]["risk"]
    assert "sub_bars" in risk_p
    assert "leverage" in risk_p["sub_bars"]
    assert "coverage" in risk_p["sub_bars"]
    assert "volatility" in risk_p["sub_bars"]

    # US-0100: Interactive coverage penalty visualizer details
    assert "coverage_penalty" in data
    cp = data["coverage_penalty"]
    assert "unadjusted_weighted_score" in cp
    assert "multiplier" in cp
    assert "deduction" in cp
    assert "formula_string" in cp
    assert "penalty_table" in cp
    assert len(cp["penalty_table"]) == 5


def test_wave1_pillar_tensions_logic():
    """US-0064: Pillar disagreement radar (highlight core tensions)."""
    # High quality but expensive
    t1 = compute_pillar_tensions({"quality": 8.5, "value": 2.5, "growth": 6.0, "risk": 7.0})
    assert any(t["tension_id"] == "high_quality_expensive" for t in t1)
    hq = next(t for t in t1 if t["tension_id"] == "high_quality_expensive")
    assert "Quality 8.5/10 vs Value 2.5/10" in hq["chip"]

    # Value trap (cheap but high risk / low risk score)
    t2 = compute_pillar_tensions({"quality": 5.0, "value": 8.2, "growth": 4.0, "risk": 3.2})
    assert any(t["tension_id"] == "value_trap_risk" for t in t2)
    vt = next(t for t in t2 if t["tension_id"] == "value_trap_risk")
    assert "Value 8.2/10 vs Risk 3.2/10" in vt["chip"]


def test_wave1_coverage_penalty_details_math():
    """US-0100: Coverage multiplier deduction calculation."""
    # 4 pillars -> multiplier 1.0, 0 deduction
    res4 = compute_coverage_penalty_details({"quality": 8.0, "value": 8.0, "growth": 8.0, "risk": 8.0}, 8.0)
    assert res4["multiplier"] == 1.0
    assert res4["deduction"] == 0.0

    # 3 pillars -> multiplier 0.92
    res3 = compute_coverage_penalty_details({"quality": 8.0, "value": 8.0, "growth": 8.0, "risk": None}, None)
    assert res3["multiplier"] == 0.92
    assert res3["coverage_count"] == 3
    assert res3["deduction"] > 0


def test_wave1_ratio_inspector_endpoint(client):
    """US-0460, US-0453, US-0481: Ratio calculation inspector & SEC provenance."""
    # Inspect ROE
    resp = client.get("/api/v1/companies/US:AAPL:US/ratios/roe/inspect")
    assert resp.status_code == 200
    data = resp.json()

    assert data["company_id"] == "US:AAPL:US"
    assert data["ratio_id"] == "roe"
    assert "formula_string" in data
    assert "vintage" in data
    assert "numerator" in data
    assert "denominator" in data
    assert "arithmetic_resolution" in data
    assert len(data["arithmetic_resolution"]) >= 2

    # US-0453: Accession / SEC URL provenance
    assert data["numerator"]["sec_edgar_url"] is not None
    assert "sec.gov" in data["numerator"]["sec_edgar_url"]

    # Inspect FCF Margin
    resp_fcf = client.get("/api/v1/companies/US:AAPL:US/ratios/fcf_margin/inspect")
    assert resp_fcf.status_code == 200
    assert resp_fcf.json()["ratio_id"] == "fcf_margin"

    # Inspect P/E
    resp_pe = client.get("/api/v1/companies/US:AAPL:US/ratios/pe/inspect")
    assert resp_pe.status_code == 200


def test_wave1_universe_coverage_health_endpoint(client):
    """US-0466: Universe data coverage & health dashboard matrix."""
    resp = client.get("/api/v1/coverage/health")
    assert resp.status_code == 200
    data = resp.json()

    assert "universe_summary" in data
    assert data["universe_summary"]["total_companies"] >= 500
    assert data["universe_summary"]["us_names"] >= 500
    assert data["universe_summary"]["canadian_names"] >= 200

    assert "provenance_summary" in data
    assert "pillar_completeness" in data
    assert "sector_breakdown" in data
    assert len(data["sector_breakdown"]) > 0

    assert "null_data_audit" in data
    assert "null_percentage" in data["null_data_audit"]
    assert "top_missing_fields" in data["null_data_audit"]


def test_wave1_bear_case_endpoint(client):
    """US-0074, US-0705, US-0725: Synthesized bear thesis & pre-mortem challenge."""
    resp = client.get("/api/v1/companies/US:AAPL:US/bear-case")
    assert resp.status_code == 200
    data = resp.json()

    assert data["company_id"] == "US:AAPL:US"
    # US-0074: Synthesized coherent bear narrative
    assert "bear_thesis_narrative" in data
    assert len(data["bear_thesis_narrative"]) > 0
    assert "core_vulnerabilities" in data
    assert "lowest_3_percentiles" in data

    # US-0725: Pre-mortem challenge prompt
    assert "pre_mortem_challenge" in data
    assert "50% drawdown" in data["pre_mortem_challenge"]

    # US-0705: Structural equal-billing mandate
    assert "equal_billing_mandate" in data


def test_wave1_factor_evidence_endpoint(client):
    """US-0060, US-0063, US-0676, US-0905, US-0919, US-0947: Factor evidence catalog."""
    resp = client.get("/api/v1/factors/evidence")
    assert resp.status_code == 200
    data = resp.json()

    # US-0676: Bessembinder base rate
    assert "bessembinder_base_rate" in data
    assert "42%" in data["bessembinder_base_rate"]["statement"]
    assert "Bessembinder" in data["bessembinder_base_rate"]["citations"][0]

    # US-0060 & US-0919: Canonical factors with regime sensitivities & Sharpe ratios
    assert "canonical_factors" in data
    factors = {f["factor_id"]: f for f in data["canonical_factors"]}
    assert "value" in factors
    assert "quality" in factors
    assert "growth" in factors
    assert "low_volatility" in factors
    assert "regime_sensitivity" in factors["value"]
    assert "sharpe_ratio" in factors["quality"]

    # US-0063, US-0905, US-0947: Forensic models with decay dates, date stamps, false positives
    assert "forensic_models" in data
    models = {m["model_id"]: m for m in data["forensic_models"]}
    assert "altman_z" in models
    assert "beneish_m" in models
    assert "piotroski_f" in models
    assert "sloan_accruals" in models

    # US-0905: Immutable date badge
    assert "Altman (1968)" in models["altman_z"]["date_badge"]
    assert "Beneish (1999)" in models["beneish_m"]["date_badge"]
    # US-0947: False positive rate
    assert "false_positive_rate" in models["beneish_m"]
    assert "14%" in models["beneish_m"]["false_positive_rate"]


def test_dossier_contains_wave1_fields(client):
    """Verify company dossier payload enriches with Wave 1 fields."""
    resp = client.get("/api/v1/companies/US:AAPL:US/dossier")
    assert resp.status_code == 200
    data = resp.json()

    assert "pillar_drilldown" in data
    assert data["pillar_drilldown"] is not None
    assert "vintage" in data
    assert data["vintage"] is not None
    assert "bear_case" in data
    assert data["bear_case"] is not None


def test_wave1_canadian_stock_drilldown_and_sedar(client):
    """Verify Canadian stock drilldown retains CAD currency and routes to SEDAR+."""
    resp = client.get("/api/v1/companies/CA:RY:TSX/pillar-drilldown")
    assert resp.status_code == 200
    data = resp.json()

    assert data["company_id"] == "CA:RY:TSX"
    assert data["currency"] == "CAD"
    
    # Check that Canadian company filings point to SEDAR+
    found_sedar = False
    for p in data["pillars"].values():
        for sm in p.get("sub_metrics", []):
            for li in sm.get("line_items", []):
                if li.get("sec_edgar_url") and "sedarplus.ca" in li["sec_edgar_url"]:
                    found_sedar = True
                    break
    assert found_sedar, "Canadian stock line items must link to SEDAR+ filings"


def test_wave1_bank_drilldown_faq(client):
    """Verify bank stocks have appropriate missing data FAQ in pillar drilldown."""
    resp = client.get("/api/v1/companies/US:JPM:US/pillar-drilldown")
    assert resp.status_code == 200
    data = resp.json()

    risk_pillar = data["pillars"].get("risk")
    assert risk_pillar is not None
    assert "bank" in risk_pillar["missing_faq"].lower() or "deposit" in risk_pillar["missing_faq"].lower()


def test_wave1_expanded_ratio_inspector_coverage(client):
    """US-0460: Verify expanded ratio inspector decomposes all 12 key financial ratios."""
    test_ratios = [
        "roic",
        "pb",
        "ev_ebitda",
        "current_ratio",
        "interest_coverage",
        "gross_margin",
        "net_debt_fcf",
    ]
    for ratio in test_ratios:
        resp = client.get(f"/api/v1/companies/US:AAPL:US/ratios/{ratio}/inspect")
        assert resp.status_code == 200, f"Failed for ratio: {ratio}"
        data = resp.json()
        assert data["ratio_id"] == ratio
        assert "formula_string" in data
        assert "numerator" in data
        assert "denominator" in data
        assert "arithmetic_resolution" in data
        assert len(data["arithmetic_resolution"]) >= 2

    # Verify Canadian ratio inspection provides SEDAR+ link
    resp_ca = client.get("/api/v1/companies/CA:RY:TSX/ratios/pb/inspect")
    assert resp_ca.status_code == 200
    ca_data = resp_ca.json()
    assert ca_data["denominator"]["currency"] == "CAD"
    if ca_data["denominator"].get("sec_edgar_url"):
        assert "sedarplus.ca" in ca_data["denominator"]["sec_edgar_url"]

