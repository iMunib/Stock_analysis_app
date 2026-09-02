"""Phase 2 tests: ID normalization, provider parsing, ingest policy, API. Network-free."""
from __future__ import annotations

import json
import pathlib
from datetime import date

import pytest
from sqlalchemy import func, select

from app.models import Company, FinancialSnapshot, Placement
from app.providers.base import AnnualStatement, CompanyRef

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


# ---------- ID normalization ----------

def test_normalize_nyse_nasdaq_to_us():
    from app.services.ids import normalize_company_id

    assert normalize_company_id("US:AES:NYSE") == "US:AES:US"
    assert normalize_company_id("US:APA:NASDAQ") == "US:APA:US"
    assert normalize_company_id("US:AES:AMEX") == "US:AES:US"


def test_reject_ca_with_wrong_suffix():
    from app.services.ids import is_valid_company_id, normalize_company_id, parse_company_id

    # the frozen-format validator must reject CA:BN:NYSE
    assert not is_valid_company_id("CA:BN:NYSE")
    assert parse_company_id("CA:BN:NYSE") is None
    # normalize intentionally accepts loose input and canonicalizes to TSX
    assert normalize_company_id("CA:BN:NYSE") == "CA:BN:TSX"


# ---------- EDGAR companyfacts parsing (fixture, no network) ----------

@pytest.fixture(scope="module")
def aapl_rows():
    from app.providers.edgar import parse_companyfacts

    data = json.loads((FIXTURES / "edgar_aapl_companyfacts_stub.json").read_text(encoding="utf-8"))
    return parse_companyfacts(data, expected_currency="USD")


def test_aapl_fixture_yields_5fy_usd(aapl_rows):
    assert len(aapl_rows) >= 5
    assert all(r.currency == "USD" for r in aapl_rows)
    years = sorted(r.fiscal_year for r in aapl_rows)
    assert years == [2020, 2021, 2022, 2023, 2024]
    top = max(aapl_rows, key=lambda r: r.fiscal_year)
    assert top.fields["Revenue"] == 391_035_000_000.0
    assert top.fields["Net_Income"] == 93_736_000_000.0
    assert top.fields["Total_Assets"] == 364_980_000_000.0  # instant fact mapped by end-year


# ---------- Yahoo parsing (fixture frames, no yfinance import) ----------

class _FakeFrame:
    """Minimal pandas-like frame for parse_frames tests."""

    def __init__(self, data: dict, columns: list[str]):
        self._data = data
        self.columns = columns
        self.empty = not data

    def __getitem__(self, col):
        class _Row:
            def __init__(self, d):
                self.index = list(d.keys())
                self._d = d

            def __getitem__(self, k):
                return self._d[k]

        return _Row(self._data[col])


@pytest.fixture(scope="module")
def ry_rows():
    from app.providers.yahoo import parse_frames

    stub = json.loads((FIXTURES / "yahoo_ry_stub.json").read_text(encoding="utf-8"))
    frames = [_FakeFrame(stub[key], list(stub[key].keys())) for key in ("financials", "balance_sheet", "cashflow")]
    return parse_frames(frames, "CAD")


def test_ry_fixture_3fy_cad_no_conversion(ry_rows):
    assert len(ry_rows) >= 3
    years = sorted(r.fiscal_year for r in ry_rows)
    assert years == [2022, 2023, 2024]
    for r in ry_rows:
        assert r.currency == "CAD"
        assert r.source == "yfinance"
    top = max(ry_rows, key=lambda r: r.fiscal_year)
    assert top.fields["Revenue"] == 57_444_000_000.0  # verbatim CAD, no conversion
    assert "Total_Assets" in top.fields


# ---------- Ingest policy: owner rows never overwritten ----------

def _seed_row(db, company_id: str) -> FinancialSnapshot:
    return db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id, FinancialSnapshot.fiscal_year.is_(None)
        )
    ).scalars().one()


def test_owner_snapshot_not_overwritten(imported_db):
    company = imported_db.get(Company, "US:MMM:US")
    revenue_before = _seed_row(imported_db, "US:MMM:US").revenue
    assert revenue_before == 24_948_000_000.0
    ni_before = _seed_row(imported_db, "US:MMM:US").net_income
    assert ni_before is not None

    # A provider row claiming the same (pseudo) year with different values must not touch the seed.
    stmt = AnnualStatement(
        fiscal_year=None, period_end=date(2024, 12, 31), currency="USD",
        source="sec_companyfacts", fields={"Revenue": 1.0, "Net_Income": 2.0},
    )
    ingest_res = _ingest(imported_db, company, [stmt])
    imported_db.rollback()
    seed = _seed_row(imported_db, "US:MMM:US")
    assert seed.revenue == revenue_before
    assert seed.net_income == ni_before
    assert ingest_res["filled_seed_nulls"] == 0


def _ingest(db, company, statements, refresh=False):
    from app.services.ingest import ingest_statements

    return ingest_statements(db, company, statements, refresh=refresh)


def test_provider_fills_seed_nulls_only(imported_db):
    """A NULL field on the seed row may be filled; non-NULL owner values stay."""
    company = imported_db.get(Company, "US:MMM:US")
    seed = _seed_row(imported_db, "US:MMM:US")
    revenue_before = seed.revenue
    # Diluted_EPS is present for MMM; find a NULL statement field to target.
    null_fields = [a for a in ("total_liabilities", "gross_profit", "fcf_calc", "ebitda", "ebit") if getattr(seed, a) is None]
    assert null_fields, "expected at least one NULL statement field on the seed MMM row"
    target = null_fields[0]
    field_name = {
        "total_liabilities": "Total_Liabilities", "gross_profit": "Gross_Profit",
        "fcf_calc": "FCF_Calc", "ebitda": "EBITDA", "ebit": "EBIT",
    }[target]
    other_nonnull = "ebitda" if seed.ebitda is not None else "ebit"
    other_field = {"ebitda": "EBITDA", "ebit": "EBIT"}[other_nonnull]
    other_before = getattr(seed, other_nonnull)
    assert other_before is not None

    stmt = AnnualStatement(
        fiscal_year=None, period_end=None, currency="USD", source="sec_companyfacts",
        fields={field_name: 123.0, other_field: 999.0, "Revenue": revenue_before},
    )
    res = _ingest(imported_db, company, [stmt])
    seed_after = _seed_row(imported_db, "US:MMM:US")
    assert getattr(seed_after, target) == 123.0, "NULL seed field should be filled"
    assert getattr(seed_after, other_nonnull) == other_before, "non-NULL seed value must not be overwritten"
    assert seed_after.revenue == revenue_before
    assert res["filled_seed_nulls"] >= 1
    imported_db.rollback()


def test_ingest_inserts_other_years_with_fiscal_year(imported_db):
    company = imported_db.get(Company, "US:MMM:US")
    stmts = [
        AnnualStatement(fiscal_year=2023, period_end=date(2023, 12, 31), currency="USD",
                        source="sec_companyfacts", fields={"Revenue": 32_681_000_000.0}),
        AnnualStatement(fiscal_year=2024, period_end=date(2024, 12, 31), currency="USD",
                        source="sec_companyfacts", fields={"Revenue": 24_575_000_000.0}),
    ]
    res = _ingest(imported_db, company, stmts)
    imported_db.flush()
    assert res["created"] == 2
    rows = imported_db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == "US:MMM:US", FinancialSnapshot.fiscal_year.isnot(None))
        .order_by(FinancialSnapshot.fiscal_year.desc())
    ).scalars().all()
    assert [r.fiscal_year for r in rows] == [2024, 2023]
    assert rows[0].source == "sec_companyfacts"
    assert rows[0].provider_as_of == date(2024, 12, 31)
    # seed row untouched, still owner_xlsx
    seed = _seed_row(imported_db, "US:MMM:US")
    assert seed.source == "Sector_Financials_Final_Owner.xlsx"
    assert seed.revenue == 24_948_000_000.0
    imported_db.rollback()


def test_second_provider_fills_nulls_first_wins(imported_db):
    company = imported_db.get(Company, "US:MMM:US")
    edgar = AnnualStatement(fiscal_year=2024, period_end=date(2024, 12, 31), currency="USD",
                            source="sec_companyfacts", fields={"Revenue": 100.0, "Net_Income": 10.0})
    _ingest(imported_db, company, [edgar])
    yf = AnnualStatement(fiscal_year=2024, period_end=date(2024, 12, 31), currency="USD",
                         source="yfinance", fields={"Revenue": 999.0, "EBIT": 55.0})
    _ingest(imported_db, company, [yf])
    row = imported_db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == "US:MMM:US", FinancialSnapshot.fiscal_year == 2024)
    ).scalars().one()
    assert row.revenue == 100.0, "first provider wins on conflict"
    assert row.net_income == 10.0
    assert row.ebit == 55.0, "NULL filled by second provider"
    imported_db.rollback()


def test_cache_skip_same_source(imported_db):
    company = imported_db.get(Company, "US:MMM:US")
    stmt = AnnualStatement(fiscal_year=2022, period_end=date(2022, 12, 31), currency="USD",
                           source="sec_companyfacts", fields={"Revenue": 1.0})
    r1 = _ingest(imported_db, company, [stmt])
    assert r1["created"] == 1
    r2 = _ingest(imported_db, company, [stmt])
    assert r2["skipped_cached"] == 1 and r2["created"] == 0
    imported_db.rollback()


# ---------- Placement roles regression ----------

def test_placement_roles_gics_extra_primary(imported_db):
    counts = dict(imported_db.execute(
        select(Placement.placement_role, func.count()).group_by(Placement.placement_role)
    ).all())
    assert counts.get("Primary", 0) == 720
    assert counts.get("Extra", 0) == 66
    assert counts.get("GICS", 0) == 720


# ---------- Quality-flag audit (workbook-level rows kept, not dropped) ----------

def test_workbook_level_flags_kept(imported_db):
    from app.models import DataQualityFlag

    wb_level = imported_db.query(DataQualityFlag).filter(DataQualityFlag.company_id.is_(None)).count()
    assert wb_level >= 10, "the '(workbook)' pseudo-ID rows must be stored with company_id NULL"


def test_quality_flags_dedup_across_versions(imported_db, seed_workbook):
    """Re-import must not duplicate flags when note text formatting evolves."""
    from app.models import DataQualityFlag
    from app.services.importer import _import_quality
    import openpyxl

    before = imported_db.query(DataQualityFlag).count()
    wb = openpyxl.load_workbook(seed_workbook, read_only=True, data_only=True)
    imported, wb_level, unresolved, dupes_removed = _import_quality(imported_db, wb)
    wb.close()
    after = imported_db.query(DataQualityFlag).count()
    assert after == before, f"re-import created {after - before} duplicate flags"


# ---------- Bank/insurer carve-out: providers must not fill corporate debt ----------

def test_insurer_total_debt_stays_null_after_provider_ingest(imported_db):
    """AGENTS.md: insurers with intentionally blank Total_Debt must stay NULL
    even when a provider reports a number. RY (a bank WITH owner debt) must
    equally keep its owner value untouched."""
    insurer = imported_db.get(Company, "US:AFL:US")
    assert insurer is not None and insurer.gics_sector == "Financials"
    seed_ins = _seed_row(imported_db, "US:AFL:US")
    assert seed_ins.total_debt is None  # owner left it blank on purpose

    stmt = AnnualStatement(
        fiscal_year=None, period_end=None, currency="USD", source="yfinance",
        fields={"Total_Debt": 5.0e10, "Gross_Profit": 1.0e10},
    )
    _ingest(imported_db, insurer, [stmt])
    seed_after = _seed_row(imported_db, "US:AFL:US")
    assert seed_after.total_debt is None, "insurer Total_Debt must stay NULL"
    assert seed_after.gross_profit is None, "insurer Gross_Profit must stay NULL"
    imported_db.rollback()

    bank = imported_db.get(Company, "CA:RY:TSX")
    assert bank is not None and bank.gics_sector == "Financials"
    assert _seed_row(imported_db, "CA:RY:TSX").total_debt == 545_439_000_000.0  # owner value intact


# ---------- Mapping / resolve ----------

def test_resolve_plain_and_suffixed():
    from app.services.mapping import resolve

    r = resolve("AAPL")
    assert r.company_id == "US:AAPL:US" and r.country == "US" and r.in_universe
    assert r.cik == 320193  # from universe_master.csv

    r = resolve("RY.TO")
    assert r.company_id == "CA:RY:TSX" and r.currency == "CAD" and r.in_universe
    assert r.yahoo_symbol == "RY.TO"

    r = resolve("US:MMM:US")
    assert r.company_id == "US:MMM:US" and r.in_universe and r.cik == 66740

    r = resolve("CA:RY:TSX")
    assert r.company_id == "CA:RY:TSX" and r.currency == "CAD"


def test_ingest_unknown_us_ticker_uses_mapping(imported_db, monkeypatch):
    """Unknown US ticker: mapping resolves via (stubbed) SEC list; ingest creates company + rows."""
    from app.providers.registry import ProviderRegistry
    from app.services.ingest import get_or_create_company
    from app.services.mapping import ResolveResult, build_ref

    class _StubRegistry(ProviderRegistry):
        def fetch_annual_statements(self, ref):
            return [
                AnnualStatement(fiscal_year=2023, period_end=date(2023, 12, 31), currency="USD",
                                source="sec_companyfacts", fields={"Revenue": 5_000_000.0}),
                AnnualStatement(fiscal_year=2024, period_end=date(2024, 12, 31), currency="USD",
                                source="sec_companyfacts", fields={"Revenue": 6_000_000.0}),
            ]

        def fetch_price(self, ref):
            return None

    monkeypatch.setattr("app.services.mapping.cik_for_unknown_us", lambda t: 1800 if t == "ABCD" else None)
    result = ResolveResult("US:ABCD:US", "ABCD", "US", "USD", "ABCD", 1800, False, "Unknown Test Co")
    ref = build_ref(result)
    assert ref.cik == 1800

    company = get_or_create_company(imported_db, ref.company_id, ref.ticker, ref.country, ref.currency, name=result.name)
    res = _ingest(imported_db, company, _StubRegistry().fetch_annual_statements(ref))
    imported_db.flush()
    assert res["created"] == 2
    assert imported_db.get(Company, "US:ABCD:US") is not None
    imported_db.rollback()


# ---------- API surface ----------

def test_financials_endpoint(client):
    r = client.get("/api/v1/companies/US:MMM:US/financials?years=10")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert body["items"][0]["source"] in ("Sector_Financials_Final_Owner.xlsx", "sec_companyfacts", "yfinance")


def test_financials_404(client):
    assert client.get("/api/v1/companies/US:NOPE:US/financials").status_code == 404


def test_resolve_endpoint(client):
    for q, expected in (("AAPL", "US:AAPL:US"), ("RY.TO", "CA:RY:TSX"), ("US:MMM:US", "US:MMM:US")):
        r = client.get(f"/api/v1/tickers/resolve?q={q}")
        assert r.status_code == 200
        assert r.json()["company_id"] == expected


def test_coverage_shape(client):
    r = client.get("/api/v1/coverage")
    assert r.status_code == 200
    body = r.json()
    for key in ("companies", "us", "ca", "companies_with_history", "pct_with_5plus_fy", "years_min", "years_max", "fixture_flag"):
        assert key in body
    assert body["companies"] == 720


def test_phase1_surface_intact(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/v1/stats").json()["companies"] == 720
    assert "not investment advice" in client.get("/api/v1/meta/disclaimer").json()["disclaimer"].lower()
