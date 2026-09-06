"""SQLAlchemy 2 engine/session setup (SQLite-friendly)."""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import DATABASE_URL

_connect_args = {}
_engine_kwargs: dict = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    # SQLite + WAL: NullPool avoids QueuePool exhaustion under concurrent dossier/valuation/forensic fan-out.
    # File-based SQLite has no true connection limit; pooling only adds contention.
    _engine_kwargs["poolclass"] = NullPool
    # Create the parent directory for file-based SQLite so first connect never fails.
    _sqlite_file = DATABASE_URL.split("///", 1)[-1]
    if _sqlite_file and not _sqlite_file.startswith(":memory:"):
        from pathlib import Path

        Path(_sqlite_file).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=60000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")   # 64 MB page cache
            cursor.execute("PRAGMA temp_store=MEMORY")
        except Exception:
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

