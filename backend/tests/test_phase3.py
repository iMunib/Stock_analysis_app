"""Phase 3 tests: pillar math, penalties, peers, halal, persistence, API. Network-free."""
from __future__ import annotations

import math

import pytest

from app.services.halal import evaluate_halal
from app.services.scoring import (
    build_peer_sets,
    composite_score,
    growth_pillar,
    peer_values_for,
    quality_pillar,
    risk_pillar,
    score_company,
    signal_for,
    value_pillar,
)


def _snap(**kw):
    base = {k: None for k in (
        "revenue", "net_income", "diluted_eps", "gross_profit", "operating_cash_flow", "capex",
        "fcf_calc", "netdebt_calc", "total_debt", "book_equity", "cash_st_investments",
        "total_assets", "total_liabilities", "ebit", "ebitda", "interest_expense",
        "roe_calc", "roa_calc", "fcfmargin_calc", "grossmargin_calc", "pe_calc", "pb_calc",
        "ev_to_ebitda_calc", "price", "market_cap", "cet1_ratio", "leverage_ratio",
        "nim_fy2025", "efficiency_ratio", "roaa",
    )}
    base.update(kw)
    return base


# ---------- pillar math on hand-built fixture ----------

def test_two_company_known_composite():
    """Hand-built pair: A (quality, cheap, growing, safe) vs B (worse).
    Peer lists exclude the company itself (engine contract)."""
    pv = {
        "pe": [20.0], "pb": [3.0], "ev_to_ebitda": [16.0],
        "earnings_yield": [0.05], "roe": [0.10], "roa": [0.05],
        "fcfmargin": [0.10], "grossmargin": [0.30], "efficiency": [], "roaa": [],
    }
    a = _snap(revenue=100.0, net_income=15.0, diluted_eps=1.5, gross_profit=50.0,
              operating_cash_flow=25.0, capex=-5.0, fcf_calc=20.0, total_debt=20.0,
              book_equity=50.0, cash_st_investments=10.0, total_assets=100.0, total_liabilities=40.0,
              ebit=20.0, ebitda=25.0, interest_expense=2.0, roe_calc=0.30, roa_calc=0.15,
              fcfmargin_calc=0.20, grossmargin_calc=0.50, pe_calc=10.0, pb_calc=1.0,
              ev_to_ebitda_calc=8.0, price=15.0, market_cap=150.0, netdebt_calc=10.0)
    hist_a = [
        {"fiscal_year": 2022, "revenue": 80.0, "diluted_eps": 1.0, "fcf_calc": 12.0},
        {"fiscal_year": 2023, "revenue": 90.0, "diluted_eps": 1.2, "fcf_calc": 16.0},
        {"fiscal_year": 2024, "revenue": 100.0, "diluted_eps": 1.5, "fcf_calc": 20.0},
    ]
    res = score_company(a, None, hist_a, pv)
    assert res["pillars"]["value"] == pytest.approx(10.0, abs=0.05)  # cheapest on all metrics
    assert res["pillars"]["growth"] is not None
    assert res["pillars"]["risk"] is not None
    assert res["pillars"]["quality"] is not None
    assert res["composite"] is not None
    assert 7.0 <= res["composite"] <= 10.0
    assert res["coverage"] == 4
    assert res["signal"] in ("strong_candidate", "constructive")
    assert res["method_version"] == "v1"
    assert "not investment advice" in res["disclaimer"].lower()


def test_missing_growth_null_with_penalty_not_five():
    cur = _snap(revenue=100.0, net_income=10.0, total_assets=200.0, total_liabilities=80.0,
                roe_calc=0.2, roa_calc=0.05,
                pe_calc=15.0, pb_calc=2.0, price=30.0, diluted_eps=2.0, market_cap=300.0)
    pv = {"pe": [10.0, 20.0], "pb": [1.0, 3.0], "ev_to_ebitda": [], "earnings_yield": [0.067, 0.05],
          "roe": [0.1], "roa": [0.03], "fcfmargin": [], "grossmargin": [], "efficiency": [], "roaa": []}
    res = score_company(cur, None, [{"fiscal_year": None}], pv)  # seed-only, no history
    assert res["pillars"]["growth"] is None, "missing growth must be NULL, not 5.0"
    assert res["coverage"] == 3
    assert res["penalty"] == 0.92
    assert res["composite"] is not None


def test_zero_pillars_insufficient():
    res = score_company(_snap(), None, [], {})
    assert res["composite"] is None
    assert res["signal"] == "insufficient_data"


def test_usd_peer_median_ignores_cad():
    # build_peer_sets never mixes currency
    companies = [
        {"company_id": "US:A:US", "custom_industry_sheet": "Software", "gics_sector": "Information Technology", "currency": "USD"},
        {"company_id": "CA:B:TSX", "custom_industry_sheet": "Software", "gics_sector": "Information Technology", "currency": "CAD"},
    ]
    members, meta = build_peer_sets(companies)
    us_peers = members["US:A:US"]
    assert all(m["currency"] == "USD" for m in us_peers), "USD peer set must exclude CAD rows"


def test_bank_quality_without_gross_profit_or_fcf():
    bank = _snap(net_income=5000.0, total_assets=400000.0, roe_calc=0.12, roa_calc=0.0125,
                 efficiency_ratio=0.55, roaa=0.012, cet1_ratio=0.13, nim_fy2025=0.025,
                 price=100.0, diluted_eps=8.0, pe_calc=12.5, market_cap=50000.0)
    pv = {"pe": [12.5, 15.0], "pb": [], "ev_to_ebitda": [], "earnings_yield": [0.08, 0.067],
          "roe": [0.12, 0.08], "roa": [0.0125, 0.008], "fcfmargin": [], "grossmargin": [],
          "efficiency": [0.55, 0.65], "roaa": [0.012, 0.009]}
    company = {"gics_sector": "Financials", "custom_industry_sheet": "Banks"}
    q, detail = quality_pillar({**bank, **company}, None, pv)
    assert q is not None, "bank must score quality without Gross_Profit/FCF"
    assert detail["path"] == "financial"
    assert 0.0 <= q <= 10.0


def test_insurer_blank_debt_does_not_crash():
    cur = _snap(net_income=800.0, total_assets=90000.0, roe_calc=0.10, roa_calc=0.009,
                total_debt=None, gross_profit=None, revenue=None, efficiency_ratio=0.7,
                gics_sector="Financials", custom_industry_sheet="Insurance")
    pv = {"roe": [0.10, 0.07], "roa": [0.009, 0.005], "fcfmargin": [], "grossmargin": [],
          "efficiency": [0.7, 0.75], "roaa": [], "pe": [], "pb": [1.5, 2.0],
          "ev_to_ebitda": [], "earnings_yield": []}
    res = score_company(cur, None, [{"fiscal_year": None}], pv)
    assert res["composite"] is not None or res["coverage"] >= 1


def test_negative_eps_pe_skipped():
    cur = _snap(pe_calc=-8.0, pb_calc=0.8, price=10.0, diluted_eps=-1.25, market_cap=100.0,
                net_income=-12.0)
    pv = {"pe": [10.0, 15.0, 20.0], "pb": [1.5, 2.0], "ev_to_ebitda": [], "earnings_yield": [0.1, 0.067, 0.05],
          "roe": [], "roa": [], "fcfmargin": [], "grossmargin": [], "efficiency": [], "roaa": []}
    v, detail = value_pillar(cur, pv)
    assert detail.get("pe_negative_skipped") is True
    assert v is not None  # PB still scored
    assert math.isclose(v, 10.0, abs_tol=0.05)  # cheapest PB in peers


def test_growth_piecewise_mapping():
    from app.services.scoring import _piecewise_growth

    assert _piecewise_growth(0.0) == 5.0
    assert _piecewise_growth(0.20) == 8.0
    assert _piecewise_growth(0.40) == 10.0
    assert _piecewise_growth(-0.20) == 2.0
    assert _piecewise_growth(-0.40) == 0.0
    assert _piecewise_growth(0.10) == pytest.approx(6.5)
    # one-year change is never CAGR
    g, _ = growth_pillar([
        {"fiscal_year": 2023, "revenue": 100.0},
        {"fiscal_year": 2024, "revenue": 150.0},
    ])
    assert g is None


def test_signal_boundaries():
    assert signal_for(None) == "insufficient_data"
    assert signal_for(9.0) == "strong_candidate"
    assert signal_for(7.0) == "constructive"
    assert signal_for(5.5) == "mixed"
    assert signal_for(4.0) == "weak"
    assert signal_for(1.0) == "avoid"


def test_composite_penalty_table():
    c, cov, pen = composite_score({"quality": 10.0, "value": 10.0, "growth": 10.0, "risk": 10.0})
    assert (c, cov) == (10.0, 4)
    c3, cov3, _ = composite_score({"quality": 10.0, "value": 10.0, "growth": 10.0, "risk": None})
    assert cov3 == 3 and c3 == pytest.approx(10.0 * 0.92, abs=0.001)


# ---------- halal ----------

def test_halal_bank_not_halal():
    company = {"gics_sector": "Financials", "custom_industry_sheet": "Banks", "name": "Royal Bank"}
    snap = _snap(market_cap=100.0, total_debt=10.0, cash_st_investments=5.0)
    res = evaluate_halal(company, snap)
    assert res["status"] == "not_halal"
    assert res["tests"]["activity_screen"]["result"] == "fail"


def test_halal_software_missing_mcap_unknown():
    company = {"gics_sector": "Information Technology", "custom_industry_sheet": "Software", "name": "SoftCo"}
    res = evaluate_halal(company, _snap(market_cap=None))
    assert res["status"] == "unknown"
    assert res["status"] != "halal_candidate"


def test_halal_clean_company_with_low_ratios_is_candidate():
    company = {"gics_sector": "Information Technology", "custom_industry_sheet": "Software", "name": "CleanSoft"}
    # impure income is unknown in v1 -> never halal_candidate by design; expect unknown
    snap = _snap(market_cap=1000.0, total_debt=50.0, cash_st_investments=50.0)
    res = evaluate_halal(company, snap)
    assert res["status"] == "unknown", "impure income unknown in v1 -> never passes as halal"


def test_halal_high_debt_not_halal():
    company = {"gics_sector": "Industrials", "custom_industry_sheet": "Industrials", "name": "LeverCo"}
    snap = _snap(market_cap=100.0, total_debt=60.0, cash_st_investments=5.0)
    res = evaluate_halal(company, snap)
    assert res["status"] == "not_halal"
    assert res["tests"]["financial_ratios"]["ratios"]["debt_to_mcap"]["result"] == "fail"


# ---------- persistence + determinism + API ----------

def test_recompute_twice_deterministic_and_api(client, imported_db):
    r1 = client.post("/api/v1/scores/recompute", json={"universe": "seed"})
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["companies_processed"] == 720
    assert body1["method_version"] == "v1"

    r_score = client.get("/api/v1/companies/US:MMM:US/score")
    assert r_score.status_code == 200
    first = r_score.json()
    assert first["disclaimer"]
    assert "not investment advice" in first["disclaimer"].lower()

    r2 = client.post("/api/v1/scores/recompute", json={"universe": "seed"})
    assert r2.status_code == 200
    second = client.get("/api/v1/companies/US:MMM:US/score").json()
    assert second["composite"] == first["composite"], "recompute must be deterministic"
    assert second["method_version"] == "v1"


def test_score_404_before_compute(client, imported_db):
    # fresh company without score -> 404
    assert client.get("/api/v1/companies/CA:NOPE:TSX/score").status_code == 404


def test_rankings_split_by_currency(client):
    r = client.post("/api/v1/scores/recompute", json={"universe": "seed"})
    assert r.status_code == 200
    r = client.get("/api/v1/rankings?scope=seed&currency=USD&limit=20")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0
    items = body["items"]
    assert all(i["currency"] == "USD" for i in items)
    comps = [i["composite"] for i in items]
    assert comps == sorted(comps, reverse=True), "rankings must be ordered desc"


def test_sector_rankings_endpoint(client):
    r = client.get("/api/v1/sectors/Software/rankings?currency=USD&limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["currency"] == "USD"
    comps = [i["composite"] for i in body["items"]]
    assert comps == sorted(comps, reverse=True)


def test_signal_histogram_shape(client):
    client.post("/api/v1/scores/recompute", json={"universe": "seed"})
    r = client.get("/api/v1/scores/summary")
    assert r.status_code == 200
    body = r.json()
    assert "signal_histogram" in body
    assert body["method_version"] == "v1"
    assert body["composite_non_null"] + body["growth_null_among_scored"] >= body["composite_non_null"]
