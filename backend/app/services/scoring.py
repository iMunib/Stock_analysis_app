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
WEIGHTS = {"quality": 0.30, "value": 0.25, "growth": 0.25, "risk": 0.20}
COVERAGE_PENALTY = {4: 1.0, 3: 0.92, 2: 0.80, 1: 0.65, 0: 0.0}

SIGNALS = [
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


def _f(x: Any) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def _winsorize(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def signal_for(composite: float | None) -> str | None:
    if composite is None:
        return "insufficient_data"
    for lo, hi, name in SIGNALS:
        if lo <= composite < hi:
            return name
    return "insufficient_data"


# --------------------------------------------------------------------------
# Peers
# --------------------------------------------------------------------------

def percentile_rank(values: list[float], x: float, lower_is_better: bool = False) -> float | None:
    vals = sorted(v for v in values if v is not None and v == v)
    if not vals:
        return None
    pos = sum(1 for v in vals if v <= x)
    frac = pos / len(vals)
    return round(1.0 - frac, 6) if lower_is_better else frac


def build_peer_sets(companies: list[dict]) -> tuple[dict[str, list[dict]], dict[str, tuple[str, int]]]:
    """Peer set: same custom_industry_sheet + currency (min 8 members), else
    GICS_Sector + currency. Currencies are never mixed."""
    by_key: dict[tuple[str, str, str], list[dict]] = {}
    for c in companies:
        cur = (c.get("currency") or "").strip().upper()
        if not cur:
            continue
        sheet = (c.get("custom_industry_sheet") or "").strip()
        sector = (c.get("gics_sector") or "").strip()
        if sheet:
            by_key.setdefault(("custom", sheet, cur), []).append(c)
        if sector:
            by_key.setdefault(("gics", sector, cur), []).append(c)

    members: dict[str, list[dict]] = {}
    meta: dict[str, tuple[str, int]] = {}
    for c in companies:
        cid = c["company_id"]
        cur = (c.get("currency") or "").strip().upper()
        sheet = (c.get("custom_industry_sheet") or "").strip()
        sector = (c.get("gics_sector") or "").strip()
        custom = by_key.get(("custom", sheet, cur)) if sheet else None
        gics = by_key.get(("gics", sector, cur)) if sector else None
        if custom and len(custom) >= MIN_CUSTOM_PEERS:
            members[cid], meta[cid] = custom, ("custom_industry_currency", len(custom))
        elif gics and len(gics) >= 2:
            members[cid], meta[cid] = gics, ("gics_currency", len(gics))
        elif custom:
            members[cid], meta[cid] = custom, ("custom_industry_currency", len(custom))
        else:
            members[cid], meta[cid] = [c], ("gics_currency", 1)
    return members, meta


def peer_values_for(members: list[dict]) -> dict[str, list[float]]:
    """Collect comparable raw metric lists from peer snapshot rows (dicts).

    CONTRACT: callers must pass peers EXCLUDING the company itself, so its own
    percentile maps to the full 0..10 range (cheapest/best = 10)."""
    out: dict[str, list[float]] = {k: [] for k in (
        "pe", "pb", "ev_to_ebitda", "earnings_yield", "roe", "roa",
        "fcfmargin", "grossmargin", "efficiency", "roaa",
    )}
    for m in members:
        row = m.get("snapshot") or {}
        pe = _f(row.get("pe_calc"))
        if pe is not None and pe > 0:
            out["pe"].append(pe)
        pb = _f(row.get("pb_calc"))
        if pb is not None and pb > 0:
            out["pb"].append(pb)
        ev = _f(row.get("ev_to_ebitda_calc"))
        if ev is not None and ev > 0:
            out["ev_to_ebitda"].append(ev)
        price, eps = _f(row.get("price")), _f(row.get("diluted_eps"))
        if price is not None and price > 0 and eps is not None and eps > 0:
            out["earnings_yield"].append(eps / price)
        for name, attr in (("roe", "roe_calc"), ("roa", "roa_calc"),
                           ("fcfmargin", "fcfmargin_calc"), ("grossmargin", "grossmargin_calc"),
                           ("efficiency", "efficiency_ratio"), ("roaa", "roaa")):
            v = _f(row.get(attr))
            if v is not None:
                out[name].append(v)
    return out


# --------------------------------------------------------------------------
# Quality
# --------------------------------------------------------------------------

def _safe_div(a: Any, b: Any) -> float | None:
    a, b = _f(a), _f(b)
    if a is None or b is None or b == 0:
        return None
    return a / b


def _g(a: Any, b: Any) -> bool | None:
    a, b = _f(a), _f(b)
    if a is None or b is None:
        return None
    return a > b


def _delta(a: Any, b: Any) -> float | None:
    a, b = _f(a), _f(b)
    if a is None or b is None:
        return None
    return a - b


def piotroski_fscore(cur: dict, prior: dict | None) -> tuple[int, int, dict]:
    """(F_used, F_possible, detail). Impossible tests reduce F_possible."""
    detail: dict[str, Any] = {}
    used = possible = 0

    def test(name: str, value: bool | None):
        nonlocal used, possible
        possible += 1
        if value is None:
            detail[name] = None
        else:
            detail[name] = bool(value)
            if value:
                used += 1

    roa = _safe_div(cur.get("net_income"), cur.get("total_assets"))
    test("roa_positive", _g(roa, 0))
    test("ocf_positive", _g(cur.get("operating_cash_flow"), 0))
    # Accruals (OCF > NI) is a CURRENT-year test in Piotroski (2000): it does not
    # need a prior FY, so it is not deferred to the prior-year block.
    test("accruals", _g(cur.get("operating_cash_flow"), cur.get("net_income")))

    if prior is None:
        # Single-FY: prior-dependent and data-absent tests are impossible, not failed.
        for name in ("delta_roa", "leverage_down",
                     "current_ratio", "eq_offer", "delta_gross_margin", "delta_asset_turnover"):
            detail[name] = None
            possible += 1
        return used, possible, detail

    roa_p = _safe_div(prior.get("net_income"), prior.get("total_assets"))
    test("delta_roa", _g(_delta(roa, roa_p), 0))

    d_cur, d_p = _f(cur.get("total_debt")), _f(prior.get("total_debt"))
    ta_cur, ta_p = _f(cur.get("total_assets")), _f(prior.get("total_assets"))
    if d_cur is None or d_p is None or ta_cur in (None, 0) or ta_p in (None, 0):
        test("leverage_down", None)  # NULL debt (owner-blank) -> skip, never fake
    else:
        test("leverage_down", _g(_delta(_safe_div(d_p, ta_p), _safe_div(d_cur, ta_cur)), 0))

    # Current assets/liabilities absent in seed -> always skip.
    test("current_ratio", None)
    # Eq offer needs a shares time series; absent in seed -> skip.
    test("eq_offer", None)

    gm_cur = _safe_div(cur.get("gross_profit"), cur.get("revenue"))
    gm_p = _safe_div(prior.get("gross_profit"), prior.get("revenue"))
    test("delta_gross_margin", _g(_delta(gm_cur, gm_p), 0))  # None when GP NULL (banks)

    at_cur = _safe_div(cur.get("revenue"), cur.get("total_assets"))
    at_p = _safe_div(prior.get("revenue"), prior.get("total_assets"))
    test("delta_asset_turnover", _g(_delta(at_cur, at_p), 0))  # None when Revenue NULL
    return used, possible, detail


def quality_pillar(cur: dict, prior: dict | None, peer_values: dict[str, list[float]]) -> tuple[float | None, dict]:
    detail: dict[str, Any] = {}
    sector = (cur.get("gics_sector") or "").strip().lower()
    sheet = (cur.get("custom_industry_sheet") or "").strip().lower()
    is_fin = sector == "financials" or sheet in {"banks", "insurance", "credit_services"}
    is_reit = sheet == "real_estate"

    components: list[float] = []  # 0..1 floats

    roe = _f(cur.get("roe_calc"))
    if roe is not None:
        components.append(_winsorize(roe, -1.0, 1.0) / 2 + 0.5)
        detail["roe_used"] = True
    roa = _f(cur.get("roa_calc"))
    if roa is not None:
        components.append(_winsorize((roa + 0.05) / 0.25, 0.0, 1.0))
        detail["roa_used"] = True

    if is_fin:
        eff = _f(cur.get("efficiency_ratio"))
        if eff is not None:
            components.append(_winsorize((0.85 - eff) / 0.45, 0.0, 1.0))
            detail["efficiency_used"] = True
        roaa = _f(cur.get("roaa"))
        if roaa is not None:
            components.append(_winsorize(roaa / 0.015, 0.0, 1.0))
            detail["roaa_used"] = True
        cet1 = _f(cur.get("cet1_ratio"))
        if cet1 is not None:
            components.append(_winsorize((cet1 - 0.08) / 0.06, 0.0, 1.0))
            detail["cet1_used"] = True
        nim = _f(cur.get("nim_fy2025")) or _f(cur.get("nim_q4_2025"))
        if nim is not None:
            components.append(_winsorize(nim / 0.04, 0.0, 1.0))
            detail["nim_used"] = True
        detail["path"] = "financial"
    else:
        fcfm = _f(cur.get("fcfmargin_calc"))
        gm = _f(cur.get("grossmargin_calc"))
        if fcfm is not None:
            components.append(_winsorize(fcfm / 0.25, 0.0, 1.0))
            detail["fcf_margin_used"] = True
        elif gm is not None and not is_reit:
            components.append(_winsorize(gm / 0.6, 0.0, 1.0))
            detail["gross_margin_used"] = True
        if gm is not None and not is_reit:
            gp_a = _safe_div(cur.get("gross_profit"), cur.get("total_assets"))
            if gp_a is not None:
                components.append(_winsorize(gp_a / 0.5, 0.0, 1.0))  # Novy-Marx
                detail["novy_marx_used"] = True

    # Sector-currency percentile components (the "see peers" part of the level blend)
    pct_used = False
    for name, attr, lower_better in (
        ("roe", "roe_calc", False), ("roa", "roa_calc", False),
        ("fcfmargin", "fcfmargin_calc", False), ("grossmargin", "grossmargin_calc", False),
        ("efficiency", "efficiency_ratio", True), ("roaa", "roaa", False),
    ):
        v = _f(cur.get(attr))
        if v is not None and peer_values.get(name):
            p = percentile_rank(peer_values[name], v, lower_is_better=lower_better)
            if p is not None:
                components.append(p)
                detail[f"{name}_pct"] = p
                pct_used = True

    if not components:
        return None, detail
    level_score = sum(components) / len(components) * 10.0

    if is_fin:
        return round(_winsorize(level_score, 0.0, 10.0), 4), detail

    f_used, f_possible, fscore_detail = piotroski_fscore(cur, prior)
    detail["fscore"] = {"used": f_used, "possible": f_possible, "tests": fscore_detail}
    f_adj = (f_used / f_possible) * 9.0 if f_possible else None
    f_mapped = f_adj * (10.0 / 9.0) if f_adj is not None else None

    if f_mapped is not None and level_score is not None:
        quality = 0.70 * f_mapped + 0.30 * level_score
        detail["blend"] = "70_fscore_30_level"
    elif f_mapped is not None:
        quality = f_mapped
        detail["blend"] = "fscore_only"
    else:
        quality = level_score
        detail["blend"] = "level_only"
    return round(_winsorize(quality, 0.0, 10.0), 4), detail


# --------------------------------------------------------------------------
# Value
# --------------------------------------------------------------------------

def value_pillar(cur: dict, peer_values: dict[str, list[float]]) -> tuple[float | None, dict]:
    detail: dict[str, Any] = {}
    parts: list[float] = []

    pe = _f(cur.get("pe_calc"))
    if pe is not None and pe <= 0:
        detail["pe_negative_skipped"] = True  # negative earnings: not cheap, not a 0
    elif pe is not None and peer_values.get("pe"):
        p = percentile_rank(peer_values["pe"], pe, lower_is_better=True)
        if p is not None:
            parts.append(p * 10)
            detail["pe_pct"] = p

    pb = _f(cur.get("pb_calc"))
    if pb is not None and pb > 0 and peer_values.get("pb"):
        p = percentile_rank(peer_values["pb"], pb, lower_is_better=True)
        if p is not None:
            parts.append(p * 10)
            detail["pb_pct"] = p

    ev = _f(cur.get("ev_to_ebitda_calc"))
    if ev is not None and ev > 0 and peer_values.get("ev_to_ebitda"):
        p = percentile_rank(peer_values["ev_to_ebitda"], ev, lower_is_better=True)
        if p is not None:
            parts.append(p * 10)
            detail["ev_ebitda_pct"] = p

    price, eps = _f(cur.get("price")), _f(cur.get("diluted_eps"))
    if price is not None and price > 0 and eps is not None and eps > 0 and peer_values.get("earnings_yield"):
        p = percentile_rank(peer_values["earnings_yield"], eps / price, lower_is_better=False)
        if p is not None:
            parts.append(p * 10)
            detail["earnings_yield_pct"] = p

    if not parts:
        return None, detail
    return round(sum(parts) / len(parts), 4), detail


# --------------------------------------------------------------------------
# Growth
# --------------------------------------------------------------------------

def _piecewise_growth(cagr: float) -> float:
    c = _winsorize(cagr, -0.40, 0.40)
    pts = [(-0.40, 0.0), (-0.20, 2.0), (0.0, 5.0), (0.20, 8.0), (0.40, 10.0)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= c <= x1:
            return y0 + (c - x0) * (y1 - y0) / (x1 - x0)
    return 10.0 if c > 0.40 else 0.0


def _cagr(begin: float, end: float, years: int) -> float | None:
    if years < 1 or begin <= 0 or end <= 0:
        return None
    return (end / begin) ** (1.0 / years) - 1.0


def growth_pillar(history: list[dict]) -> tuple[float | None, dict]:
    """history: FY rows (dicts) any order; needs fiscal_year + metric."""
    detail: dict[str, Any] = {}
    rows = [r for r in history if r.get("fiscal_year") is not None]
    if len(rows) < 2:
        detail["reason"] = "insufficient_history"
        return None, detail
    rows = sorted(rows, key=lambda r: r["fiscal_year"])
    scores: list[float] = []
    for name in ("revenue", "diluted_eps", "fcf_calc"):
        pts = [(r["fiscal_year"], _f(r.get(name))) for r in rows]
        pts = [(y, v) for y, v in pts if v is not None and v > 0]
        if len(pts) < 3:
            detail[name] = None
            continue
        (y0, v0), (y1, v1) = pts[0], pts[-1]
        years = y1 - y0
        if years < 2:
            detail[name] = "one_year_change_not_used"
            continue
        cagr = _cagr(v0, v1, years)
        if cagr is None:
            detail[name] = None
            continue
        s = _piecewise_growth(cagr)
        scores.append(s)
        detail[name] = {"cagr": round(cagr, 4), "score": round(s, 4), "years": years}
    if not scores:
        detail.setdefault("reason", "no_series_with_3plus_fy")
        return None, detail
    return round(sum(scores) / len(scores), 4), detail


# --------------------------------------------------------------------------
# Risk
# --------------------------------------------------------------------------

def _piecewise(points: list[tuple[float, float]], x: float) -> float:
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    return points[-1][1] if x > points[-1][0] else points[0][1]


def risk_pillar(cur: dict, history: list[dict]) -> tuple[float | None, dict]:
    detail: dict[str, Any] = {}
    parts: list[float] = []

    nd, ebitda = _f(cur.get("netdebt_calc")), _f(cur.get("ebitda"))
    if nd is not None and ebitda is not None and ebitda > 0 and nd > 0:
        lev = nd / ebitda
        parts.append(_piecewise([(0.0, 10.0), (1.0, 8.0), (2.0, 6.5), (4.0, 3.0), (6.0, 0.0)], lev))
        detail["netdebt_ebitda"] = round(lev, 3)

    ta, tl = _f(cur.get("total_assets")), _f(cur.get("total_liabilities"))
    if ta is not None and tl is not None and ta > 0:
        ratio = tl / ta
        parts.append(_winsorize((0.9 - ratio) / 0.6, 0.0, 1.0) * 10)
        detail["liab_assets"] = round(ratio, 3)

    ebit, ie = _f(cur.get("ebit")), _f(cur.get("interest_expense"))
    if ebit is not None and ie is not None and ie > 0:
        cov = ebit / ie
        parts.append(_piecewise([(0.0, 0.0), (1.0, 0.0), (3.0, 5.0), (10.0, 10.0)], cov))
        detail["interest_coverage"] = round(cov, 2)

    cet1 = _f(cur.get("cet1_ratio"))
    if cet1 is not None:
        parts.append(_winsorize((cet1 - 0.08) / 0.06, 0.0, 1.0) * 10)
        detail["cet1"] = cet1
    lev_ratio = _f(cur.get("leverage_ratio"))
    if lev_ratio is not None:
        parts.append(_winsorize((lev_ratio - 0.03) / 0.07, 0.0, 1.0) * 10)
        detail["leverage_ratio"] = lev_ratio

    ni = [_f(r.get("net_income")) for r in history if r.get("fiscal_year") is not None]
    ni = [v for v in ni if v is not None]
    if len(ni) >= 5:
        mean = sum(ni) / len(ni)
        if mean != 0:
            cv = statistics.stdev(ni) / abs(mean)
            parts.append(10.0 - _winsorize(cv, 0.0, 1.0) * 10)
            detail["earnings_cv"] = round(cv, 3)
    else:
        detail["volatility_skipped"] = f"only_{len(ni)}_fy"

    if not parts:
        detail["reason"] = "no_risk_inputs"
        return None, detail
    return round(sum(parts) / len(parts), 4), detail


# --------------------------------------------------------------------------
# Composite
# --------------------------------------------------------------------------

def composite_score(pillars: dict[str, float | None]) -> tuple[float | None, int, float]:
    avail = {k: v for k, v in pillars.items() if v is not None}
    coverage = len(avail)
    if coverage == 0:
        return None, 0, 0.0
    total_w = sum(WEIGHTS[k] for k in avail)
    weighted = sum(WEIGHTS[k] * v for k, v in avail.items()) / total_w
    penalty = COVERAGE_PENALTY[coverage]
    return round(weighted * penalty, 4), coverage, penalty


def score_company(
    cur: dict,
    prior: dict | None,
    history: list[dict],
    peer_values: dict[str, list[float]],
) -> dict:
    q, qd = quality_pillar(cur, prior, peer_values)
    v, vd = value_pillar(cur, peer_values)
    g, gd = growth_pillar(history)
    r, rd = risk_pillar(cur, history)
    pillars = {"quality": q, "value": v, "growth": g, "risk": r}
    composite, coverage, penalty = composite_score(pillars)
    return {
        "composite": composite,
        "pillars": pillars,
        "coverage": coverage,
        "penalty": penalty,
        "signal": signal_for(composite),
        "method_version": METHOD_VERSION,
        "details": {"quality": qd, "value": vd, "growth": gd, "risk": rd},
        "disclaimer": DISCLAIMER,
    }
