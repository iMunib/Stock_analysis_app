"""Tests for GuruFocus-Style Solvency & Distress Engine (Altman Z-Score) (Master Directive WS3)."""
import pytest
from app.models import Company, FinancialSnapshot
from app.services.distress_engine import compute_distress


def test_altman_z_industrial_manufacturing(imported_db):
    """Manufacturing firms use original 5-factor Z-Score."""
    res = compute_distress(imported_db, "US:MMM:US")
    assert res["status"] == "computed"
    assert res["model_used"] == "manufacturing"
    assert res["z_score"] is not None
    assert res["active_z"] == res["z_score"]
    assert res["zone"] in ("Safe", "Grey", "Distress")
    assert "x1_working_capital_to_ta" in res["factors"]
    assert "x5_sales_to_ta" in res["factors"]


def test_altman_z_tech_service_model(imported_db):
    """Asset-light / software firms use 4-factor Z''-Score without asset turnover distortion."""
    res = compute_distress(imported_db, "US:MSFT:US")
    assert res["status"] == "computed"
    assert res["model_used"] == "non_manufacturing"
    assert res["z_double_prime"] is not None
    assert res["active_z"] == res["z_double_prime"]
    assert res["zone"] in ("Safe", "Grey", "Distress")


def test_altman_z_bank_financial_exclusion(imported_db):
    """Banks and financial institutions must be excluded."""
    res = compute_distress(imported_db, "CA:RY:TSX")
    assert res["status"] == "financial_institution_excluded"
    assert res["model_used"] == "excluded"
    assert res["z_score"] is None
    assert res["zone"] == "Excluded"
