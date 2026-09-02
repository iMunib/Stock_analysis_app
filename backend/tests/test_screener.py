"""Tests for the multi-metric forensic screener (directive §2C/§3)."""
from __future__ import annotations

import pytest

from app.models import (
    Company,
    FinancialSnapshotTTM,
    Score,
    ScreenerPreset,
    ValuationReverseDCF,
)
from app.services.screener_engine import ensure_system_presets, run_screener_query


@pytest.fixture()
def screener_companies(imported_db):
    """Three companies with TTM/DCF/Score rows chosen to split the presets."""
    rows = [
        # Compounder: high ROIC, cheap-ish, clean accruals, negative expectations gap
        dict(
            cid="US:COMPOUND:US", cur="USD", roic=0.22, ev_ebitda=9.0, fcf_yield=0.08,
            sloan=0.02, conv=1.10, gap=-0.06, composite=7.5, signal="strong_candidate",
        ),
        # Red-flag: accruals above 0.10 and weak conversion (OR logic target)
        dict(
            cid="US:REDFLAG:US", cur="USD", roic=0.05, ev_ebitda=18.0, fcf_yield=0.02,
            sloan=0.14, conv=0.40, gap=0.03, composite=4.0, signal="watchlist",
        ),
        # Canadian mid: mediocre, no DCF row (NULL joins must not crash)
        dict(
            cid="CA:MIDCO:TSX", cur="CAD", roic=0.09, ev_ebitda=12.0, fcf_yield=0.04,
            sloan=0.06, conv=0.90, gap=None, composite=5.5, signal="watchlist",
        ),
    ]
    for r in rows:
        imported_db.merge(Company(
            company_id=r["cid"], ticker=r["cid"].split(":")[1], name=f"Test {r['cid']}",
            country="US" if r["cid"].startswith("US:") else "CA", currency=r["cur"],
            gics_sector="Industrials", is_deleted=False,
        ))
        imported_db.merge(FinancialSnapshotTTM(
            company_id=r["cid"], currency=r["cur"], quarter_count=4, is_complete=True,
            roic=r["roic"], ev_ebitda=r["ev_ebitda"], fcf_yield=r["fcf_yield"],
            sloan_accrual_ratio=r["sloan"], cash_conversion_ratio=r["conv"],
        ))
        imported_db.merge(Score(
            company_id=r["cid"], composite=r["composite"], signal=r["signal"],
            method_version="v1", peer_set_type="gics_currency",
        ))
        if r["gap"] is not None:
            imported_db.merge(ValuationReverseDCF(
                company_id=r["cid"], status="converged", market_implied_growth_10y=0.10 + r["gap"],
                historical_5y_cagr=0.10, expectations_gap=r["gap"], wacc=0.09, terminal_growth_rate=0.025,
            ))
    imported_db.commit()
    return imported_db


def test_system_presets_seeded(screener_companies):
    presets = ensure_system_presets(screener_companies)
    ids = {p.id for p in presets}
    assert {"buffett_burry_deep_value", "forensic_red_flags", "discounted_compounders"} <= ids
    assert all(p.is_system_preset for p in presets)
    # idempotent
    again = ensure_system_presets(screener_companies)
    assert len(again) == len(presets)
    # stored rows match the engine contract
    assert screener_companies.get(ScreenerPreset, "buffett_burry_deep_value") is not None


def test_deep_value_preset_filters(screener_companies):
    out = run_screener_query(screener_companies, {
        "roic_min": 0.15, "ev_ebitda_max": 10.0, "fcf_yield_min": 0.07, "sloan_accrual_max": 0.05,
    })
    ids = [r["company_id"] for r in out["items"]]
    assert "US:COMPOUND:US" in ids
    assert "US:REDFLAG:US" not in ids
    assert "CA:MIDCO:TSX" not in ids


def test_red_flag_or_logic(screener_companies):
    # Sloan > 0.10 OR conversion < 0.60
    out = run_screener_query(screener_companies, {
        "sloan_accrual_min": 0.10, "cash_conversion_max": 0.60, "flag_logic": "OR",
    })
    ids = {r["company_id"] for r in out["items"]}
    assert "US:REDFLAG:US" in ids  # matches both branches
    assert "US:COMPOUND:US" not in ids


def test_compounders_expectations_gap(screener_companies):
    out = run_screener_query(screener_companies, {"roic_min": 0.18, "expectations_gap_max": -0.04})
    ids = [r["company_id"] for r in out["items"]]
    assert ids == ["US:COMPOUND:US"]


def test_currency_never_mixed_and_nulls_survive(screener_companies):
    out = run_screener_query(screener_companies, {"currency": "CAD"})
    ids = [r["company_id"] for r in out["items"]]
    assert "CA:MIDCO:TSX" in ids  # fixture row survives NULL DCF join
    assert all(r["company_id"].startswith("CA:") for r in out["items"])
    assert all(r["currency"] == "CAD" for r in out["items"])
    row = next(r for r in out["items"] if r["company_id"] == "CA:MIDCO:TSX")
    assert row["expectations_gap"] is None  # NULL DCF join stays in results, reported as None
    assert row["dcf_status"] is None

    usd = run_screener_query(screener_companies, {"currency": "USD"})
    assert {r["currency"] for r in usd["items"]} == {"USD"}
    assert all(r["company_id"].startswith("US:") for r in usd["items"])


def test_screener_api_roundtrip(client):
    r = client.post("/api/v1/screener/run", json={"roic_min": 0.15, "limit": 10})
    assert r.status_code == 200
    body = r.json()
    assert {"items", "count", "limit", "offset"} <= set(body)
    for item in body["items"]:
        assert item["currency"] in ("USD", "CAD")
    p = client.get("/api/v1/screener/presets")
    assert p.status_code == 200
    assert len(p.json()) >= 3
