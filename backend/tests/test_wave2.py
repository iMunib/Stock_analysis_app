"""Test suite for Wave 2: Screener Presets, Multi-Metric Filtering, & Watchlist Morning Brief.

Covers:
- Epic 7 (28 Stories): Canonical presets, AND/OR logic, 5Y sparklines, book checklists,
  'Why matched' cohort stats, NULL diagnostic warnings, CSV export, custom preset CRUD, auto-run queue.
- Epic 5 (5 Stories): Watchlist 1-page morning brief, historical pillar/composite deltas,
  signal re-ratings, post-earnings comparison, SEDAR+/EDGAR filings, alert channel routing.
"""
from __future__ import annotations

import pytest
from app.models import FinancialStatement


@pytest.fixture(autouse=True)
def setup_wave2_data(client, imported_db):
    """Ensure scores are computed and test statement history is available in the test database."""
    test_histories = [
        # SHOP: prior years for post-earnings and sparklines
        dict(company_id="CA:SHOP:TSX", fiscal_year=2024, currency="CAD", revenue=8880000000.0, net_income=2019000000.0, diluted_eps=1.56, free_cash_flow=1597000000.0),
        dict(company_id="CA:SHOP:TSX", fiscal_year=2023, currency="CAD", revenue=7060000000.0, net_income=-1220000000.0, diluted_eps=-0.98, free_cash_flow=905000000.0),
        # AAPL: prior years for post-earnings and sparklines
        dict(company_id="US:AAPL:US", fiscal_year=2024, currency="USD", revenue=391035000000.0, net_income=93736000000.0, diluted_eps=6.08, free_cash_flow=108807000000.0),
        dict(company_id="US:AAPL:US", fiscal_year=2023, currency="USD", revenue=383285000000.0, net_income=96995000000.0, diluted_eps=6.13, free_cash_flow=99584000000.0),
        # ACN: multi-year history for screener top-10 sparklines
        dict(company_id="US:ACN:US", fiscal_year=2024, currency="USD", revenue=64896000000.0, net_income=7333000000.0, diluted_eps=11.44, free_cash_flow=8644000000.0),
        dict(company_id="US:ACN:US", fiscal_year=2023, currency="USD", revenue=64111000000.0, net_income=6877000000.0, diluted_eps=10.77, free_cash_flow=8435000000.0),
    ]
    for row in test_histories:
        existing = imported_db.query(FinancialStatement).filter_by(
            company_id=row["company_id"], fiscal_year=row["fiscal_year"], period_type="FY"
        ).first()
        if not existing:
            imported_db.add(FinancialStatement(
                company_id=row["company_id"],
                fiscal_year=row["fiscal_year"],
                period_type="FY",
                currency=row["currency"],
                source="test_fixture",
                revenue=row["revenue"],
                net_income=row["net_income"],
                diluted_eps=row["diluted_eps"],
                free_cash_flow=row["free_cash_flow"],
            ))
    imported_db.commit()
    client.post("/api/v1/scores/recompute", json={"universe": "seed"})


def test_screen_canonical_presets(client):
    """Verifies that canonical literature presets execute cleanly and return matching records."""
    # 1. Buffett-Burry Deep Value
    res = client.get("/api/v1/screen?preset=buffett_burry_deep_value")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    for it in data["items"]:
        assert it["is_bank"] is False
        if it["composite"] is not None:
            assert it["composite"] >= 6.0

    # 2. Greenblatt Magic Formula
    res_gb = client.get("/api/v1/screen?preset=greenblatt_magic_formula")
    assert res_gb.status_code == 200
    data_gb = res_gb.json()
    assert data_gb["count"] > 0

    # 3. Sustainable Dividends (US-0003)
    res_div = client.get("/api/v1/screen?preset=sustainable_dividends")
    assert res_div.status_code == 200
    data_div = res_div.json()
    assert data_div["count"] > 0

    # 4. GARP (US-0005)
    res_garp = client.get("/api/v1/screen?preset=garp_investor")
    assert res_garp.status_code == 200
    assert res_garp.json()["count"] > 0

    # 5. Novy-Marx Gross Profitability (US-0007)
    res_nm = client.get("/api/v1/screen?preset=novy_marx_gross_profitability")
    assert res_nm.status_code == 200
    assert res_nm.json()["count"] > 0


def test_screen_criteria_logic_and_vs_or(client):
    """Tests interactive criteria combining under AND vs OR logic (US-0010)."""
    # Strict AND logic: both composite >= 8.0 AND roe >= 25%
    res_and = client.get("/api/v1/screen?composite_min=8.0&roe_min=25.0&criteria_logic=AND")
    assert res_and.status_code == 200
    count_and = res_and.json()["count"]

    # Relaxed OR logic: either composite >= 8.0 OR roe >= 25%
    res_or = client.get("/api/v1/screen?composite_min=8.0&roe_min=25.0&criteria_logic=OR")
    assert res_or.status_code == 200
    count_or = res_or.json()["count"]

    assert count_or >= count_and, "OR logic must match equal or more companies than AND logic"


def test_screen_features_sparklines_and_checklists(client):
    """Verifies that screener returns 5Y sparkline arrays and academic book checklists (US-0039, US-0041)."""
    res = client.get("/api/v1/screen?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0

    has_sparkline = False
    for it in data["items"]:
        # Verify book checklists structure (US-0041)
        ck = it.get("checklists", {})
        assert "graham" in ck
        assert "lynch" in ck
        assert "greenblatt" in ck
        assert "piotroski" in ck

        # Verify revenue sparkline exists (US-0039)
        sp = it.get("revenue_sparkline", [])
        if len(sp) >= 2:
            has_sparkline = True
            assert all(isinstance(v, (int, float)) for v in sp)

    assert has_sparkline, "At least some companies must have multi-year revenue sparklines"


def test_screen_why_matched_summary_and_null_warning(client):
    """Tests 'Why These Matched' cohort summary and NULL diagnostic warnings (US-0038, US-0049)."""
    # Active cohort summary
    res = client.get("/api/v1/screen?composite_min=6.5&currency=USD")
    assert res.status_code == 200
    data = res.json()
    assert data["why_matched_summary"] is not None
    summary = data["why_matched_summary"]
    assert summary["count"] == data["count"]
    if data["count"] > 0:
        assert summary["median_composite"] is not None
        assert isinstance(summary["top_sectors"], list)

    # Empty result NULL diagnostic warning (US-0049)
    res_empty = client.get("/api/v1/screen?composite_min=9.99&debt_to_ebitda_max=0.01")
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert data_empty["total"] == 0
    assert data_empty["null_warning"] is not None
    assert data_empty["null_warning"]["has_null_data_warning"] is True
    assert len(data_empty["null_warning"]["null_reasons"]) > 0


def test_screener_csv_export(client):
    """Tests CSV export with embedded filter metadata and formula-transparent columns (US-0012, US-0030)."""
    res = client.get("/api/v1/screen/export?currency=USD&composite_min=6.0")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    content = res.text

    # Verify metadata header comments (US-0012)
    assert "# Equity Intelligence Screener Export" in content
    assert "# Active Filters:" in content
    assert "# Methodology: Locked weights" in content

    # Verify formula-transparent headers (US-0030)
    assert "Composite Score [Quality*0.30 + Value*0.25 + Growth*0.25 + Risk*0.20 * Penalty]" in content
    assert "P/E Ratio [Market Price / Diluted EPS]" in content
    assert "ROE % [Net Income / Book Equity * 100]" in content
    assert "ROIC % [NOPAT / Invested Capital * 100]" in content
    assert "Graham Checklist" in content
    assert "Lynch Checklist" in content


def test_screener_custom_preset_crud_and_autorun(client):
    """Tests saving custom presets with one-word names and auto-run queue toggling (US-0009, US-0042)."""
    # 1. Create custom preset (US-0009)
    payload = {
        "name": "Bargains",
        "criteria": {"composite_min": 6.5, "pe_max": 15.0, "exclude_banks": True},
        "auto_run_on_refresh": True,
    }
    res_post = client.post("/api/v1/screener/presets", json=payload)
    assert res_post.status_code == 200
    post_data = res_post.json()
    assert post_data["ok"] is True
    assert post_data["name"] == "Bargains"
    preset_id = post_data["id"]

    # 2. Verify it appears in list
    res_list = client.get("/api/v1/screener/presets")
    assert res_list.status_code == 200
    presets = res_list.json()
    match = next((p for p in presets if p["id"] == preset_id), None)
    assert match is not None
    assert match["is_system"] is False
    assert match["auto_run_on_refresh"] is True

    # 3. Toggle auto-run queue (US-0042)
    res_toggle = client.put(f"/api/v1/screener/presets/{preset_id}/auto-run")
    assert res_toggle.status_code == 200
    assert res_toggle.json()["auto_run_on_refresh"] is False

    # 4. Delete custom preset
    res_del = client.delete(f"/api/v1/screener/presets/{preset_id}")
    assert res_del.status_code == 200
    assert res_del.json()["ok"] is True


def test_watchlist_digest_endpoint(client):
    """Tests 1-page morning watchlist brief, deltas, and filing provenance (US-0351, US-0092, US-0453)."""
    res = client.get("/api/v1/watchlist/digest?ids=US:AAPL:US,CA:SHOP:TSX,US:MSFT:US")
    assert res.status_code == 200
    data = res.json()

    assert "summary" in data
    assert "items" in data
    summary = data["summary"]
    assert summary["total_watched"] == 3
    assert "as_of_date" in summary

    items = data["items"]
    assert len(items) == 3

    # Check Canadian stock routing to SEDAR+ (Rule #3 & US-0453)
    shop = next((it for it in items if it["company_id"] == "CA:SHOP:TSX"), None)
    assert shop is not None
    assert shop["currency"] == "CAD"
    assert "sedarplus.ca" in shop["fresh_filing"]["filing_url"]

    # Check US stock routing to SEC EDGAR
    aapl = next((it for it in items if it["company_id"] == "US:AAPL:US"), None)
    assert aapl is not None
    assert aapl["currency"] == "USD"
    assert "sec.gov" in aapl["fresh_filing"]["filing_url"]

    # Verify pillar deltas exist (US-0092)
    for it in items:
        p_deltas = it["pillar_deltas"]
        assert "quality" in p_deltas
        assert "value" in p_deltas
        assert "growth" in p_deltas
        assert "risk" in p_deltas
        assert "delta" in p_deltas["quality"]


def test_watchlist_post_earnings_comparison(client):
    """Tests post-earnings actuals vs prior year comparison (US-0377)."""
    res = client.get("/api/v1/watchlist/digest?ids=CA:SHOP:TSX,US:AAPL:US")
    assert res.status_code == 200
    data = res.json()

    for it in data["items"]:
        pe = it["post_earnings"]
        assert pe["has_recent_earnings"] is True
        assert pe["fiscal_year"] is not None
        assert pe["revenue"] is not None
        assert pe["prior_revenue"] is not None
        assert pe["revenue_growth_pct"] is not None
        assert "score_moved" in pe


def test_watchlist_alert_severity_and_routing(client):
    """Tests per-alert severity and channel routing (digest vs immediate) (US-0367)."""
    custom_alerts = [
        {"id": "US:AAPL:US", "pe_above": 20.0, "severity": "elevated", "channel": "digest"},
        {"id": "CA:SHOP:TSX", "composite_below": 9.0, "severity": "critical", "channel": "immediate"},
    ]
    res = client.post("/api/v1/watchlist/digest", json={"ids": ["US:AAPL:US", "CA:SHOP:TSX"], "alerts": custom_alerts})
    assert res.status_code == 200
    data = res.json()

    for it in data["items"]:
        alerts = it["alerts"]
        assert len(alerts) > 0
        for al in alerts:
            assert al["severity"] in ("critical", "elevated", "informational")
            assert al["channel"] in ("immediate", "digest")
            assert "title" in al
            assert "message" in al


def test_watchlist_deltas_feed(client):
    """Tests programmatic /api/v1/watchlist/deltas feed."""
    res = client.get("/api/v1/watchlist/deltas?ids=US:MSFT:US,CA:SHOP:TSX")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["deltas"]) == 2
    for d in data["deltas"]:
        assert "current_composite" in d
        assert "composite_delta" in d
        assert "pillar_deltas" in d
