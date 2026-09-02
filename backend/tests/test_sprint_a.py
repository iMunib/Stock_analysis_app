"""Phase 10 A tests: history sanity + parser duration gate."""
from __future__ import annotations

import json
import pathlib
from datetime import date

from app.services.history_sanity import sanitize_history

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _rows(values):
    """Rows newest-first like the dossier API: (fiscal_year, revenue)."""
    return [{"fiscal_year": fy, "revenue": v} for fy, v in values]


def test_msft_like_series_excludes_quarters():
    """[331B, 281B, 245B, 212B, 143B, 30B, 26B, 23B] -> 30/26/23 excluded."""
    series = [
        (2026, 331_000_000_000), (2025, 281_000_000_000), (2024, 245_000_000_000),
        (2023, 212_000_000_000), (2022, 143_000_000_000),
        (2019, 30_000_000_000), (2018, 26_000_000_000), (2017, 23_000_000_000),
    ]
    out = sanitize_history(_rows(series))
    table_fy = [r["fiscal_year"] for r in out["rows_for_table"]]
    growth_fy = [r["fiscal_year"] for r in out["rows_for_growth"]]
    # table still lists all 8
    assert sorted(table_fy) == [2017, 2018, 2019, 2022, 2023, 2024, 2025, 2026]
    # growth excludes the three suspect years
    assert 2019 not in growth_fy and 2018 not in growth_fy and 2017 not in growth_fy
    assert 2022 in growth_fy and 2026 in growth_fy
    assert len(out["warnings"]) == 3
    for w in out["warnings"]:
        assert w["code"] == "SCALE_OR_TAG_SUSPECT"
    # table rows carry the warning chip
    for r in out["rows_for_table"]:
        if r["fiscal_year"] in (2017, 2018, 2019):
            assert r["quality_flag"] == "SCALE_OR_TAG_SUSPECT"
            assert "excluded from growth" in r["warning"]


def test_real_hole_stays_hole():
    series = [(2024, 245e9), (2023, 212e9), (2022, None), (2021, 168e9), (2020, 143e9)]
    out = sanitize_history(_rows(series))
    fy2022 = next(r for r in out["rows_for_table"] if r["fiscal_year"] == 2022)
    assert fy2022["revenue"] is None
    assert "quality_flag" not in fy2022  # a hole is a hole, never invented
    assert 2022 not in [r["fiscal_year"] for r in out["rows_for_growth"]]
    assert len(out["warnings"]) == 0


def test_healthy_series_untouched():
    series = [(2026, 400e9), (2025, 380e9), (2024, 360e9), (2023, 340e9), (2022, 300e9)]
    out = sanitize_history(_rows(series))
    assert len(out["rows_for_growth"]) == 5
    assert out["warnings"] == []


def test_parser_duration_gate_quarters_rejected():
    """EDGAR parse must reject 90-day (quarterly) facts that were stealing FY years."""
    from app.providers.edgar import parse_companyfacts

    payload = {
        "facts": {
            "dei": {},
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            # annual FY fact
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-07-01", "end": "2024-06-30", "val": 143_000_000_000},
                            # quarterly fact that previously slipped through as CY2024
                            {"form": "10-K", "fp": "FY", "frame": "CY2024Q1", "start": "2023-10-01", "end": "2023-12-31", "val": 30_000_000_000},
                        ]
                    }
                }
            }
        }
    }
    rows = parse_companyfacts(payload, expected_currency="USD")
    assert len(rows) == 1
    assert rows[0].fields["Revenue"] == 143_000_000_000.0
    assert rows[0].fiscal_year == 2024


def test_parser_prefers_365d_duplicate():
    from app.providers.edgar import parse_companyfacts

    payload = {
        "facts": {
            "dei": {},
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-07-01", "end": "2024-06-30", "val": 143_000_000_000},
                            # same year, shorter stub (351 days) — must NOT win
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-07-15", "end": "2024-06-30", "val": 90_000_000_000},
                        ]
                    }
                }
            }
        }
    }
    rows = parse_companyfacts(payload, expected_currency="USD")
    assert rows[0].fields["Revenue"] == 143_000_000_000.0


def test_live_db_msft_still_suspect_after_patch():
    """Read-path check: if the live DB still holds the bad 2019 row, dossier must flag it."""
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///../data/app.db")
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT fiscal_year, revenue FROM financial_snapshots WHERE company_id='US:MSFT:US' AND fiscal_year IS NOT NULL ORDER BY fiscal_year DESC LIMIT 12")
            ).all()
        if not rows:
            return  # no provider history (fresh db) — nothing to assert
        out = sanitize_history([{"fiscal_year": fy, "revenue": rev} for fy, rev in rows])
        fy2019 = next((r for r in out["rows_for_table"] if r["fiscal_year"] == 2019), None)
        if fy2019 and fy2019.get("revenue") and fy2019["revenue"] < 60e9:
            assert fy2019["quality_flag"] == "SCALE_OR_TAG_SUSPECT", "live 2019 must be flagged"
            assert 2019 not in [r["fiscal_year"] for r in out["rows_for_growth"]]
    finally:
        engine.dispose()
