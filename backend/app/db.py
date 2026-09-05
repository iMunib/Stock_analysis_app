"""SQLAlchemy 2 engine/session setup (SQLite-friendly)."""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL

_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    # Create the parent directory for file-based SQLite so first connect never fails.
    _sqlite_file = DATABASE_URL.split("///", 1)[-1]
    if _sqlite_file and not _sqlite_file.startswith(":memory:"):
        from pathlib import Path

        Path(_sqlite_file).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")   # 64 MB page cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        # Performance indexes — skip silently if tables don't exist yet (fresh DB / tests).
        for ddl in [
            "CREATE INDEX IF NOT EXISTS idx_snapshots_comp_fy "
            "ON financial_snapshots(company_id, fiscal_year, period_type)",
            "CREATE INDEX IF NOT EXISTS idx_snapshots_comp_date "
            "ON financial_snapshots(company_id, as_of_date)",
            "CREATE INDEX IF NOT EXISTS idx_scores_peer "
            "ON scores(peer_group, composite_score)",
            "CREATE INDEX IF NOT EXISTS idx_placements_comp_sheet "
            "ON placements(company_id, sheet_name)",
            "CREATE INDEX IF NOT EXISTS idx_companies_sector_cur "
            "ON companies(gics_sector, currency)",
        ]:
            try:
                cursor.execute(ddl)
            except Exception:  # noqa: BLE001 — table may not exist yet (test DB / first boot)
                pass
        cursor.close()


class Base(DeclarativeBase):
    """Declarative base for all Phase 1 models."""


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_session() -> Session:
    """Dependency-style session generator (also usable directly)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


get_db = get_session

