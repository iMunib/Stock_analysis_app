"""AAOIFI-style halal FLAG (informational, never a filter, never a fatwa).

Approximation documented in docs/SCORING_SPEC.md:
- Activity screen: Banks / Insurance / Credit_Services / conventional Financials,
  alcohol, tobacco, gambling, weapons, pork, adult entertainment -> not_halal.
- Financial ratios vs Market_Cap (AAOIFI-style 30/30/5): interest-bearing debt,
  cash+ST investments; impure income stays unknown unless interest income exists.
- Missing inputs -> unknown. Never halal_candidate by default.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHOD = "aaoifi_style_v1"

ACTIVITY_FAIL_SHEET = {
    "banks",
    "insurance",
    "credit_services",
    "alcohol",
    "tobacco",
    "gambling",
    "weapons",
    "defense",
    "pork",
    "adult",
}
ACTIVITY_FAIL_SECTOR = {"financials"}
ACTIVITY_KEYWORDS = [
    "alcohol",
    "brewer",
    "distiller",
    "tobacco",
    "casino",
    "gambl",
    "weapon",
    "defen",
    "arms",
    "adult",
    "pork",
]

DEBT_TO_MCAP_LIMIT = 0.30
CASH_TO_MCAP_LIMIT = 0.30
IMPURE_INCOME_LIMIT = 0.05


def _to_float_optional(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric == numeric else None


_f = _to_float_optional


def _is_activity_failure(sector: str, sheet: str, company_name: str) -> tuple[bool, str | None]:
    keyword_hit = next((k for k in ACTIVITY_KEYWORDS if k in company_name), None)
    failed = sheet in ACTIVITY_FAIL_SHEET or sector in ACTIVITY_FAIL_SECTOR or keyword_hit is not None
    return failed, keyword_hit


def _evaluate_debt_ratio(snap: dict[str, Any], market_cap: float) -> tuple[dict[str, Any], bool]:
    debt = _to_float_optional(snap.get("total_debt"))
    if debt is None:
        return {"result": "unknown", "reason": "debt_null (owner blank or unsourced)"}, True
    ratio = debt / market_cap
    return {"ratio": round(ratio, 4), "limit": DEBT_TO_MCAP_LIMIT, "result": "pass" if ratio < DEBT_TO_MCAP_LIMIT else "fail"}, False


def _evaluate_cash_ratio(snap: dict[str, Any], market_cap: float) -> tuple[dict[str, Any], bool]:
    cash = _to_float_optional(snap.get("cash_st_investments"))
    if cash is None:
        return {"result": "unknown", "reason": "cash_null"}, True
    ratio = cash / market_cap
    return {"ratio": round(ratio, 4), "limit": CASH_TO_MCAP_LIMIT, "result": "pass" if ratio < CASH_TO_MCAP_LIMIT else "fail"}, False


def _evaluate_impure_income_ratio(snap: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    interest_income = _to_float_optional(snap.get("interest_income"))
    revenue = _to_float_optional(snap.get("revenue"))
    if interest_income is None:
        return {
            "result": "unknown",
            "reason": "interest income missing from filings; cannot certify impure income <= 5%",
        }, True
    if revenue is None or revenue <= 0:
        return {
            "result": "unknown",
            "reason": "revenue missing or non-positive; cannot compute impure income ratio",
        }, True
    impure_ratio = max(0.0, interest_income) / revenue
    return {
        "ratio": round(impure_ratio, 4),
        "limit": IMPURE_INCOME_LIMIT,
        "result": "pass" if impure_ratio <= IMPURE_INCOME_LIMIT else "fail",
    }, False


def evaluate_halal(company: dict[str, Any], snap: dict[str, Any] | None) -> dict[str, Any]:
    """Pure evaluation. company: {gics_sector, custom_industry_sheet, name}; snap: snapshot dict."""
    now = datetime.now(UTC).replace(tzinfo=None)
    tests: dict[str, Any] = {}

    sector = (company.get("gics_sector") or "").strip().lower()
    sheet = (company.get("custom_industry_sheet") or "").strip().lower()
    company_name = (company.get("name") or "").lower()

    activity_failed, keyword_hit = _is_activity_failure(sector, sheet, company_name)
    tests["activity_screen"] = {
        "result": "fail" if activity_failed else "pass",
        "basis": {"gics_sector": sector or None, "custom_industry_sheet": sheet or None, "keyword_hit": keyword_hit},
    }
    if activity_failed:
        return {
            "status": "not_halal",
            "tests": tests,
            "method": METHOD,
            "computed_at": now,
            "note": "Business-activity screen failed (banks/insurers/conventional financials fail activity even if ratios look fine).",
        }

    if snap is None:
        tests["financial_ratios"] = {"result": "unknown", "reason": "no_snapshot"}
        return {
            "status": "unknown",
            "tests": tests,
            "method": METHOD,
            "computed_at": now,
            "note": "No snapshot available; ratios unknown.",
        }

    market_cap = _to_float_optional(snap.get("market_cap"))
    if market_cap is None or market_cap <= 0:
        tests["financial_ratios"] = {"result": "unknown", "reason": "market_cap_missing"}
        return {
            "status": "unknown",
            "tests": tests,
            "method": METHOD,
            "computed_at": now,
            "note": "Market cap missing; AAOIFI-style ratios cannot be computed. Unknown, never halal by default.",
        }

    ratio_results: dict[str, Any] = {}
    unknown_flags: list[bool] = []

    debt_result, debt_unknown = _evaluate_debt_ratio(snap, market_cap)
    ratio_results["debt_to_mcap"] = debt_result
    unknown_flags.append(debt_unknown)

    cash_result, cash_unknown = _evaluate_cash_ratio(snap, market_cap)
    ratio_results["cash_to_mcap"] = cash_result
    unknown_flags.append(cash_unknown)

    income_result, income_unknown = _evaluate_impure_income_ratio(snap)
    ratio_results["impure_income"] = income_result
    unknown_flags.append(income_unknown)

    overall_unknown = any(unknown_flags)
    tests["financial_ratios"] = {"result": "unknown" if overall_unknown else "pass", "ratios": ratio_results}

    hard_fail = any(result.get("result") == "fail" for result in ratio_results.values() if isinstance(result, dict))
    if hard_fail:
        status = "not_halal"
        note = "One or more AAOIFI-style ratio limits exceeded."
    elif overall_unknown:
        status = "unknown"
        note = "Activity screen passed but ratio inputs are incomplete; unknown, never halal by default."
    else:
        status = "halal_candidate"
        note = "Activity and ratio screens passed (approximation, not a fatwa)."
    return {
        "status": status,
        "halal_candidate": status == "halal_candidate",
        "tests": tests,
        "method": METHOD,
        "computed_at": now,
        "note": note,
    }
