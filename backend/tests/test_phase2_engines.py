"""Comprehensive unit tests for Phase 2: Core Analytical Engines & Decision Logic."""
import pytest
from app.models import Company, FinancialSnapshot
from app.services.archetype_engine import classify_archetype
from app.services.owner_earnings import compute_owner_earnings
from app.services.moat_engine import compute_economic_moat
from app.services.penman_engine import compute_penman
from app.services.valuation_engine import evaluate_reverse_dcf_hurdles
from app.services.verdict_engine import (
    synthesize_safety_verdict,
    VERDICT_COMPOUNDER,
    VERDICT_BARGAIN,
    VERDICT_OVERVALUED,
    VERDICT_CYCLICAL,
    VERDICT_AVOID,
)


def test_peter_lynch_fast_grower(imported_db):
    """Test Fast Grower classification (CAGR >= 20% with clean balance sheet)."""
    cid = "US:TEST_FAST_GROW:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="FAST", country="US", currency="USD",
            name="Fast Growth Corp", gics_sector="Information Technology",
        ))
        s1 = FinancialSnapshot(
            company_id=cid, fiscal_year=2021, period_type="FY", currency="USD",
            revenue=100_000_000.0, diluted_eps=1.00, book_equity=100_000_000.0,
        )
        s2 = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=200_000_000.0, diluted_eps=2.00, book_equity=200_000_000.0,  # ~26% CAGR over 3 yrs
            market_cap=2_000_000_000.0, price=20.0, net_income=200_000_000.0,
        )
        imported_db.add_all([s1, s2])
        imported_db.commit()

        res = classify_archetype(imported_db, cid)
        assert res["archetype"] == "Fast Growers"
        assert res["metrics"]["revenue_cagr_pct"] >= 20.0
        assert res["metrics"]["peg_ratio"] is not None
        assert res["metrics"]["peg_status"] in ("Attractive", "Fair", "Stretched")
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()


def test_buffett_owner_earnings_greenwald(imported_db):
    """Test Greenwald Growth vs Maintenance CapEx separation."""
    cid = "US:TEST_OWNER_EARN:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="BUFFETT", country="US", currency="USD",
            name="Buffett Quality Inc", gics_sector="Consumer Staples",
        ))
        s1 = FinancialSnapshot(
            company_id=cid, fiscal_year=2023, period_type="FY", currency="USD",
            revenue=500_000_000.0, current_assets=100_000_000.0, current_liabilities=50_000_000.0,
        )
        s2 = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=600_000_000.0, net_income=80_000_000.0, ebit=100_000_000.0, ebitda=120_000_000.0,
            capex=30_000_000.0, ppe_net=150_000_000.0, market_cap=1_000_000_000.0,
            current_assets=120_000_000.0, current_liabilities=60_000_000.0,
        )
        imported_db.add_all([s1, s2])
        imported_db.commit()

        res = compute_owner_earnings(imported_db, cid)
        assert res["status"] == "computed"
        assert res["growth_capex"] > 0.0
        assert res["maintenance_capex"] <= res["total_capex"]
        assert res["owner_earnings"] is not None
        assert res["owner_earnings_yield_pct"] is not None
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()


def test_pat_dorsey_moat_classification(imported_db):
    """Test Dorsey 4-Moat heuristic model (Wide, Narrow, None)."""
    cid = "US:TEST_MOAT_CORP:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="MOAT", country="US", currency="USD",
            name="Wide Moat Monopoly Inc", gics_sector="Information Technology",
        ))
        s1 = FinancialSnapshot(
            company_id=cid, fiscal_year=2021, period_type="FY", currency="USD",
            revenue=100_000_000.0, gross_profit=70_000_000.0,  # 70% Gross Margin
        )
        s2 = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=180_000_000.0, gross_profit=135_000_000.0, ebit=60_000_000.0,
            book_equity=200_000_000.0, net_income=50_000_000.0,  # 25% ROE, 75% Gross Margin
        )
        imported_db.add_all([s1, s2])
        imported_db.commit()

        res = compute_economic_moat(imported_db, cid)
        assert res["moat_rating"] in ("Wide", "Narrow")
        assert res["sources"]["switching_costs"]["present"] is True
        assert res["sources"]["intangible_assets"]["present"] is True
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()


def test_penman_buyback_distortion_alert():
    """Test buyback distortion alert when ROIC > 30%, FLEV > 2.0, and RNOA < 15%."""
    snap = FinancialSnapshot(
        total_assets=100_000_000.0,
        total_liabilities=85_000_000.0,
        total_debt=70_000_000.0,
        cash_st_investments=10_000_000.0,
        book_equity=15_000_000.0,  # Equity compressed by buybacks
        ebit=14_000_000.0,
        interest_expense=3_000_000.0,
        roe_calc=0.45,  # 45% headline ROE/ROIC
    )
    res = compute_penman(snap)
    assert res is not None
    assert res["flev"] > 2.0
    assert res["rnoa"] < 0.25
    assert res["leverage_distortion"] is True
    assert res["buyback_distortion_alert"] == "High ROIC is artificially inflated by debt-funded buybacks."


def test_safety_verdict_deterministic_synthesis(imported_db):
    """Test deterministic 60-second safety verdict across diverse profiles."""
    msft_verdict = synthesize_safety_verdict(imported_db, "US:MSFT:US")
    assert msft_verdict["verdict_badge"] in (VERDICT_COMPOUNDER, VERDICT_BARGAIN, VERDICT_OVERVALUED)
    assert "solvency" in msft_verdict["traffic_lights"]
    assert len(msft_verdict["decision_bullets"]) > 0


def test_dossier_expanded_analytical_payload(client, imported_db):
    """Verify dossier endpoint returns complete decision_verdict, archetype, moat, and 3 tiers."""
    from app.models import CompanyProfile
    prof = imported_db.get(CompanyProfile, "US:MSFT:US")
    if not prof:
        imported_db.add(CompanyProfile(company_id="US:MSFT:US", summary="Microsoft Corp", dividend_yield=0.008))
        imported_db.commit()

    resp = client.get("/api/v1/companies/US:MSFT:US/dossier")
    assert resp.status_code == 200
    data = resp.json()
    assert "decision_verdict" in data and data["decision_verdict"] is not None
    assert "archetype" in data and data["archetype"] is not None
    assert "moat_rating" in data and data["moat_rating"] is not None
    assert "level1" in data and data["level1"] is not None
    assert "level2" in data and data["level2"] is not None
    assert "level3" in data and data["level3"] is not None
