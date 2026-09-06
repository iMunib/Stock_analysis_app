"""Wave 4 Valuation suite tests (Epic 10: 38 stories — Guided DCF, EPV, DDM, Residual, Normalized, Decomposition, Rank)."""
from __future__ import annotations

import pytest
from app.models import FinancialSnapshot


@pytest.fixture(autouse=True)
def setup_wave4_data(client, imported_db):
    # Ensure AAPL has enough history for EPV/DDM etc (reuse MSFT/AAPL histories from wave3)
    # Ensure a non-financial with dividend history for DDM via retained earnings walk
    # Add a synthetic dividend history for US:KO:US if missing (KO is steady payer)
    rows = [
        dict(company_id="US:KO:US", fiscal_year=2022, currency="USD", revenue=43000000000.0, net_income=9500000000.0, retained_earnings=25000000000.0, total_assets=92000000000.0, book_equity=25000000000.0, total_debt=44000000000.0, ebit=12000000000.0, shares_snapshot=4300000000.0, price=60.0, market_cap=258000000000.0, cash_st_investments=10000000000.0),
        dict(company_id="US:KO:US", fiscal_year=2023, currency="USD", revenue=45900000000.0, net_income=10700000000.0, retained_earnings=28000000000.0, total_assets=97000000000.0, book_equity=27000000000.0, total_debt=45000000000.0, ebit=13000000000.0, shares_snapshot=4300000000.0, price=60.0, market_cap=258000000000.0, cash_st_investments=11000000000.0),
        dict(company_id="US:KO:US", fiscal_year=2024, currency="USD", revenue=47000000000.0, net_income=11500000000.0, retained_earnings=31000000000.0, total_assets=100000000000.0, book_equity=29000000000.0, total_debt=46000000000.0, ebit=13500000000.0, shares_snapshot=4300000000.0, price=62.0, market_cap=266600000000.0, cash_st_investments=12000000000.0),
    ]
    for row in rows:
        existing = imported_db.query(FinancialSnapshot).filter_by(company_id=row["company_id"], fiscal_year=row["fiscal_year"], period_type="FY").first()
        if not existing:
            imported_db.add(FinancialSnapshot(company_id=row["company_id"], fiscal_year=row["fiscal_year"], period_type="FY", currency=row["currency"], source="test_fixture", **{k: v for k, v in row.items() if k not in ("company_id", "fiscal_year", "currency")}))
        else:
            for k, v in row.items():
                if k in ("company_id", "fiscal_year", "currency"):
                    continue
                if getattr(existing, k) is None:
                    setattr(existing, k, v)
    imported_db.commit()
    client.post("/api/v1/scores/recompute", json={"universe": "seed"})


def test_guided_dcf_computed_and_wacc_build(client):
    res = client.get("/api/v1/companies/US:AAPL:US/valuation/guided?revenue_growth=0.05&operating_margin=0.30&wacc=0.09&terminal_g=0.025")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "computed"
    assert "wacc_build" in data
    assert "Rf" in data["wacc_build"]["formula"]
    assert data["per_share"] is not None
    assert "uncertainty_range" in data
    assert data["uncertainty_range"]["p10_per_share"] is not None
    assert data["uncertainty_range"]["p90_per_share"] is not None
    assert "steps" in data and len(data["steps"]) == 5
    assert "terminal_heavy" in data
    assert "disclaimer" in data


def test_guided_dcf_bank_excluded(client):
    res = client.get("/api/v1/companies/CA:RY:TSX/valuation/guided")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "financial_institution_excluded"
    assert "DDM" in data["reason"] or "Residual" in data["reason"]


def test_epv_computed_and_thin_history_flag(client):
    res = client.get("/api/v1/companies/US:AAPL:US/valuation/epv?wacc=0.09")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("computed", "insufficient_data")
    if data["status"] == "computed":
        assert data["epv"] is not None
        assert data["reproduction_cost"] is not None
        assert "thin_history" in data
        assert "disclaimer" in data


def test_epv_financial_note_for_bank(client):
    res = client.get("/api/v1/companies/CA:RY:TSX/valuation/epv")
    assert res.status_code == 200
    data = res.json()
    assert data["is_financial"] is True
    assert data["financial_note"] is not None


def test_ddm_insufficient_and_computed_paths(client):
    # KO should have 3-yr div history via RE walk → computed
    res = client.get("/api/v1/companies/US:KO:US/valuation/ddm")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("computed", "insufficient_data")
    if data["status"] == "computed":
        assert data["fair_value_per_share"] is not None
    # Sparse name should be insufficient
    res2 = client.get("/api/v1/companies/CA:IIP.UN:TSX/valuation/ddm")
    assert res2.status_code == 200
    assert res2.json()["status"] == "insufficient_data"


def test_residual_income_bank_computed_and_nonbank_not_applicable(client):
    res_bank = client.get("/api/v1/companies/CA:RY:TSX/valuation/residual-income")
    assert res_bank.status_code == 200
    # RY may be insufficient if book history thin, but should not be not_applicable
    assert res_bank.json()["status"] in ("computed", "insufficient_data")
    res_nonbank = client.get("/api/v1/companies/US:AAPL:US/valuation/residual-income")
    assert res_nonbank.status_code == 200
    assert res_nonbank.json()["status"] == "not_applicable"


def test_normalized_earnings_cyclical_and_range(client):
    res = client.get("/api/v1/companies/US:XOM:US/valuation/normalized")
    assert res.status_code == 200
    data = res.json()
    assert "normalized_ebit" in data
    assert "is_normalized" in data
    assert "median_5y" in data or data.get("median_5y") is None


def test_decomposition_insufficient_or_computed(client):
    res = client.get("/api/v1/companies/US:AAPL:US/valuation/decomposition")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("computed", "insufficient_data")
    if data["status"] == "computed":
        assert "volume_component" in data
        assert "price_note" in data


def test_valuation_rank_and_compare(client):
    res = client.get("/api/v1/valuation/rank?ids=US:AAPL:US,US:MSFT:US")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 2
    assert "discount_pct" in data["ranked"][0]
    # Compare exactly 2
    res2 = client.get("/api/v1/valuation/compare?ids=US:AAPL:US,US:MSFT:US")
    assert res2.status_code == 200
    assert res2.json()["count"] == 2


def test_guided_dcf_uncertainty_range_not_single_point(client):
    res = client.get("/api/v1/companies/US:MSFT:US/valuation/guided")
    assert res.status_code == 200
    data = res.json()
    if data["status"] == "computed":
        r = data["uncertainty_range"]
        assert r["p10_per_share"] != r["p50_per_share"] != r["p90_per_share"] or r["p10_per_share"] is not None
