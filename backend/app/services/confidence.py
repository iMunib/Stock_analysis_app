"""Deterministic data-confidence computation.

Rules are documented in docs/METRIC_CATALOG.md and here. All thresholds are
conservative and deterministic — no AI, no estimation.

Returned DataConfidence object is computed at request time from stored data;
it is NOT stored in the database (avoids stale cache issues).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone


@dataclass
class DataConfidence:
    """Read-only confidence summary for a company's data quality."""

    # Individual freshness signals: "green" | "amber" | "red" | "unknown"
    price_freshness: str = "unknown"
    financial_freshness: str = "unknown"

    # Depth indicators
    history_depth: int = 0          # number of FY rows with non-null revenue
    coverage_pillars: int = 0       # 0–4 scoring pillars computed
    peer_count: int = 0

    # Cross-currency flag
    currency_aligned: bool | None = None  # True = match, False = mismatch, None = unknown

    # Overall roll-up
    confidence: str = "Insufficient"   # "High" | "Medium" | "Low" | "Insufficient"
    reasons: list[str] = field(default_factory=list)


def _price_freshness(price_asof: str | date | None) -> tuple[str, list[str]]:
    """
    Rules:
        price asof <= 1 trading day → green
        2–7 days → amber
        > 7 days or unknown → red/unknown
    """
    reasons: list[str] = []
    if price_asof is None:
        reasons.append("Price as-of date not recorded")
        return "unknown", reasons

    if isinstance(price_asof, str):
        try:
            d = date.fromisoformat(str(price_asof)[:10])
        except (ValueError, TypeError):
            reasons.append("Price as-of date not parseable")
            return "unknown", reasons
    elif isinstance(price_asof, (date, datetime)):
        d = price_asof if isinstance(price_asof, date) else price_asof.date()
    else:
        reasons.append("Price as-of date not parseable")
        return "unknown", reasons

    today = datetime.now(timezone.utc).date()
    delta = (today - d).days
    if delta <= 1:
        return "green", reasons
    elif delta <= 7:
        reasons.append(f"Price is {delta} days old (last updated {d})")
        return "amber", reasons
    else:
        reasons.append(f"Price is {delta} days stale (last updated {d})")
        return "red", reasons


def _financial_freshness(period_end: date | str | None, fetched_at: datetime | None) -> tuple[str, list[str]]:
    """
    Financial freshness is based on the statement period end date vs today.
    Rules (approximate):
        period_end within 15 months → green (typical annual filing lag)
        15–24 months → amber
        > 24 months → red
        unknown → unknown
    """
    reasons: list[str] = []
    if period_end is None:
        reasons.append("Statement period end not recorded")
        return "unknown", reasons

    if isinstance(period_end, str):
        try:
            d = date.fromisoformat(str(period_end)[:10])
        except (ValueError, TypeError):
            reasons.append("Statement period end not parseable")
            return "unknown", reasons
    elif isinstance(period_end, (date, datetime)):
        d = period_end if isinstance(period_end, date) else period_end.date()
    else:
        reasons.append("Statement period end not parseable")
        return "unknown", reasons

    today = datetime.now(timezone.utc).date()
    months = (today.year - d.year) * 12 + (today.month - d.month)
    if months <= 15:
        return "green", reasons
    elif months <= 24:
        reasons.append(f"Latest statement is {months} months old (period end {d})")
        return "amber", reasons
    else:
        reasons.append(f"Latest statement is {months} months old — may be very stale (period end {d})")
        return "red", reasons


def _history_depth(history_rows: list[dict]) -> int:
    """Count FY rows with non-null revenue."""
    return sum(1 for r in history_rows if r.get("revenue") is not None and r.get("fiscal_year") is not None)


def compute_confidence(
    *,
    price_asof: str | date | None = None,
    statement_period_end: date | str | None = None,
    fetched_at: datetime | None = None,
    history_rows: list[dict] | None = None,
    coverage_pillars: int = 0,
    peer_count: int = 0,
    reporting_currency: str | None = None,
    trading_currency: str | None = None,
) -> DataConfidence:
    """Compute DataConfidence from stored fields. All rules are deterministic."""
    c = DataConfidence()
    c.coverage_pillars = coverage_pillars
    c.peer_count = peer_count

    # Price freshness
    c.price_freshness, p_reasons = _price_freshness(price_asof)
    c.reasons.extend(p_reasons)

    # Financial freshness
    c.financial_freshness, f_reasons = _financial_freshness(statement_period_end, fetched_at)
    c.reasons.extend(f_reasons)

    # History depth
    c.history_depth = _history_depth(history_rows or [])

    # Currency alignment
    if reporting_currency and trading_currency:
        rc = reporting_currency.upper().strip()
        tc = trading_currency.upper().strip()
        if rc == tc:
            c.currency_aligned = True
        else:
            c.currency_aligned = False
            c.reasons.append(f"Reporting currency ({rc}) differs from trading currency ({tc}) — price ratios suppressed")
    else:
        c.currency_aligned = None

    # Coverage penalty note
    if coverage_pillars < 2:
        c.reasons.append(f"Only {coverage_pillars}/4 scoring pillars available — composite is low-confidence")
    elif coverage_pillars < 4:
        c.reasons.append(f"{coverage_pillars}/4 scoring pillars available — composite has coverage penalty applied")

    # History depth note
    if c.history_depth == 0:
        c.reasons.append("No annual statement history in database — add ticker to fetch")
    elif c.history_depth < 3:
        c.reasons.append(f"Only {c.history_depth} year(s) of annual history — Growth pillar may be blank")

    # Peer count note
    if peer_count <= 1:
        c.reasons.append("Peer set has ≤1 member — Value score uses broad universe fallback")

    # Overall roll-up
    freshness_scores = {
        "green": 3,
        "amber": 2,
        "red": 1,
        "unknown": 0,
    }
    pf = freshness_scores.get(c.price_freshness, 0)
    ff = freshness_scores.get(c.financial_freshness, 0)

    if coverage_pillars == 0 or c.history_depth == 0:
        c.confidence = "Insufficient"
    elif (pf >= 2 and ff >= 3 and c.history_depth >= 3 and coverage_pillars >= 3
          and c.currency_aligned is not False):
        c.confidence = "High"
    elif (pf >= 1 and ff >= 2 and c.history_depth >= 1 and coverage_pillars >= 2):
        c.confidence = "Medium"
    elif coverage_pillars >= 1:
        c.confidence = "Low"
    else:
        c.confidence = "Insufficient"

    return c


def confidence_to_dict(c: DataConfidence) -> dict:
    return {
        "price_freshness": c.price_freshness,
        "financial_freshness": c.financial_freshness,
        "history_depth": c.history_depth,
        "coverage_pillars": c.coverage_pillars,
        "peer_count": c.peer_count,
        "currency_aligned": c.currency_aligned,
        "confidence": c.confidence,
        "reasons": c.reasons,
    }
