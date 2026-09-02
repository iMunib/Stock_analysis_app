"""Application configuration. Phase 1: env-based, no secrets required."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env if present (gitignored). Never fail when absent.
load_dotenv()

_DEFAULT_DB = "sqlite:///./data/app.db"

# Allow explicit env override; compose passes sqlite:////app/data/app.db
DATABASE_URL: str = os.environ.get("DATABASE_URL", _DEFAULT_DB)
SEC_USER_AGENT: str = os.environ.get("SEC_USER_AGENT", "InvestmentResearchApp contact@localhost")
OPENROUTER_API_KEY: str | None = os.environ.get("OPENROUTER_API_KEY") or None

APP_NAME = "Investment Research API"
APP_VERSION = "0.1.0-phase1"

DISCLAIMER = (
    "This is personal research software for a single local user. "
    "It is NOT investment advice, not a broker, and not a product. "
    "All data is a static research snapshot; verify everything before relying on it."
)

# Seed locations are probed in order by the importer.
_HERE = Path(__file__).resolve()
_SEED_CANDIDATES = [
    Path("/seed"),                          # docker mount (read-only)
    Path(os.environ.get("SEED_DIR", "")) if os.environ.get("SEED_DIR") else None,
    Path.cwd() / "seed",                    # run from repo root
    Path.cwd().parent / "seed",             # run from backend/
    _HERE.parents[2] / "seed",              # backend/app/config.py -> repo root
    _HERE.parents[1] / "seed",              # legacy fallback (backend/seed)
]
SEED_DIRS: list[Path] = [p for p in _SEED_CANDIDATES if p and p.is_dir()]

SEED_FILENAME = "Sector_Financials_Final_Owner.xlsx"


def find_seed_workbook() -> Path | None:
    for d in SEED_DIRS:
        p = d / SEED_FILENAME
        if p.is_file():
            return p
    return None
