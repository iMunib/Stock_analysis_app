"""Pytest fixtures: isolated test DB + one real-workbook import per session."""
from __future__ import annotations

import os
import pathlib

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
os.chdir(BACKEND_DIR)

# Isolated test database BEFORE app modules are imported (engine binds at import).
TEST_DB = BACKEND_DIR / ".pytest_app.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
# Phase 6A: disable the lifespan job worker in tests; drive process_one() manually.
os.environ["JOBS_WORKER_DISABLED"] = "1"

from app.db import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: F401,E402
from app.config import find_seed_workbook  # noqa: E402
from app.services.importer import run_import  # noqa: E402


@pytest.fixture(scope="session")
def seed_workbook():
    wb = find_seed_workbook()
    if wb is None:
        pytest.fail("seed workbook missing — Phase 1 requires it for real-data tests")
    return wb


@pytest.fixture(scope="session")
def imported_db(seed_workbook):
    # Workstream A: create_all is reserved for isolated, ephemeral test DBs where
    # Alembic is explicitly bypassed. Production never calls it.
    Base.metadata.create_all(bind=engine)
    # Tests that trigger the app lifespan require a valid migration stamp
    # (A2 guard) — stamp the ephemeral DB to head without running migrations.
    from alembic import command as _alembic_command
    from alembic.config import Config as _AlembicConfig

    _cfg = _AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
    _cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    _cfg.set_main_option("sqlalchemy.url", f"sqlite:///{TEST_DB.as_posix()}")
    _alembic_command.stamp(_cfg, "head")
    run_import(force=True, seed_path=seed_workbook)
    yield SessionLocal()
    SessionLocal.close_all()
    engine.dispose()
    for suffix in ("", "-wal", "-shm"):
        p = pathlib.Path(str(TEST_DB) + suffix)
        if p.exists():
            p.unlink()


@pytest.fixture()
def client(imported_db):
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
