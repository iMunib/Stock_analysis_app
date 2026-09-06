"""Workbook → SQLite importer (Phase 1).

Reads the frozen owner workbook and upserts companies, latest-FY snapshots,
placements, and data-quality flags. Idempotent: skips when the same source
(filename + mtime) is already imported unless --force.

Never converts currency, never backfills blanks (NULL stays NULL), never
invents fiscal years.
"""
from __future__ import annotations

import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import find_seed_workbook, SEED_FILENAME
from app.db import SessionLocal
from app.models import Company, DataQualityFlag, FinancialSnapshot, ImportRun, Placement, FinancialStatement, DerivedMetric, PeerBenchmark
from app.services.fundamentals import compute_snapshot_ratios, sync_snapshot_to_3nf
from app.services.ids import normalize_company_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=False,
)
logger = logging.getLogger("importer")

MONEY_COLS = [
    "Revenue", "Net_Income", "Diluted_EPS", "Gross_Profit", "Operating_Cash_Flow",
    "Capex", "Total_Debt", "Cash_ST_Investments", "Book_Equity", "Total_Assets",
    "Total_Liabilities", "EBIT", "EBITDA", "Interest_Expense", "FCF_Reported",
    "Free_Cash_Flow", "FCF_Calc", "NetDebt_Calc", "FCFMargin_Calc", "GrossMargin_Calc",
    "ROE_Calc", "ROA_Calc", "PE_Calc", "PB_Calc", "EV_Calc", "EV_to_EBITDA_Calc",
    "Price", "Shares_Snapshot", "Market_Cap", "TopLine_Alt",
    "CET1_Ratio", "CET1_Requirement_or_Target", "Total_Capital_Ratio",
    "Leverage_Ratio", "NIM_FY2025", "NIM_Q4_2025", "Efficiency_Ratio", "ROAA",
]
STR_SNAPSHOT_COLS = ["Price_Currency", "Price_AsOf", "CET1_Approach"]
PROV_COLS = ["Extraction_Status", "Source_Primary", "Fill_OK", "Membership_Flag", "Fiscal_Year_End"]

SNAPSHOT_FIELD_MAP = {
    "Revenue": "revenue", "Net_Income": "net_income", "Diluted_EPS": "diluted_eps",
    "Gross_Profit": "gross_profit", "Operating_Cash_Flow": "operating_cash_flow",
    "Capex": "capex", "Total_Debt": "total_debt", "Cash_ST_Investments": "cash_st_investments",
    "Book_Equity": "book_equity", "Total_Assets": "total_assets",
    "Total_Liabilities": "total_liabilities", "EBIT": "ebit", "EBITDA": "ebitda",
    "Interest_Expense": "interest_expense", "FCF_Reported": "fcf_reported",
    "Free_Cash_Flow": "free_cash_flow", "FCF_Calc": "fcf_calc",
    "NetDebt_Calc": "netdebt_calc", "FCFMargin_Calc": "fcfmargin_calc",
    "GrossMargin_Calc": "grossmargin_calc", "ROE_Calc": "roe_calc", "ROA_Calc": "roa_calc",
    "PE_Calc": "pe_calc", "PB_Calc": "pb_calc", "EV_Calc": "ev_calc",
    "EV_to_EBITDA_Calc": "ev_to_ebitda_calc", "Price": "price",
    "Shares_Snapshot": "shares_snapshot", "Market_Cap": "market_cap",
    "TopLine_Alt": "topline_alt", "CET1_Ratio": "cet1_ratio",
    "CET1_Requirement_or_Target": "cet1_requirement_or_target",
    "Total_Capital_Ratio": "total_capital_ratio", "Leverage_Ratio": "leverage_ratio",
    "NIM_FY2025": "nim_fy2025", "NIM_Q4_2025": "nim_q4_2025",
    "Efficiency_Ratio": "efficiency_ratio", "ROAA": "roaa",
}

FIXTURE_ROWS = [
    # (company_id, name, ticker, country, currency, gics_sector, gics_industry, custom_sheet, revenue, net_income, total_debt, cet1_ratio, nim)
    ("US:FIXT:US", "Fixture Industrials Inc", "FIXT", "US", "USD", "Industrials", "Industrial Conglomerates", "Industrials", 1_000_000_000, 100_000_000, 250_000_000, None, None),
    ("US:FIXT2:US", "Fixture Software Corp", "FIXT2", "US", "USD", "Information Technology", "Software", "Software", 500_000_000, 60_000_000, 50_000_000, None, None),
    ("CA:FIXT:TSX", "Fixture Energy Ltd", "FIXT", "CA", "CAD", "Energy", "Oil & Gas", "Oil_Gas_Producers", 800_000_000, 90_000_000, 300_000_000, None, None),
    ("CA:FIXT2:TSX", "Fixture Materials Inc", "FIXT2", "CA", "CAD", "Materials", "Gold", "Materials", 600_000_000, 40_000_000, None, None, None),
    ("CA:FIXTB:TSX", "Fixture Bank of Fixture", "FIXTB", "CA", "CAD", "Financials", "Banks", "Banks", None, 700_000_000, None, 0.13, 0.021),
]


def _cell(v):
    """Workbook cell → python value. Blanks/whitespace → None. Numbers pass through."""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s if s else None
    return v


def _num(v):
    v = _cell(v)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_asof(v) -> date | None:
    s = _cell(v)
    if s is None:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _yes(v) -> bool:
    return str(_cell(v) or "").strip().lower() in {"yes", "y", "true", "1"}


def _sheet_rows(wb, sheet_name: str) -> tuple[list[str], list[tuple]]:
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    data = [r for r in rows[1:] if r and any(_cell(v) is not None for v in r)]
    return header, data


def _row_get(header: list[str], row: tuple, name: str):
    try:
        idx = header.index(name)
    except ValueError:
        return None
    return row[idx] if idx < len(row) else None


def _import_companies(db: Session, wb, source_name: str) -> int:
    header, data = _sheet_rows(wb, "01_All_Companies")
    required = ["Company_ID", "Currency"]
    for req in required:
        if req not in header:
            raise ValueError(f"01_All_Companies missing required column {req!r}")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    imported = 0
    for row in data:
        raw_id = _cell(_row_get(header, row, "Company_ID"))
        company_id = normalize_company_id(raw_id) if raw_id else None
        if not company_id:
            continue
        company = db.get(Company, company_id)
        if company is None:
            company = Company(company_id=company_id)
            db.add(company)
        company.ticker = _cell(_row_get(header, row, "Primary_Ticker"))
        company.exchange = "US" if company_id.startswith("US:") else "TSX"
        company.country = _cell(_row_get(header, row, "Country_of_Listing"))
        company.name = _cell(_row_get(header, row, "Company_Name"))
        company.gics_sector = _cell(_row_get(header, row, "GICS_Sector"))
        company.gics_industry = _cell(_row_get(header, row, "GICS_Industry"))
        company.custom_industry_sheet = _cell(_row_get(header, row, "Custom_Industry_Sheet"))
        company.currency = _cell(_row_get(header, row, "Currency"))
        company.in_sp500 = _yes(_row_get(header, row, "In_SP500"))
        company.in_tsx_composite = _yes(_row_get(header, row, "In_TSX_Composite"))
        company.indexes = [
            label
            for label, flag in (("SP500", company.in_sp500), ("TSX_Composite", company.in_tsx_composite))
            if flag
        ]
        company.fiscal_year_end = _cell(_row_get(header, row, "Fiscal_Year_End"))
        company.extraction_status = _cell(_row_get(header, row, "Extraction_Status"))
        company.source_primary = _cell(_row_get(header, row, "Source_Primary"))
        company.imported_at = now

        # Upsert latest-FY snapshot (fiscal_year NULL by contract; unique key tolerates it).
        snap = db.execute(
            select(FinancialSnapshot).where(
                FinancialSnapshot.company_id == company_id,
                FinancialSnapshot.fiscal_year.is_(None),
                FinancialSnapshot.period_type == "FY",
            )
        ).scalar_one_or_none()
        if snap is None:
            snap = FinancialSnapshot(company_id=company_id, fiscal_year=None, period_type="FY")
            db.add(snap)
        snap.source = source_name
        snap.currency = company.currency
        snap.as_of_date = _parse_asof(_row_get(header, row, "Price_AsOf"))
        for col, attr in SNAPSHOT_FIELD_MAP.items():
            setattr(snap, attr, _num(_row_get(header, row, col)))
        snap.price_currency = _cell(_row_get(header, row, "Price_Currency"))
        snap.price_asof = _cell(_row_get(header, row, "Price_AsOf"))
        snap.cet1_approach = _cell(_row_get(header, row, "CET1_Approach"))
        for col in PROV_COLS:
            attr = {
                "Extraction_Status": "extraction_status",
                "Source_Primary": "source_primary",
                "Fill_OK": "fill_ok",
                "Membership_Flag": "membership_flag",
                "Fiscal_Year_End": "fiscal_year_end",
            }[col]
            if hasattr(snap, attr):
                setattr(snap, attr, _cell(_row_get(header, row, col)))
        compute_snapshot_ratios(snap, company)
        sync_snapshot_to_3nf(db, snap, company)
        imported += 1
    # Flush so later passes (placements, quality flags) can resolve companies via
    # db.get(): pending objects are not in the identity map until flushed.
    db.flush()
    return imported


def _import_placements(db: Session, wb) -> int:
    if "06_Placements" not in wb.sheetnames:
        return _import_placements_from_topic_tabs(db, wb)
    header, data = _sheet_rows(wb, "06_Placements")
    count = 0
    for row in data:
        raw_id = _cell(_row_get(header, row, "Company_ID"))
        company_id = normalize_company_id(raw_id) if raw_id else None
        if not company_id or db.get(Company, company_id) is None:
            continue
        primary = _cell(_row_get(header, row, "Primary_Sheet"))
        extras = _cell(_row_get(header, row, "Extra_Sheets")) or ""
        gics_sheet = _cell(_row_get(header, row, "GICS_Sheet"))
        seen: set[tuple[str, str]] = set()
        entries: list[tuple[str, str]] = []
        if primary:
            entries.append((str(primary), "Primary"))
        for extra in str(extras).split("|"):
            extra = extra.strip()
            if extra:
                entries.append((extra, "Extra"))
        if gics_sheet:
            entries.append((str(gics_sheet), "GICS"))
        for sheet_name, role in entries:
            key = (sheet_name, role)
            if key in seen:
                continue
            seen.add(key)
            existing = db.execute(
                select(Placement).where(
                    Placement.company_id == company_id,
                    Placement.sheet_name == sheet_name,
                    Placement.placement_role == role,
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(Placement(company_id=company_id, sheet_name=sheet_name, placement_role=role))
                count += 1
    return count


def _import_placements_from_topic_tabs(db: Session, wb) -> int:
    """Fallback: derive placements from topic tabs' Placement_Role column."""
    count = 0
    skip = {"00_README", "01_All_Companies", "02_Coverage", "03_Data_Quality",
            "04_Collisions", "05_Membership", "06_Placements"}
    for name in wb.sheetnames:
        if name in skip or name.startswith("GICS_"):
            continue
        header, data = _sheet_rows(wb, name)
        if "Company_ID" not in header:
            continue
        for row in data:
            raw_id = _cell(_row_get(header, row, "Company_ID"))
            company_id = normalize_company_id(raw_id) if raw_id else None
            if not company_id or db.get(Company, company_id) is None:
                continue
            role = str(_cell(_row_get(header, row, "Placement_Role")) or "Primary")
            existing = db.execute(
                select(Placement).where(
                    Placement.company_id == company_id,
                    Placement.sheet_name == name,
                    Placement.placement_role == role,
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(Placement(company_id=company_id, sheet_name=name, placement_role=role))
                count += 1
    return count


def _import_quality(db: Session, wb) -> tuple[int, int, int]:
    """Import 03_Data_Quality rows. Returns (imported, workbook_level, unresolved).

    '(workbook)' pseudo-ID rows are workbook-level notes stored with company_id
    NULL - audited and kept, never silently dropped. Truly unresolvable IDs are
    also kept with company_id NULL and counted as unresolved.
    """
    if "03_Data_Quality" not in wb.sheetnames:
        return 0, 0, 0
    header, data = _sheet_rows(wb, "03_Data_Quality")
    imported = workbook_level = unresolved = duplicates_removed = 0
    for row in data:
        raw_id = _cell(_row_get(header, row, "Company_ID"))
        company_id = normalize_company_id(raw_id) if raw_id else None
        if company_id is not None and db.get(Company, company_id) is None:
            company_id = None
        if company_id is None:
            if raw_id and raw_id.strip().lower() == "(workbook)":
                workbook_level += 1
            else:
                unresolved += 1
        field = _cell(_row_get(header, row, "Field"))
        code = _cell(_row_get(header, row, "Issue"))
        note_parts = []
        for col in ("Source_Attempted", "Retrieval_Date", "Resolution", "Notes"):
            v = _cell(_row_get(header, row, col))
            if v is not None:
                note_parts.append(f"{col}: {v}")
        note = " | ".join(note_parts) if note_parts else None
        if raw_id and str(raw_id) != str(company_id or ""):
            note = f"raw_id: {raw_id}" + (f" | {note}" if note else "")
        # Dedup on (company_id, field, code) - note text may evolve between code
        # versions; update the first row in place and absorb any duplicates left
        # by older buggy versions (self-healing re-import).
        key_filter = (
            DataQualityFlag.company_id.is_(None)
            if company_id is None
            else DataQualityFlag.company_id == company_id
        )
        matches = db.execute(
            select(DataQualityFlag)
            .where(key_filter, DataQualityFlag.field == field, DataQualityFlag.code == code)
            .order_by(DataQualityFlag.id)
        ).scalars().all()
        if not matches:
            db.add(DataQualityFlag(company_id=company_id, field=field, code=code, note=note))
            imported += 1
        else:
            first = matches[0]
            if first.note != note:
                first.note = note
                imported += 1
            for extra in matches[1:]:
                db.delete(extra)
                duplicates_removed += 1
    return imported, workbook_level, unresolved, duplicates_removed


def _build_fixture_workbook(tmp_path: Path) -> Path:
    """Synthetic 5-row fixture so the app stays runnable when the seed is missing."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "01_All_Companies"
    header = [
        "Company_ID", "Company_Name", "Primary_Ticker", "Country_of_Listing", "Currency",
        "GICS_Sector", "GICS_Industry", "Custom_Industry_Sheet", "Exchange", "In_SP500",
        "In_TSX_Composite", "Extraction_Status", "Source_Primary", "Fiscal_Year_End",
        "Revenue", "Net_Income", "Diluted_EPS", "Gross_Profit", "Operating_Cash_Flow",
        "Capex", "Total_Debt", "Cash_ST_Investments", "Book_Equity", "Total_Assets",
        "Total_Liabilities", "EBIT", "EBITDA", "Interest_Expense", "FCF_Reported",
        "Free_Cash_Flow", "FCF_Calc", "NetDebt_Calc", "FCFMargin_Calc", "GrossMargin_Calc",
        "ROE_Calc", "ROA_Calc", "Price", "Price_Currency", "Price_AsOf",
        "Shares_Snapshot", "Market_Cap", "PE_Calc", "PB_Calc", "EV_Calc",
        "EV_to_EBITDA_Calc", "CET1_Ratio", "CET1_Approach", "CET1_Requirement_or_Target",
        "Total_Capital_Ratio", "Leverage_Ratio", "NIM_FY2025", "NIM_Q4_2025",
        "Efficiency_Ratio", "ROAA", "Fill_OK", "Membership_Flag", "TopLine_Alt",
    ]
    ws.append(header)
    for r in FIXTURE_ROWS:
        (cid, name, ticker, country, currency, sector, industry, sheet, revenue, ni, debt, cet1, nim) = r
        row = {h: None for h in header}
        row.update({
            "Company_ID": cid, "Company_Name": name, "Primary_Ticker": ticker,
            "Country_of_Listing": country, "Currency": currency, "GICS_Sector": sector,
            "GICS_Industry": industry, "Custom_Industry_Sheet": sheet,
            "In_SP500": "Yes" if country == "US" else "No",
            "In_TSX_Composite": "Yes" if country == "CA" else "No",
            "Extraction_Status": "FIXTURE", "Source_Primary": "SYNTHETIC",
            "Revenue": revenue, "Net_Income": ni, "Total_Debt": debt,
            "CET1_Ratio": cet1, "NIM_FY2025": nim,
        })
        ws.append([row[h] for h in header])
    wb.save(tmp_path)
    return tmp_path


def run_import(force: bool = False, seed_path: Path | None = None) -> dict:
    """Main entry. Returns a summary dict. Database is primary durable operational store."""
    db: Session = SessionLocal()
    try:
        # Check if operational database already contains companies
        existing_companies = db.execute(select(Company.company_id)).scalars().all()
        if existing_companies and seed_path is None and not force:
            logger.info(
                "Operational SQLite database already populated with %d companies. "
                "Excel seed reading skipped (database is primary durable store).",
                len(existing_companies),
            )
            return {"status": "skipped", "companies": len(existing_companies), "source": "database_operational"}

        fixture = False
        path = seed_path or find_seed_workbook()
        if path is None:
            if existing_companies:
                logger.info("Seed workbook redacted/archived; SQLite database is operational with %d companies.", len(existing_companies))
                return {"status": "skipped", "companies": len(existing_companies), "source": "database_operational"}
            logger.warning("FAIL: seed workbook missing - falling back to synthetic fixture")
            fixture = True
            fixture_dir = Path("./data").resolve()
            fixture_dir.mkdir(parents=True, exist_ok=True)
            path = _build_fixture_workbook(fixture_dir / "fixture_seed.xlsx")
            logger.info("Importing synthetic 5-row fixture instead: %s", path)

        stat = path.stat()
        source_name = path.name
        source_mtime = stat.st_mtime

        import openpyxl

        last = db.execute(
            select(ImportRun)
            .where(ImportRun.source_filename == source_name, ImportRun.source_mtime == source_mtime)
            .order_by(ImportRun.id.desc())
        ).scalars().first()
        if last is not None and not force and not fixture:
            logger.info("Skip: %s (mtime %s) already imported at %s. Use --force to re-import.", source_name, source_mtime, last.imported_at)
            companies = db.execute(select(Company.company_id)).scalars().all()
            return {"status": "skipped", "companies": len(companies), "source": source_name}

        count = _import_companies(db, openpyxl.load_workbook(path, read_only=True, data_only=True), source_name)
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        placements = _import_placements(db, wb)
        flags, workbook_level, unresolved, dupes_removed = _import_quality(db, wb)
        db.add(ImportRun(
            source_filename=source_name,
            source_mtime=source_mtime,
            imported_at=datetime.now(timezone.utc).replace(tzinfo=None),
            companies_imported=count,
            fixture=fixture,
            note="synthetic fixture" if fixture else None,
        ))
        db.commit()
        logger.info(
            "Imported %d companies, %d placements, %d quality flags "
            "(workbook-level: %d, unresolved: %d, dupes removed: %d) from %s",
            count, placements, flags, workbook_level, unresolved, dupes_removed, source_name,
        )
        return {
            "status": "fixture" if fixture else "imported",
            "companies": count,
            "placements": placements,
            "flags": flags,
            "workbook_level_flags": workbook_level,
            "unresolved_flags": unresolved,
            "source": source_name,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force" in sys.argv
    run_import(force=force)