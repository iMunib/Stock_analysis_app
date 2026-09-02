"""AAOIFI-style halal FLAG (informational, never a filter, never a fatwa).

Approximation documented in docs/SCORING_SPEC.md:
- Activity screen: Banks / Insurance / Credit_Services / conventional Financials,
  alcohol, tobacco, gambling, weapons, pork, adult entertainment -> not_halal.
- Financial ratios vs Market_Cap (AAOIFI-style 30/30/5): interest-bearing debt,
  cash+ST investments; impure income stays unknown unless interest income exists.
- Missing inputs -> unknown. Never halal_candidate by default.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

METHOD = "aaoifi_style_v1"

ACTIVITY_FAIL_SHEET = {
    "banks", "insurance", "credit_services",
    "alcohol", "tobacco", "gambling", "weapons", "defense", "pork", "adult",
}
ACTIVITY_FAIL_SECTOR = {"financials"}
ACTIVITY_KEYWORDS = [
    "alcohol", "brewer", "distiller", "tobacco", "casino", "gambl",
    "weapon", "defen", "arms", "adult", "pork",
]

DEBT_TO_MCAP_LIMIT = 0.30
CASH_TO_MCAP_LIMIT = 0.30


def _f(x: Any) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def evaluate_halal(company: dict, snap: dict | None) -> dict:
    """Pure evaluation. company: {gics_sector, custom_industry_sheet, name}; snap: snapshot dict."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    tests: dict[str, Any] = {}

    sector = (company.get("gics_sector") or "").strip().lower()
    sheet = (company.get("custom_industry_sheet") or "").strip().lower()
    name = (company.get("name") or "").lower()

    activity_fail = sheet in ACTIVITY_FAIL_SHEET or sector in ACTIVITY_FAIL_SECTOR or any(k in name for k in ACTIVITY_KEYWORDS)
    tests["activity_screen"] = {
        "result": "fail" if activity_fail else "pass",
        "basis": {"gics_sector": sector or None, "custom_industry_sheet": sheet or None, "keyword_hit": next((k for k in ACTIVITY_KEYWORDS if k in name), None)},
    }
    if activity_fail:
        return {
            "status": "not_halal",
            "tests": tests,
            "method": METHOD,
            "computed_at": now,
            "note": "Business-activity screen failed (banks/insurers/conventional financials fail activity even if ratios look fine).",
        }

    if snap is None:
        tests["financial_ratios"] = {"result": "unknown", "reason": "no_snapshot"}
        return {"status": "unknown", "tests": tests, "method": METHOD, "computed_at": now,
                "note": "No snapshot available; ratios unknown."}

    mcap = _f(snap.get("market_cap"))
    if mcap is None or mcap <= 0:
        tests["financial_ratios"] = {"result": "unknown", "reason": "market_cap_missing"}
        return {"status": "unknown", "tests": tests, "method": METHOD, "computed_at": now,
                "note": "Market cap missing; AAOIFI-style ratios cannot be computed. Unknown, never halal by default."}

    ratio_results: dict[str, Any] = {}
    overall_unknown = False

    debt = _f(snap.get("total_debt"))
    if debt is None:
        ratio_results["debt_to_mcap"] = {"result": "unknown", "reason": "debt_null (owner blank or unsourced)"}
        overall_unknown = True
    else:
        ratio = debt / mcap
        ratio_results["debt_to_mcap"] = {"ratio": round(ratio, 4), "limit": DEBT_TO_MCAP_LIMIT,
                                         "result": "pass" if ratio < DEBT_TO_MCAP_LIMIT else "fail"}

    cash = _f(snap.get("cash_st_investments"))
    if cash is None:
        ratio_results["cash_to_mcap"] = {"result": "unknown", "reason": "cash_null"}
        overall_unknown = True
    else:
        ratio = cash / mcap
        ratio_results["cash_to_mcap"] = {"ratio": round(ratio, 4), "limit": CASH_TO_MCAP_LIMIT,
                                         "result": "pass" if ratio < CASH_TO_MCAP_LIMIT else "fail"}

    ratio_results["impure_income"] = {
        "result": "unknown",
        "reason": "interest income not sourced in Phase 1-3; cannot certify impure income < 5%",
    }
    overall_unknown = True  # impure income unknown -> never pass as halal

    tests["financial_ratios"] = {"result": "unknown" if overall_unknown else "pass", "ratios": ratio_results}

    hard_fail = any(r.get("result") == "fail" for r in ratio_results.values() if isinstance(r, dict))
    if hard_fail:
        status = "not_halal"
        note = "One or more AAOIFI-style ratio limits exceeded."
    elif overall_unknown:
        status = "unknown"
        note = "Activity screen passed but ratio inputs are incomplete; unknown, never halal by default."
    else:
        status = "halal_candidate"
        note = "Activity and ratio screens passed (approximation, not a fatwa)."
    return {"status": status, "tests": tests, "method": METHOD, "computed_at": now, "note": note}
