"""History sanity (Phase 10 A): read-path filter for FY revenue outliers.

Detects scale/tag errors (e.g. MSFT FY2017-2019 showing $23-31B quarters vs $143B
annual) without deleting stored rows. One function, used by the dossier API and
scoring growth, so table / growth / bars always agree.
"""
from __future__ import annotations

import statistics
from typing import Any

SUSPECT_CODE = "SCALE_OR_TAG_SUSPECT"
LOW_FACTOR = 0.25
HIGH_FACTOR = 4.0


def _revenue(row: dict) -> float | None:
    v = row.get("revenue")
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f and f > 0 else None


def _baseline(values: list[float]) -> float | None:
    """Median of values >= the 40th percentile (median of all if n < 5)."""
    if not values:
        return None
    if len(values) < 5:
        return statistics.median(values)
    ordered = sorted(values)
    p40 = ordered[int(0.4 * (len(ordered) - 1))]
    strong = [v for v in ordered if v >= p40]
    return statistics.median(strong) if strong else None


def sanitize_history(rows: list[dict]) -> dict:
    """Split FY rows into table rows vs growth rows, with warnings.

    rows: dicts with at least fiscal_year and revenue (any extra fields pass through).
    Returns {rows_for_table, rows_for_growth, warnings}.

    - Table keeps every year, newest first; suspect years carry
      warning="excluded from growth — possible filing tag error".
    - Growth/bars use only non-suspect years.
    - A real hole (year with revenue NULL) stays a hole — never invented.
    """
    revs = [v for v in (_revenue(r) for r in rows) if v is not None]
    baseline = _baseline(revs)

    rows_for_table: list[dict] = []
    rows_for_growth: list[dict] = []
    warnings: list[dict] = []

    def _fy(r: dict):
        fy = r.get("fiscal_year")
        return fy if isinstance(fy, (int, float)) else -10**9  # NULL-safe sort (seed rows last)

    for r in sorted(rows, key=lambda r: (_fy(r), str(r.get("company_id", ""))), reverse=True):
        out = dict(r)
        rev = _revenue(r)
        suspect = False
        if rev is not None and baseline:
            if rev < LOW_FACTOR * baseline or rev > HIGH_FACTOR * baseline:
                suspect = True
        if suspect:
            out["quality_flag"] = SUSPECT_CODE
            out["warning"] = "excluded from growth — possible filing tag error"
            warnings.append({"fiscal_year": _fy(r), "revenue": rev, "code": SUSPECT_CODE, "baseline": baseline})
        elif rev is None:
            # a real hole stays a hole in growth rows too (never invented),
            # but no warning chip — it is simply not on file.
            pass
        else:
            rows_for_growth.append(out)
        rows_for_table.append(out)

    return {"rows_for_table": rows_for_table, "rows_for_growth": rows_for_growth, "warnings": warnings}
