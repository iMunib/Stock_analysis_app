"""Importer tests against the real seed workbook (Phase 1 exit requirement)."""
from __future__ import annotations

import openpyxl
from sqlalchemy import select

from app.models import Company, DataQualityFlag, FinancialSnapshot, Placement
from app.services.importer import SNAPSHOT_FIELD_MAP, _import_companies, _sheet_rows


def test_exactly_720_unique_companies(imported_db):
    total = imported_db.query(Company).count()
    assert total == 720, f"expected 720 unique companies, got {total}"


def test_currency_stored_verbatim_no_conversion(imported_db, seed_workbook):
    # Pick a known CAD company from the workbook and compare raw cell to DB.
    wb = openpyxl.load_workbook(seed_workbook, read_only=True, data_only=True)
    header, rows = _sheet_rows(wb, "01_All_Companies")
    idx = {name: header.index(name) for name in header}
    cad_row = next(r for r in rows if str(r[idx["Company_ID"]]).startswith("CA:"))
    cid = str(r_cad := cad_row[idx["Company_ID"]])
    expected_rev = cad_row[idx["Revenue"]]
    wb.close()

    company = imported_db.get(Company, cid)
    assert company is not None
    assert company.currency == "CAD"
    snap = (
        imported_db.execute(
            select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid)
        )
        .scalars()
        .first()
    )
    if expected_rev is not None:
        assert snap.revenue == float(expected_rev), "CAD revenue must be stored verbatim (no conversion)"
    assert snap.currency == "CAD"


def test_blank_stays_null_for_bank(imported_db, seed_workbook):
    """Find a Financials company whose Total_Debt is blank in the workbook;
    assert the DB kept NULL (never 0, never backfilled)."""
    wb = openpyxl.load_workbook(seed_workbook, read_only=True, data_only=True)
    header, rows = _sheet_rows(wb, "01_All_Companies")
    idx = {name: header.index(name) for name in header}
    target = None
    for r in rows:
        if r[idx["GICS_Sector"]] == "Financials":
            cid = str(r[idx["Company_ID"]])
            if r[idx["Total_Debt"]] in (None, ""):
                target = cid
                break
    wb.close()
    assert target, "no blank-Total_Debt financial found in seed (unexpected)"
    snap = (
        imported_db.execute(
            select(FinancialSnapshot).where(FinancialSnapshot.company_id == target)
        )
        .scalars()
        .first()
    )
    assert snap is not None
    assert snap.total_debt is None, f"{target} Total_Debt must stay NULL"


def test_extras_do_not_inflate_company_count(imported_db):
    assert imported_db.query(Company).count() == 720
    placements = imported_db.query(Placement).count()
    extras = imported_db.query(Placement).filter(Placement.placement_role == "Extra").count()
    assert placements > 720, "placements should include Primary + Extra + GICS rows"
    assert extras > 0, "expected Extra placement rows in the seed"
    # Every placement references an existing company (no phantom rows).
    company_ids = {c.company_id for c in imported_db.query(Company).all()}
    orphan = [p for p in imported_db.query(Placement).all() if p.company_id not in company_ids]
    assert not orphan


def test_idempotent_reimport(imported_db, seed_workbook):
    before = imported_db.query(Company).count()
    assert before == 720
    # Run the full import again; count must not change and no duplicate snapshots.
    from app.services.importer import run_import

    run_import(force=True, seed_path=seed_workbook)
    after = imported_db.query(Company).count()
    assert after == 720
    snaps = (
        imported_db.execute(
            select(FinancialSnapshot.company_id, FinancialSnapshot.fiscal_year, FinancialSnapshot.period_type)
        )
        .all()
    )
    assert len(snaps) == len(set(snaps)), "duplicate snapshot rows detected"


def test_quality_flags_imported(imported_db):
    flags = imported_db.query(DataQualityFlag).count()
    assert flags > 0, "expected quality flags from 03_Data_Quality"
    raw_ids = imported_db.query(DataQualityFlag).limit(1).all()
    assert all(f.company_id for f in raw_ids)


def test_fiscal_year_never_invented(imported_db):
    nulls = imported_db.query(FinancialSnapshot).filter(FinancialSnapshot.fiscal_year.isnot(None)).count()
    assert nulls == 0, "Phase 1 must not invent fiscal years"


def test_asof_from_price_asof(imported_db):
    from datetime import date

    snap = imported_db.query(FinancialSnapshot).filter(FinancialSnapshot.as_of_date.isnot(None)).first()
    assert snap is not None
    assert isinstance(snap.as_of_date, date)


def test_mmm_revenue_verbatim(imported_db, seed_workbook):
    """Anchor test: US:MMM Revenue equals the workbook cell exactly."""
    wb = openpyxl.load_workbook(seed_workbook, read_only=True, data_only=True)
    header, rows = _sheet_rows(wb, "01_All_Companies")
    idx = {name: header.index(name) for name in header}
    mmm = next(r for r in rows if str(r[idx["Company_ID"]]) == "US:MMM:US")
    expected = float(mmm[idx["Revenue"]])
    wb.close()
    snap = (
        imported_db.execute(
            select(FinancialSnapshot).where(FinancialSnapshot.company_id == "US:MMM:US")
        )
        .scalars()
        .first()
    )
    assert snap.revenue == expected == 24_948_000_000.0
