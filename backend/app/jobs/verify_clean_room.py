"""Clean-room verification runner (Trust sprint, Workstream A3).

Proves the repository can go from ZERO to a served research API using only
Alembic migrations + the real importer — no create_all, no shortcuts.

Usage:
    python -m app.jobs.verify_clean_room

Exit code 0 = clean room verified; non-zero with a printed failure reason.
"""
from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
SEED = BACKEND_DIR.parent / "seed" / "Sector_Financials_Final_Owner.xlsx"

REQUIRED_TABLES = {
    "companies",
    "financial_snapshots",
    "financial_snapshots_ttm",
    "valuation_reverse_dcf",
    "screener_presets",
    "scores",
    "halal_flags",
    "jobs",
    "company_profiles",
    "company_key_stats",
    "llm_cache",
    "alembic_version",
}
REQUIRED_INDEXES = {
    "ix_companies_ticker",  # representative index; presence checked loosely below
}


def _fail(msg: str) -> None:
    print(f"CLEAN-ROOM FAIL: {msg}")
    sys.exit(1)


def _step(msg: str) -> None:
    print(f"[clean-room] {msg}")


def main() -> int:
    _step("booting isolated temporary SQLite database")
    tmp = tempfile.TemporaryDirectory(prefix="clean_room_")
    try:
        rc = _run(Path(tmp.name))
    finally:
        # Dispose engines bound to the temp DB BEFORE removing the dir
        # (SQLite WAL keeps handles; Windows cannot unlink open files).
        import gc

        try:
            from app.db import engine as _boot_engine

            _boot_engine.dispose()
        except Exception:
            pass
        gc.collect()
        tmp.cleanup()
    if rc == 0:
        print("CLEAN-ROOM OK: zero -> migrated -> imported (720/1506) -> scored -> served")
    return rc


def _run(db_dir: Path) -> int:
    db_path = db_dir / "clean_room.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    # Import app modules AFTER the env var is set (engine binds at import).
    for mod in [m for m in list(sys.modules) if m.startswith("app.")]:
        del sys.modules[mod]

    # 1. Migrate from zero: alembic upgrade head (programmatic).
    from alembic import command as alembic_command
    from alembic.config import Config as AlembicConfig

    _step("alembic upgrade head from empty file")
    cfg = AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    alembic_command.upgrade(cfg, "head")

    # 2. Inspect the generated schema.
    import sqlite3

    con = sqlite3.connect(db_path)
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = REQUIRED_TABLES - tables
    if missing:
        _fail(f"migrated schema missing tables: {sorted(missing)}")
    indexes = {
        r[0]
        for r in con.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    }
    idx_missing = REQUIRED_INDEXES - indexes
    if idx_missing:
        _fail(f"migrated schema missing indexes: {sorted(idx_missing)}")
    stamp = con.execute("SELECT version_num FROM alembic_version").fetchall()
    con.close()
    _step(f"schema verified ({len(tables)} tables), stamp={stamp}")

    # 3. Real importer against the owner workbook.
    if not SEED.exists():
        _fail(f"seed workbook missing: {SEED}")
    _step("running real importer on owner workbook")
    from app.services.importer import run_import

    run_import(force=True, seed_path=SEED)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()

    from app.models import Company, DataQualityFlag, Placement

    companies = db.query(Company).count()
    placements = db.query(Placement).count()
    flags = db.query(DataQualityFlag).count()
    usd = db.query(Company).filter(Company.currency == "USD").count()
    cad = db.query(Company).filter(Company.currency == "CAD").count()
    _step(
        f"imported: {companies} companies ({usd} USD / {cad} CAD), "
        f"{placements} placements, {flags} quality flags"
    )
    if companies != 720:
        _fail(f"expected 720 companies, got {companies}")
    if placements != 1506:
        _fail(f"expected 1,506 placements, got {placements}")
    if flags <= 0:
        _fail("quality flags missing after import")

    # 4. Scoring batch for one USD + one CAD company.
    _step("scoring US:MSFT:US (USD) and CA:RY:TSX (CAD)")
    from app.services.scoring_service import recompute

    for cid in ("US:MSFT:US", "CA:RY:TSX"):
        out = recompute(db, company_id=cid)
        if not out or out.get("scored", 0) < 1:
            _fail(f"scoring failed for {cid}: {out}")

    # 5. FastAPI smoke against the fresh DB (lifespan guard included).
    _step("TestClient smoke: /health, /api/v1/stats, MSFT dossier")
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        r = client.get("/health")
        if r.status_code != 200:
            _fail(f"/health -> {r.status_code}")
        r = client.get("/api/v1/stats")
        if r.status_code != 200:
            _fail(f"/api/v1/stats -> {r.status_code}")
        r = client.get("/api/v1/companies/US:MSFT:US/dossier")
        if r.status_code != 200:
            _fail(f"MSFT dossier -> {r.status_code}: {r.text[:200]}")
        dossier = r.json()
        if dossier["identity"]["company_id"] != "US:MSFT:US":
            _fail("dossier identity mismatch")

    db.close()
    engine.dispose()
    _step("teardown complete")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        print("CLEAN-ROOM FAIL: unexpected exception")
        sys.exit(1)
