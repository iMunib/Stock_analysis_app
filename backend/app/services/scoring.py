"""Deterministic Phase 3 scoring engine (method_version=v1).

Design locked in docs/SCORING_SPEC.md:
    composite = 0.30*Quality + 0.25*Value + 0.25*Growth + 0.20*Risk (Risk inverted)

Missing pillars are NULL (never imputed); coverage penalty applies:
    4 pillars -> full; 3 -> *0.92; 2 -> *0.80; 1 -> *0.65; 0 -> NULL + insufficient_data.

Pure functions over dicts: no network, no DB.
"""
from __future__ import annotations

import statistics
from typing import Any

METHOD_VERSION = "v1"
WEIGHTS: dict[str, float] = {"quality": 0.30, "value": 0.25, "growth": 0.25, "risk": 0.20}
COVERAGE_PENALTY: dict[int, float] = {4: 1.0, 3: 0.92, 2: 0.80, 1: 0.65, 0: 0.0}

SIGNALS: list[tuple[float, float, str]] = [
    (8.0, 10.001, "strong_candidate"),
    (6.5, 8.0, "constructive"),
    (5.0, 6.5, "mixed"),
    (3.5, 5.0, "weak"),
    (0.0, 3.5, "avoid"),
]

MIN_CUSTOM_PEERS = 8

DISCLAIMER = (
    "Personal research score, not investment advice. Deterministic heuristic over a "
    "static research snapshot; verify everything before relying on it."
)

# ---------------------------------------------------------------------------
# Domain constants extracted from inline formulas (G25: Named constants)
# ---------------------------------------------------------------------------
ROE_WINSOR_LO = -1.0
ROE_WINSOR_HI = 1.0
ROA_OFFSET = 0.05
ROA_SCALE = 0.25
EFFICIENCY_BASE = 0.85
EFFICIENCY_SCALE = 0.45
ROAA_SCALE = 0.015
CET1_BASE = 0.08
CET1_SCALE = 0.06
NIM_SCALE = 0.04
FCF_MARGIN_SCALE = 0.25
GROSS_MARGIN_SCALE = 0.6
NOVY_MARX_GP_SCALE = 0.5
QUALITY_FSCORE_WEIGHT = 0.70
QUALITY_LEVEL_WEIGHT = 0.30
FSCORE_MAX = 9.0
SCORE_MAX = 10.0

RISK_NETDEBT_EBITDA_POINTS: list[tuple[float, float]] = [(0.0, 10.0), (1.0, 8.0), (2.0, 6.5), (4.0, 3.0), (6.0, 0.0)]
RISK_LIAB_ASSETS_BASE = 0.9
RISK_LIAB_ASSETS_SCALE = 0.6
RISK_COVERAGE_POINTS: list[tuple[float, float]] = [(0.0, 0.0), (1.0, 0.0), (3.0, 5.0), (10.0, 10.0)]
CET1_RISK_BASE = 0.08
CET1_RISK_SCALE = 0.06
LEVERAGE_BASE = 0.03
LEVERAGE_SCALE = 0.07

GROWTH_CAGR_POINTS: list[tuple[float, float]] = [(-0.40, 0.0), (-0.20, 2.0), (0.0, 5.0), (0.20, 8.0), (0.40, 10.0)]
GROWTH_CAGR_CLAMP_LO = -0.40
GROWTH_CAGR_CLAMP_HI = 0.40
GROWTH_CAGR_WINSOR_LO = -0.40
GROWTH_CAGR_WINSOR_HI = 0.40


def _to_float_optional(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric == numeric else None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# Backward-compat aliases (N1 improvement but preserve old imports)
_f = _to_float_optional
_winsorize = _clamp


def signal_for(composite: float | None) -> str | None:
    if composite is None:
        return "insufficient_data"
    for low, high, name in SIGNALS:
        if low <= composite < high:
            return name
    return "insufficient_data"


# --------------------------------------------------------------------------
# Peers
# --------------------------------------------------------------------------


def percentile_rank(values: list[float], observed: float, lower_is_better: bool = False) -> float | None:
    valid = sorted(v for v in values if v is not None and v == v)
    if not valid:
        return None
    position = sum(1 for v in valid if v <= observed)
    fraction = position / len(valid)
    return round(1.0 - fraction, 6) if lower_is_better else fraction


def build_peer_sets(companies: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, tuple[str, int]]]:
    """Peer set: same consolidated custom_industry_sheet + currency (min 8 members), else
    GICS_Sector + currency. Currencies are never mixed. Consolidation 86→~40 ensures n≥8."""
    try:
        from app.services.industry_consolidation import consolidate_sheet  # local import to avoid cycle
    except Exception:
        def consolidate_sheet(s):  # type: ignore
            return s

    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for company in companies:
        currency = (company.get("currency") or "").strip().upper()
        if not currency:
            continue
        raw_sheet = (company.get("custom_industry_sheet") or "").strip()
        sheet = (consolidate_sheet(raw_sheet) or "").strip() if raw_sheet else ""
        sector = (company.get("gics_sector") or "").strip()
        if sheet:
            by_key.setdefault(("custom", sheet, currency), []).append(company)
        if sector:
            by_key.setdefault(("gics", sector, currency), []).append(company)

    members: dict[str, list[dict[str, Any]]] = {}
    meta: dict[str, tuple[str, int]] = {}
    for company in companies:
        company_id: str = company["company_id"]
        currency = (company.get("currency") or "").strip().upper()
        raw_sheet = (company.get("custom_industry_sheet") or "").strip()
        sheet = (consolidate_sheet(raw_sheet) or "").strip() if raw_sheet else ""
        sector = (company.get("gics_sector") or "").strip()
        custom = by_key.get(("custom", sheet, currency)) if sheet else None
        gics = by_key.get(("gics", sector, currency)) if sector else None
        if custom and len(custom) >= MIN_CUSTOM_PEERS:
            members[company_id], meta[company_id] = custom, ("custom_industry_currency", len(custom))
        elif gics and len(gics) >= 2:
            members[company_id], meta[company_id] = gics, ("gics_currency", len(gics))
        elif custom and len(custom) >= 2:
            members[company_id], meta[company_id] = custom, ("custom_industry_currency", len(custom))
        else:
            full_currency = [c for c in companies if (c.get("currency") or "").strip().upper() == currency]
            if len(full_currency) >= 2:
                members[company_id], meta[company_id] = full_currency, ("broad_peer_set", len(full_currency))
            elif gics:
                members[company_id], meta[company_id] = gics, ("gics_currency", len(gics))
            elif custom:
                members[company_id], meta[company_id] = custom, ("custom_industry_currency", len(custom))
            else:
                members[company_id], meta[company_id] = [company], ("broad_peer_set", 1)
    return members, meta


def peer_values_for(members: list[dict[str, Any]]) -> dict[str, list[float]]:
    """Collect comparable raw metric lists from peer snapshot rows (dicts).

    CONTRACT: callers must pass peers EXCLUDING the company itself, so its own
    percentile maps to the full 0..10 range (cheapest/best = 10)."""
    out: dict[str, list[float]] = {
        k: [] for k in ("pe", "pb", "ev_to_ebitda", "earnings_yield", "roe", "roa", "fcfmargin", "grossmargin", "efficiency", "roaa")
    }
    for member in members:
        row = member.get("snapshot") or {}
        seed_snapshot = member.get("seed_snapshot") or {}
        if seed_snapshot:
            enriched_row = dict(row)
            for key, value in seed_snapshot.items():
                if enriched_row.get(key) is None and value is not None:
                    enriched_row[key] = value
            row = enriched_row
        pe = _to_float_optional(row.get("pe_calc"))
        if pe is not None and pe > 0:
            out["pe"].append(pe)
        pb = _to_float_optional(row.get("pb_calc"))
        if pb is not None and pb > 0:
            out["pb"].append(pb)
        ev = _to_float_optional(row.get("ev_to_ebitda_calc"))
        if ev is not None and ev > 0:
            out["ev_to_ebitda"].append(ev)
        price, eps = _to_float_optional(row.get("price")), _to_float_optional(row.get("diluted_eps"))
        if price is not None and price > 0 and eps is not None and eps > 0:
            out["earnings_yield"].append(eps / price)
        for name, attr in (
            ("roe", "roe_calc"),
            ("roa", "roa_calc"),
            ("fcfmargin", "fcfmargin_calc"),
            ("grossmargin", "grossmargin_calc"),
            ("efficiency", "efficiency_ratio"),
            ("roaa", "roaa"),
        ):
            value = _to_float_optional(row.get(attr))
            if value is not None:
                out[name].append(value)
    return out


# --------------------------------------------------------------------------
# Quality
# --------------------------------------------------------------------------


def _safe_divide(numerator: Any, denominator: Any) -> float | None:
    num, den = _to_float_optional(numerator), _to_float_optional(denominator)
    if num is None or den is None or den == 0:
        return None
    return num / den


def _is_greater(left: Any, right: Any) -> bool | None:
    left_num, right_num = _to_float_optional(left), _to_float_optional(right)
    if left_num is None or right_num is None:
        return None
    return left_num > right_num


def _difference(left: Any, right: Any) -> float | None:
    left_num, right_num = _to_float_optional(left), _to_float_optional(right)
    if left_num is None or right_num is None:
        return None
    return left_num - right_num


# Aliases for backward compat
_safe_div = _safe_divide
_g = _is_greater
_delta = _difference


def piotroski_fscore(cur: dict[str, Any], prior: dict[str, Any] | None) -> tuple[int, int, dict[str, Any]]:
    """(F_used, F_possible, detail). Impossible tests reduce F_possible."""
    detail: dict[str, Any] = {}
    used = possible = 0

    def record_test(name: str, value: bool | None) -> None:
        nonlocal used, possible
        possible += 1
        if value is None:
            detail[name] = None
        else:
            detail[name] = bool(value)
            if value:
                used += 1

    roa = _safe_divide(cur.get("net_income"), cur.get("total_assets"))
    record_test("roa_positive", _is_greater(roa, 0))
    record_test("ocf_positive", _is_greater(cur.get("operating_cash_flow"), 0))
    record_test("accruals", _is_greater(cur.get("operating_cash_flow"), cur.get("net_income")))

    if prior is None:
        for name in ("delta_roa", "leverage_down", "current_ratio", "eq_offer", "delta_gross_margin", "delta_asset_turnover"):
            detail[name] = None
            possible += 1
        return used, possible, detail

    roa_prior = _safe_divide(prior.get("net_income"), prior.get("total_assets"))
    record_test("delta_roa", _is_greater(_difference(roa, roa_prior), 0))

    debt_cur, debt_prior = _to_float_optional(cur.get("total_debt")), _to_float_optional(prior.get("total_debt"))
    assets_cur, assets_prior = _to_float_optional(cur.get("total_assets")), _to_float_optional(prior.get("total_assets"))
    if debt_cur is None or debt_prior is None or assets_cur in (None, 0) or assets_prior in (None, 0):
        record_test("leverage_down", None)
    else:
        record_test("leverage_down", _is_greater(_difference(_safe_divide(debt_prior, assets_prior), _safe_divide(debt_cur, assets_cur)), 0))

    record_test("current_ratio", None)
    record_test("eq_offer", None)

    gm_cur = _safe_divide(cur.get("gross_profit"), cur.get("revenue"))
    gm_prior = _safe_divide(prior.get("gross_profit"), prior.get("revenue"))
    record_test("delta_gross_margin", _is_greater(_difference(gm_cur, gm_prior), 0))

    at_cur = _safe_divide(cur.get("revenue"), cur.get("total_assets"))
    at_prior = _safe_divide(prior.get("revenue"), prior.get("total_assets"))
    record_test("delta_asset_turnover", _is_greater(_difference(at_cur, at_prior), 0))
    return used, possible, detail


def _is_financial_company(cur: dict[str, Any]) -> bool:
    sector = (cur.get("gics_sector") or "").strip().lower()
    sheet = (cur.get("custom_industry_sheet") or "").strip().lower()
    return sector == "financials" or sheet in {"banks", "insurance", "credit_services"}


def _is_reit_company(cur: dict[str, Any]) -> bool:
    return (cur.get("custom_industry_sheet") or "").strip().lower() == "real_estate"


def _quality_components_for_financial(cur: dict[str, Any], detail: dict[str, Any], components: list[float]) -> None:
    efficiency = _to_float_optional(cur.get("efficiency_ratio"))
    if efficiency is not None:
        components.append(_clamp((EFFICIENCY_BASE - efficiency) / EFFICIENCY_SCALE, 0.0, 1.0))
        detail["efficiency_used"] = True
    roaa = _to_float_optional(cur.get("roaa"))
    if roaa is not None:
        components.append(_clamp(roaa / ROAA_SCALE, 0.0, 1.0))
        detail["roaa_used"] = True
    cet1 = _to_float_optional(cur.get("cet1_ratio"))
    if cet1 is not None:
        components.append(_clamp((cet1 - CET1_BASE) / CET1_SCALE, 0.0, 1.0))
        detail["cet1_used"] = True
    nim = _to_float_optional(cur.get("nim_fy2025")) or _to_float_optional(cur.get("nim_q4_2025"))
    if nim is not None:
        components.append(_clamp(nim / NIM_SCALE, 0.0, 1.0))
        detail["nim_used"] = True
    detail["path"] = "financial"


def _quality_components_for_industrial(cur: dict[str, Any], detail: dict[str, Any], components: list[float]) -> None:
    is_reit = _is_reit_company(cur)
    fcfm = _to_float_optional(cur.get("fcfmargin_calc"))
    gross_margin = _to_float_optional(cur.get("grossmargin_calc"))
    if fcfm is not None:
        components.append(_clamp(fcfm / FCF_MARGIN_SCALE, 0.0, 1.0))
        detail["fcf_margin_used"] = True
    elif gross_margin is not None and not is_reit:
        components.append(_clamp(gross_margin / GROSS_MARGIN_SCALE, 0.0, 1.0))
        detail["gross_margin_used"] = True
    if gross_margin is not None and not is_reit:
        gp_to_assets = _safe_divide(cur.get("gross_profit"), cur.get("total_assets"))
        if gp_to_assets is not None:
            components.append(_clamp(gp_to_assets / NOVY_MARX_GP_SCALE, 0.0, 1.0))
            detail["novy_marx_used"] = True


def _append_percentile_components(
    cur: dict[str, Any], peer_values: dict[str, list[float]], detail: dict[str, Any], components: list[float]
) -> None:
    for name, attr, lower_better in (
        ("roe", "roe_calc", False),
        ("roa", "roa_calc", False),
        ("fcfmargin", "fcfmargin_calc", False),
        ("grossmargin", "grossmargin_calc", False),
        ("efficiency", "efficiency_ratio", True),
        ("roaa", "roaa", False),
    ):
        value = _to_float_optional(cur.get(attr))
        if value is not None and peer_values.get(name):
            percentile = percentile_rank(peer_values[name], value, lower_is_better=lower_better)
            if percentile is not None:
                components.append(percentile)
                detail[f"{name}_pct"] = percentile


def quality_pillar(
    cur: dict[str, Any], prior: dict[str, Any] | None, peer_values: dict[str, list[float]]
) -> tuple[float | None, dict[str, Any]]:
    detail: dict[str, Any] = {}
    is_financial = _is_financial_company(cur)
    components: list[float] = []

    roe = _to_float_optional(cur.get("roe_calc"))
    if roe is not None:
        components.append(_clamp(roe, ROE_WINSOR_LO, ROE_WINSOR_HI) / 2 + 0.5)
        detail["roe_used"] = True
    roa = _to_float_optional(cur.get("roa_calc"))
    if roa is not None:
        components.append(_clamp((roa + ROA_OFFSET) / ROA_SCALE, 0.0, 1.0))
        detail["roa_used"] = True

    if is_financial:
        _quality_components_for_financial(cur, detail, components)
    else:
        _quality_components_for_industrial(cur, detail, components)

    _append_percentile_components(cur, peer_values, detail, components)

    if not components:
        return None, detail
    level_score = sum(components) / len(components) * SCORE_MAX

    if is_financial:
        return round(_clamp(level_score, 0.0, SCORE_MAX), 4), detail

    f_used, f_possible, fscore_detail = piotroski_fscore(cur, prior)
    detail["fscore"] = {"used": f_used, "possible": f_possible, "tests": fscore_detail}
    f_adjusted = (f_used / f_possible) * FSCORE_MAX if f_possible else None
    f_mapped = f_adjusted * (SCORE_MAX / FSCORE_MAX) if f_adjusted is not None else None

    if f_mapped is not None and level_score is not None:
        quality = QUALITY_FSCORE_WEIGHT * f_mapped + QUALITY_LEVEL_WEIGHT * level_score
        detail["blend"] = "70_fscore_30_level"
    elif f_mapped is not None:
        quality = f_mapped
        detail["blend"] = "fscore_only"
    else:
        quality = level_score
        detail["blend"] = "level_only"
    return round(_clamp(quality, 0.0, SCORE_MAX), 4), detail


# --------------------------------------------------------------------------
# Value
# --------------------------------------------------------------------------


def value_pillar(cur: dict[str, Any], peer_values: dict[str, list[float]]) -> tuple[float | None, dict[str, Any]]:
    detail: dict[str, Any] = {}
    parts: list[float] = []

    pe = _to_float_optional(cur.get("pe_calc"))
    if pe is not None and pe <= 0:
        detail["pe_negative_skipped"] = True
    elif pe is not None and peer_values.get("pe"):
        percentile = percentile_rank(peer_values["pe"], pe, lower_is_better=True)
        if percentile is not None:
            parts.append(percentile * SCORE_MAX)
            detail["pe_pct"] = percentile

    pb = _to_float_optional(cur.get("pb_calc"))
    if pb is not None and pb > 0 and peer_values.get("pb"):
        percentile = percentile_rank(peer_values["pb"], pb, lower_is_better=True)
        if percentile is not None:
            parts.append(percentile * SCORE_MAX)
            detail["pb_pct"] = percentile

    ev = _to_float_optional(cur.get("ev_to_ebitda_calc"))
    if ev is not None and ev > 0 and peer_values.get("ev_to_ebitda"):
        percentile = percentile_rank(peer_values["ev_to_ebitda"], ev, lower_is_better=True)
        if percentile is not None:
            parts.append(percentile * SCORE_MAX)
            detail["ev_ebitda_pct"] = percentile

    price, eps = _to_float_optional(cur.get("price")), _to_float_optional(cur.get("diluted_eps"))
    if price is not None and price > 0 and eps is not None and eps > 0 and peer_values.get("earnings_yield"):
        percentile = percentile_rank(peer_values["earnings_yield"], eps / price, lower_is_better=False)
        if percentile is not None:
            parts.append(percentile * SCORE_MAX)
            detail["earnings_yield_pct"] = percentile

    if not parts:
        return None, detail
    return round(sum(parts) / len(parts), 4), detail


# --------------------------------------------------------------------------
# Growth
# --------------------------------------------------------------------------


def _score_from_cagr(cagr: float) -> float:
    clamped = _clamp(cagr, GROWTH_CAGR_WINSOR_LO, GROWTH_CAGR_WINSOR_HI)
    points = GROWTH_CAGR_POINTS
    for (x0, y0), (x1, y1) in zip(points, points[1:], strict=False):
        if x0 <= clamped <= x1:
            return y0 + (clamped - x0) * (y1 - y0) / (x1 - x0)
    return SCORE_MAX if clamped > GROWTH_CAGR_CLAMP_HI else 0.0


def _compound_annual_growth_rate(begin: float, end: float, years: int) -> float | None:
    if years < 1 or begin <= 0 or end <= 0:
        return None
    return (end / begin) ** (1.0 / years) - 1.0


_piecewise_growth = _score_from_cagr
_cagr = _compound_annual_growth_rate


def growth_pillar(history: list[dict[str, Any]]) -> tuple[float | None, dict[str, Any]]:
    """history: FY rows (dicts) any order; needs fiscal_year + metric."""
    detail: dict[str, Any] = {}
    rows = [r for r in history if r.get("fiscal_year") is not None]
    if len(rows) < 2:
        detail["reason"] = "insufficient_history"
        return None, detail
    rows = sorted(rows, key=lambda row: row["fiscal_year"])
    scores: list[float] = []
    for name in ("revenue", "diluted_eps", "fcf_calc"):
        points = [(row["fiscal_year"], _to_float_optional(row.get(name))) for row in rows]
        points = [(y, v) for y, v in points if v is not None and v > 0]
        if len(points) < 3:
            detail[name] = None
            continue
        (y0, v0), (y1, v1) = points[0], points[-1]
        years = y1 - y0
        if years < 2:
            detail[name] = "one_year_change_not_used"
            continue
        cagr = _compound_annual_growth_rate(v0, v1, years)  # type: ignore[arg-type]
        if cagr is None:
            detail[name] = None
            continue
        scored = _score_from_cagr(cagr)
        scores.append(scored)
        detail[name] = {"cagr": round(cagr, 4), "score": round(scored, 4), "years": years}
    if not scores:
        detail.setdefault("reason", "no_series_with_3plus_fy")
        return None, detail
    return round(sum(scores) / len(scores), 4), detail


# --------------------------------------------------------------------------
# Risk
# --------------------------------------------------------------------------


def _interpolate_piecewise(points: list[tuple[float, float]], observed: float) -> float:
    for (x0, y0), (x1, y1) in zip(points, points[1:], strict=False):
        if x0 <= observed <= x1:
            return y0 + (observed - x0) * (y1 - y0) / (x1 - x0)
    return points[-1][1] if observed > points[-1][0] else points[0][1]


_piecewise = _interpolate_piecewise


def risk_pillar(cur: dict[str, Any], history: list[dict[str, Any]]) -> tuple[float | None, dict[str, Any]]:
    detail: dict[str, Any] = {}
    parts: list[float] = []

    net_debt, ebitda = _to_float_optional(cur.get("netdebt_calc")), _to_float_optional(cur.get("ebitda"))
    if net_debt is not None and ebitda is not None and ebitda > 0 and net_debt > 0:
        leverage = net_debt / ebitda
        parts.append(_interpolate_piecewise(RISK_NETDEBT_EBITDA_POINTS, leverage))
        detail["netdebt_ebitda"] = round(leverage, 3)

    total_assets, total_liabilities = _to_float_optional(cur.get("total_assets")), _to_float_optional(cur.get("total_liabilities"))
    if total_assets is not None and total_liabilities is not None and total_assets > 0:
        ratio = total_liabilities / total_assets
        parts.append(_clamp((RISK_LIAB_ASSETS_BASE - ratio) / RISK_LIAB_ASSETS_SCALE, 0.0, 1.0) * SCORE_MAX)
        detail["liab_assets"] = round(ratio, 3)

    ebit, interest_expense = _to_float_optional(cur.get("ebit")), _to_float_optional(cur.get("interest_expense"))
    if ebit is not None and interest_expense is not None and interest_expense > 0:
        coverage = ebit / interest_expense
        parts.append(_interpolate_piecewise(RISK_COVERAGE_POINTS, coverage))
        detail["interest_coverage"] = round(coverage, 2)

    cet1 = _to_float_optional(cur.get("cet1_ratio"))
    if cet1 is not None:
        parts.append(_clamp((cet1 - CET1_RISK_BASE) / CET1_RISK_SCALE, 0.0, 1.0) * SCORE_MAX)
        detail["cet1"] = cet1
    lev_ratio = _to_float_optional(cur.get("leverage_ratio"))
    if lev_ratio is not None:
        parts.append(_clamp((lev_ratio - LEVERAGE_BASE) / LEVERAGE_SCALE, 0.0, 1.0) * SCORE_MAX)
        detail["leverage_ratio"] = lev_ratio

    net_incomes = [_to_float_optional(row.get("net_income")) for row in history if row.get("fiscal_year") is not None]
    net_incomes = [v for v in net_incomes if v is not None]
    if len(net_incomes) >= 5:
        mean = sum(net_incomes) / len(net_incomes)
        if mean != 0:
            cv = statistics.stdev(net_incomes) / abs(mean)  # type: ignore[arg-type]
            parts.append(SCORE_MAX - _clamp(cv, 0.0, 1.0) * SCORE_MAX)
            detail["earnings_cv"] = round(cv, 3)
    else:
        detail["volatility_skipped"] = f"only_{len(net_incomes)}_fy"

    if not parts:
        detail["reason"] = "no_risk_inputs"
        return None, detail
    return round(sum(parts) / len(parts), 4), detail


# --------------------------------------------------------------------------
# Composite
# --------------------------------------------------------------------------


def composite_score(pillars: dict[str, float | None]) -> tuple[float | None, int, float]:
    available = {k: v for k, v in pillars.items() if v is not None}
    coverage = len(available)
    if coverage == 0:
        return None, 0, 0.0
    total_weight = sum(WEIGHTS[k] for k in available)
    weighted = sum(WEIGHTS[k] * v for k, v in available.items()) / total_weight
    penalty = COVERAGE_PENALTY[coverage]
    return round(weighted * penalty, 4), coverage, penalty


def score_company(
    cur: dict[str, Any],
    prior: dict[str, Any] | None,
    history: list[dict[str, Any]],
    peer_values: dict[str, list[float]],
) -> dict[str, Any]:
    quality, quality_detail = quality_pillar(cur, prior, peer_values)
    value, value_detail = value_pillar(cur, peer_values)
    growth, growth_detail = growth_pillar(history)
    risk, risk_detail = risk_pillar(cur, history)
    pillars = {"quality": quality, "value": value, "growth": growth, "risk": risk}
    composite, coverage, penalty = composite_score(pillars)
    return {
        "composite": composite,
        "pillars": pillars,
        "coverage": coverage,
        "penalty": penalty,
        "signal": signal_for(composite),
        "method_version": METHOD_VERSION,
        "details": {"quality": quality_detail, "value": value_detail, "growth": growth_detail, "risk": risk_detail},
        "disclaimer": DISCLAIMER,
    }
