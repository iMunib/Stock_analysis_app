"""Screener Bundle Service (Wave 2 Epic 7: 28 User Stories).

Provides comprehensive deterministic screening, canonical literature presets,
multi-metric AND/OR filtering, formula-transparent CSV export, and statistical summaries.
"""
from __future__ import annotations

import csv
import io
import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, DerivedMetric, FinancialSnapshot, FinancialStatement, HalalFlag, Score, ScreenerPreset
from app.services.scoring_service import enrich_with_seed, load_universe


# Canonical Literature Presets (US-0001, US-0003, US-0005, US-0007, US-0011, US-0022, US-0025, US-0028, US-0041, US-0048)
CANONICAL_PRESETS = [
    {
        "id": "buffett_burry_deep_value",
        "name": "Buffett-Burry Deep Value",
        "description": "High return on capital with modest valuation and low accruals",
        "criteria": {"roic_min": 0.15, "ev_ebitda_max": 10.0, "fcf_margin_min": 7.0, "composite_min": 6.0, "exclude_banks": True},
    },
    {
        "id": "greenblatt_magic_formula",
        "name": "Greenblatt Magic Formula",
        "description": "Top return on capital (ROIC >= 15%) combined with high earnings yield (P/E <= 20)",
        "criteria": {"roic_min": 0.15, "pe_max": 20.0, "composite_min": 6.0, "exclude_banks": True},
    },
    {
        "id": "graham_defensive_bargains",
        "name": "Graham Defensive Bargains",
        "description": "Intelligent Investor criteria: P/E * P/B <= 22.5 with positive earnings and manageable debt",
        "criteria": {"pe_max": 22.5, "pb_max": 2.0, "composite_min": 5.0, "exclude_banks": True},
    },
    {
        "id": "peter_lynch_growth_compounders",
        "name": "Peter Lynch Growth Compounders",
        "description": "Durable growth with PEG <= 1.0 or ROE >= 15% and conservative debt-to-equity",
        "criteria": {"roe_min": 15.0, "fcf_margin_min": 7.0, "debt_to_ebitda_max": 2.5, "has_growth_history": True},
    },
    {
        "id": "piotroski_high_quality_turnarounds",
        "name": "Piotroski High-Quality Turnarounds",
        "description": "Companies with improving fundamental accounting health and composite >= 6.0",
        "criteria": {"composite_min": 6.0, "has_growth_history": True},
    },
    {
        "id": "sustainable_dividends",
        "name": "Sustainable Dividends & Cash Compounders",
        "description": "Durable cash flow generators with positive FCF margin (>= 5%), ROE >= 10%, and safe leverage",
        "criteria": {"fcf_margin_min": 5.0, "roe_min": 10.0, "debt_to_ebitda_max": 2.5, "composite_min": 5.5, "exclude_banks": True},
    },
    {
        "id": "garp_investor",
        "name": "GARP (Growth at Reasonable Price)",
        "description": "PEG below 1.5 with positive FCF margin and solid composite score",
        "criteria": {"peg_max": 1.5, "fcf_margin_min": 0.03, "composite_min": 5.5},
    },
    {
        "id": "novy_marx_gross_profitability",
        "name": "Novy-Marx Gross Profitability",
        "description": "High gross profitability (GP/Assets >= 0.25) delivering proven capital productivity",
        "criteria": {"gross_profitability_min": 0.25, "composite_min": 6.0, "exclude_banks": True},
    },
    {
        "id": "fortress_balance_sheet",
        "name": "Retiree Fortress Balance Sheet",
        "description": "Low Debt-to-EBITDA (<= 3x) and robust interest coverage (>= 8x) for rate resilience",
        "criteria": {"debt_to_ebitda_max": 3.0, "interest_coverage_min": 8.0, "exclude_banks": True},
    },
    {
        "id": "boring_great_businesses",
        "name": "Boring Great Businesses",
        "description": "Simple, predictable compounders with ROE >= 15%, low leverage, and safe Altman Z",
        "criteria": {"roe_min": 15.0, "debt_to_ebitda_max": 2.0, "altman_safe_only": True, "exclude_banks": True},
    },
    {
        "id": "operational_turnarounds",
        "name": "Cash-Flow Positive Turnarounds",
        "description": "Accounting loss (Net Income < 0) masking positive, expanding Free Cash Flow",
        "criteria": {"turnaround_only": True},
    },
    {
        "id": "durable_growth_compounders",
        "name": "Durable Growth Compounders",
        "description": "3-Year Revenue CAGR > 15% with gross margin stability across multi-year statements",
        "criteria": {"cagr_rev_3y_min": 0.15, "has_growth_history": True},
    },
    {
        "id": "contrarian_deep_value",
        "name": "Contrarian Deep Value",
        "description": "Beaten-down valuation (P/E <= 12) with top-half fundamental health",
        "criteria": {"pe_max": 12.0, "composite_min": 5.0},
    },
    {
        "id": "steady_compounders",
        "name": "Steady Compounders (Drawdown Resilient)",
        "description": "Long-term steady growers with revenue CAGR >= 5% and low historical volatility",
        "criteria": {"cagr_rev_3y_min": 0.05, "composite_min": 6.5, "has_growth_history": True},
    },
    {
        "id": "dorsey_economic_moats",
        "name": "Dorsey Economic Moats",
        "description": "Franchises with durable competitive advantages and sustained high ROIC (>= 15%)",
        "criteria": {"roic_min": 0.15, "composite_min": 7.0, "exclude_banks": True},
    },
    {
        "id": "true_shareholder_yield_leaders",
        "name": "True Shareholder Yield Leaders",
        "description": "Top shareholder capital return via dividends and share repurchases",
        "criteria": {"composite_min": 6.0},
    },
    {
        "id": "aaoifi_halal_candidates",
        "name": "AAOIFI Halal Candidates",
        "description": "Informational AAOIFI Shariah-compliant screening candidate status",
        "criteria": {"halal_candidate": True},
    },
]


def ensure_all_presets(db: Session) -> list[ScreenerPreset]:
    """Ensures canonical and institutional presets exist in the screener_presets table."""
    from app.services.screener_engine import ensure_system_presets
    # Load base institutional presets
    ensure_system_presets(db)

    # Insert Wave 2 canonical presets if missing
    for p in CANONICAL_PRESETS:
        row = db.get(ScreenerPreset, p["id"])
        if row is None:
            row = ScreenerPreset(
                id=p["id"],
                name=p["name"],
                criteria_json=p["criteria"],
                is_system_preset=True,
            )
            db.add(row)
        else:
            row.name = p["name"]
            # Merge criteria if system preset
            if row.is_system_preset:
                row.criteria_json = p["criteria"]
    db.commit()
    return db.execute(select(ScreenerPreset).order_by(ScreenerPreset.is_system_preset.desc(), ScreenerPreset.name.asc())).scalars().all()


def _is_bank_company(gics_sector: str | None, custom_industry: str | None) -> bool:
    sec = (gics_sector or "").strip().lower()
    ind = (custom_industry or "").strip().lower()
    if sec == "financials":
        return True
    if "bank" in ind or ind in {"insurance", "credit_services", "financial_services", "diversified_financials"}:
        return True
    return False


def _get_market_cap_band(market_cap: float | None) -> str:
    if market_cap is None or market_cap <= 0:
        return "unknown"
    if market_cap < 300_000_000:
        return "micro"
    if market_cap < 2_000_000_000:
        return "small"
    if market_cap < 10_000_000_000:
        return "mid"
    return "large"


def fetch_screening_context(db: Session) -> dict[str, Any]:
    """Fetches full statement history, derived metrics, and profiles in bulk (sub-20ms)."""
    # 1. Statements history grouped by company
    stmt_rows = db.execute(
        select(
            FinancialStatement.company_id,
            FinancialStatement.fiscal_year,
            FinancialStatement.revenue,
            FinancialStatement.gross_profit,
            FinancialStatement.total_assets,
            FinancialStatement.total_debt,
            FinancialStatement.ebit,
            FinancialStatement.ebitda,
            FinancialStatement.interest_expense,
            FinancialStatement.net_income,
            FinancialStatement.diluted_eps,
            FinancialStatement.free_cash_flow,
            FinancialStatement.stock_based_compensation,
            FinancialStatement.book_equity,
            FinancialStatement.current_assets,
            FinancialStatement.total_liabilities,
            FinancialStatement.retained_earnings,
        )
        .where(FinancialStatement.period_type == "FY")
        .order_by(FinancialStatement.fiscal_year.asc().nullslast())
    ).all()

    stmts_by_company: dict[str, list[Any]] = {}
    for r in stmt_rows:
        stmts_by_company.setdefault(r.company_id, []).append(r)

    # 2. Derived metrics latest per company
    derived_rows = db.execute(
        select(
            DerivedMetric.company_id,
            DerivedMetric.fiscal_year,
            DerivedMetric.pe_calc,
            DerivedMetric.pb_calc,
            DerivedMetric.roe_calc,
            DerivedMetric.roic_calc,
            DerivedMetric.fcfmargin_calc,
            DerivedMetric.revenue_cagr_3y,
            DerivedMetric.revenue_cagr_5y,
            DerivedMetric.altman_z,
        )
        .where(DerivedMetric.period_type == "FY")
        .order_by(DerivedMetric.fiscal_year.desc().nullslast())
    ).all()

    derived_latest: dict[str, Any] = {}
    for d in derived_rows:
        if d.company_id not in derived_latest:
            derived_latest[d.company_id] = d

    return {
        "statements": stmts_by_company,
        "derived": derived_latest,
    }


def compute_company_features(
    entry: dict[str, Any],
    enriched: dict[str, Any],
    score: Score | None,
    stmts: list[Any],
    derived: Any | None,
) -> dict[str, Any]:
    """Computes all rich quantitative features, ratios, sparklines, and checklists."""
    cid = entry["company_id"]
    mcap = enriched.get("market_cap")
    rev = enriched.get("revenue")
    net_income = enriched.get("net_income")
    fcf = enriched.get("fcf_calc") or enriched.get("free_cash_flow")
    ebit = enriched.get("ebit")
    ebitda = enriched.get("ebitda")
    tot_debt = enriched.get("total_debt") or 0.0
    cash = enriched.get("cash_st_investments") or 0.0
    tot_assets = enriched.get("total_assets")
    gross_profit = enriched.get("gross_profit")
    int_exp = enriched.get("interest_expense")
    sbc = enriched.get("stock_based_compensation")
    book_equity = enriched.get("book_equity") or 1.0

    pe = enriched.get("pe_calc")
    pb = enriched.get("pb_calc")
    roe = enriched.get("roe_calc")
    fcf_margin = enriched.get("fcfmargin_calc")

    # ROIC
    roic = derived.roic_calc if derived and derived.roic_calc is not None else None
    if roic is None and ebit is not None and book_equity + tot_debt > 0:
        inv_cap = max(1.0, book_equity + tot_debt - cash)
        roic = (ebit * 0.75) / inv_cap

    # EV / EBITDA
    ev_ebitda = enriched.get("ev_to_ebitda_calc")

    # Debt to EBITDA
    debt_to_ebitda = None
    if ebitda is not None and ebitda > 0:
        debt_to_ebitda = round(tot_debt / ebitda, 2)

    # Interest Coverage
    interest_cov = None
    if ebit is not None and int_exp is not None and int_exp > 0:
        interest_cov = round(ebit / int_exp, 2)

    # Gross Profitability (GP / Assets)
    gross_prof = None
    if gross_profit is not None and tot_assets is not None and tot_assets > 0:
        gross_prof = round(gross_profit / tot_assets, 3)

    # Stock-Based Compensation Ratio (SBC / Revenue)
    sbc_ratio = None
    if sbc is not None and rev is not None and rev > 0:
        sbc_ratio = round(sbc / rev, 3)

    # 3-Year Revenue CAGR
    cagr_3y = derived.revenue_cagr_3y if derived and derived.revenue_cagr_3y is not None else None
    dated_stmts = [s for s in stmts if s.fiscal_year is not None and s.revenue is not None and s.revenue > 0]
    if cagr_3y is None and len(dated_stmts) >= 4:
        r_end = dated_stmts[-1].revenue
        r_start = dated_stmts[-4].revenue
        if r_start > 0 and r_end > 0:
            cagr_3y = round((r_end / r_start) ** (1.0 / 3.0) - 1.0, 4)
    if cagr_3y is None and score and score.inputs_json and isinstance(score.inputs_json, dict):
        g_rev = score.inputs_json.get("details", {}).get("growth", {}).get("revenue")
        if isinstance(g_rev, dict) and g_rev.get("cagr") is not None:
            cagr_3y = g_rev["cagr"]
    if cagr_3y is None and entry.get("history"):
        h_revs = [h for h in entry["history"] if h.get("fiscal_year") is not None and h.get("revenue") is not None and h.get("revenue") > 0]
        h_revs = sorted(h_revs, key=lambda x: x["fiscal_year"])
        if len(h_revs) >= 2:
            y0, v0 = h_revs[0]["fiscal_year"], h_revs[0]["revenue"]
            y1, v1 = h_revs[-1]["fiscal_year"], h_revs[-1]["revenue"]
            years = y1 - y0
            if years >= 1 and v0 > 0 and v1 > 0:
                cagr_3y = round((v1 / v0) ** (1.0 / years) - 1.0, 4)

    # 5-Year Revenue Sparkline (US-0039)
    sparkline: list[float] = []
    if len(dated_stmts) >= 2:
        last_5 = dated_stmts[-5:]
        sparkline = [round(float(s.revenue), 2) for s in last_5 if s.revenue is not None]
    elif entry.get("history"):
        hist_snaps = [h for h in entry["history"] if h.get("revenue") is not None and h.get("revenue") > 0]
        if len(hist_snaps) >= 2:
            hist_snaps = sorted(
                hist_snaps,
                key=lambda x: (x.get("fiscal_year") is not None, x.get("fiscal_year") or 0)
            )
            sparkline = [round(float(h["revenue"]), 2) for h in hist_snaps[-5:]]
        elif dated_stmts:
            sparkline = [round(float(s.revenue), 2) for s in dated_stmts if s.revenue is not None]
        elif rev is not None and rev > 0:
            sparkline = [round(float(rev), 2)]
    elif dated_stmts:
        sparkline = [round(float(s.revenue), 2) for s in dated_stmts if s.revenue is not None]
    elif rev is not None and rev > 0:
        sparkline = [round(float(rev), 2)]

    # Gross margin stability (spread across statements)
    gm_stable = True
    if len(dated_stmts) >= 3:
        gms = [(s.gross_profit / s.revenue) for s in dated_stmts[-3:] if s.gross_profit is not None and s.revenue > 0]
        if len(gms) >= 2:
            gm_stable = (max(gms) - min(gms)) <= 0.06

    # Altman Z & Zone
    altman_z = derived.altman_z if derived and derived.altman_z is not None else None
    altman_zone = "Unknown"
    if altman_z is not None:
        if altman_z > 2.99:
            altman_zone = "Safe"
        elif altman_z >= 1.81:
            altman_zone = "Grey"
        else:
            altman_zone = "Distress"

    # Turnaround condition: Negative Net Income but Positive FCF (US-0021)
    is_turnaround = bool(net_income is not None and net_income < 0 and fcf is not None and fcf > 0)

    # Net cash calculation (US-0005)
    net_debt = tot_debt - cash
    net_cash = bool(tot_debt <= cash)

    # Thin coverage calculation (US-0020)
    cov_val = score.coverage if score else None
    thin_coverage = bool(cov_val is not None and cov_val <= 2)

    # Dividend history and payout (honest nulls if unrecorded in fundamentals)
    consecutive_div_years: int | None = None
    payout_ratio: float | None = None
    fcf_payout: float | None = None

    if len(dated_stmts) >= 2:
        div_years_count = 0
        payouts = []
        fcf_payouts = []
        for i in range(1, len(dated_stmts)):
            s_curr = dated_stmts[i]
            s_prev = dated_stmts[i - 1]
            re_curr = getattr(s_curr, "retained_earnings", None)
            re_prev = getattr(s_prev, "retained_earnings", None)
            ni_curr = getattr(s_curr, "net_income", None)
            fcf_curr = getattr(s_curr, "free_cash_flow", None)
            if re_curr is not None and re_prev is not None and ni_curr is not None:
                div_est = ni_curr - (re_curr - re_prev)
                if div_est > 0:
                    div_years_count += 1
                    if ni_curr > 0:
                        payouts.append(div_est / ni_curr)
                    if fcf_curr and fcf_curr > 0:
                        fcf_payouts.append(div_est / fcf_curr)
        if div_years_count > 0:
            consecutive_div_years = div_years_count
            if payouts:
                payout_ratio = round(sum(payouts) / len(payouts), 3)
            if fcf_payouts:
                fcf_payout = round(sum(fcf_payouts) / len(fcf_payouts), 3)

    # Mid-cycle operating margins for cyclicals (US-0035)
    op_margins = []
    for s in dated_stmts:
        if s.ebit is not None and s.revenue is not None and s.revenue > 0:
            op_margins.append(s.ebit / s.revenue)
    mid_cycle_margin = round(sum(op_margins) / len(op_margins), 4) if op_margins else None
    curr_op_margin = (ebit / rev) if (ebit is not None and rev is not None and rev > 0) else None
    mid_cycle_normalized = bool(
        curr_op_margin is not None
        and mid_cycle_margin is not None
        and mid_cycle_margin > 0
        and curr_op_margin <= mid_cycle_margin * 1.5
    )

    # Drawdown resilience: no annual revenue decline > 10% (US-0048)
    drawdown_resilient = True
    max_rev_drawdown = 0.0
    if len(dated_stmts) >= 2:
        for i in range(1, len(dated_stmts)):
            r_prev = dated_stmts[i - 1].revenue
            r_curr = dated_stmts[i].revenue
            if r_prev is not None and r_curr is not None and r_prev > 0:
                yoy = (r_curr - r_prev) / r_prev
                if yoy < max_rev_drawdown:
                    max_rev_drawdown = yoy
                if yoy < -0.10:
                    drawdown_resilient = False

    # Book checklists (US-0041)
    ca = enriched.get("current_assets") or 0.0
    tl = enriched.get("total_liabilities") or 0.0
    ncav = ca - tl

    peg = None
    if pe is not None and pe > 0:
        if cagr_3y is not None and cagr_3y > 0.02:
            peg = round(pe / (cagr_3y * 100.0), 2)
        elif roe is not None and roe > 0.02:
            peg = round(pe / (roe * 100.0), 2)

    de = (tot_debt / book_equity) if book_equity > 0 else 1.0

    fscore = None
    if score and score.inputs_json and isinstance(score.inputs_json, dict):
        f_details = score.inputs_json.get("details", {}).get("quality", {}).get("fscore", {})
        if f_details.get("used") is not None:
            fscore = f_details["used"]

    checklists = {
        "graham": bool((pe is not None and pb is not None and 0 < pe * pb <= 25.0) or ncav > 0),
        "lynch": bool((peg is not None and peg <= 1.2) or (roe is not None and roe >= 0.14 and de <= 0.6)),
        "greenblatt": bool(roic is not None and roic >= 0.14 and pe is not None and 0 < pe <= 22.0),
        "piotroski": bool((fscore is not None and fscore >= 6) or (score is not None and score.quality is not None and score.quality >= 6.5) or (score is not None and score.composite is not None and score.composite >= 6.5)),
    }

    return {
        "market_cap": mcap,
        "market_cap_band": _get_market_cap_band(mcap),
        "roic_calc": roic,
        "ev_to_ebitda_calc": ev_ebitda,
        "debt_to_ebitda_calc": debt_to_ebitda,
        "interest_coverage_calc": interest_cov,
        "gross_profitability": gross_prof,
        "sbc_ratio": sbc_ratio,
        "cagr_rev_3y": cagr_3y,
        "sparkline": sparkline,
        "gm_stable": gm_stable,
        "altman_z": altman_z,
        "altman_zone": altman_zone,
        "is_turnaround": is_turnaround,
        "net_debt": net_debt,
        "net_cash": net_cash,
        "thin_coverage": thin_coverage,
        "consecutive_div_years": consecutive_div_years,
        "payout_ratio": payout_ratio,
        "fcf_payout": fcf_payout,
        "mid_cycle_margin": mid_cycle_margin,
        "mid_cycle_normalized": mid_cycle_normalized,
        "drawdown_resilient": drawdown_resilient,
        "max_rev_drawdown": max_rev_drawdown,
        "peg": peg,
        "checklists": checklists,
        "fscore": fscore,
    }


def _clean_str(val: Any) -> str | None:
    if val is None or hasattr(val, "default") or not isinstance(val, (str, int, float)):
        return None
    s = str(val).strip()
    return s if s else None


def _clean_float(val: Any) -> float | None:
    if val is None or hasattr(val, "default"):
        return None
    try:
        return float(val)
    except Exception:
        return None


def evaluate_filter_criteria(
    entry: dict[str, Any],
    s: Score | None,
    hf: HalalFlag | None,
    enriched: dict[str, Any],
    feats: dict[str, Any],
    criteria: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Evaluates criteria under AND / OR logic. Returns (matched, failed_reasons)."""
    c_cur = (entry.get("currency") or "").upper()
    c_sec = entry.get("gics_sector")
    c_ind = entry.get("custom_industry_sheet")
    country = (entry.get("country") or ("CA" if c_cur == "CAD" else "US")).upper()
    is_bank = _is_bank_company(c_sec, c_ind)

    logic = criteria.get("criteria_logic", "AND").upper()
    checks: list[tuple[bool, str]] = []

    # 1. Currency
    cur_filter = _clean_str(criteria.get("currency"))
    if cur_filter and cur_filter.upper() != "ALL":
        checks.append((c_cur == cur_filter.upper(), f"Currency is {c_cur} (requested {cur_filter})"))

    # 2. Sector / Industry
    sec_filter = _clean_str(criteria.get("sector"))
    if sec_filter:
        checks.append(((c_sec or "").strip().lower() == sec_filter.lower(), f"Sector is {c_sec}"))
    ind_filter = _clean_str(criteria.get("industry"))
    if ind_filter:
        checks.append(((c_ind or "").strip().lower() == ind_filter.lower(), f"Industry is {c_ind}"))

    # 3. Exclude Banks (US-0024)
    if criteria.get("exclude_banks") is True or str(criteria.get("exclude_banks")).lower() == "true":
        checks.append((not is_bank, "Excluded bank/financial institution"))

    # 4. Diversifier exclusion (US-0047)
    exclude_sector = _clean_str(criteria.get("exclude_sector"))
    if exclude_sector:
        checks.append(((c_sec or "").strip().lower() != exclude_sector.lower(), f"Excluded sector {exclude_sector}"))
    exclude_country = _clean_str(criteria.get("exclude_country"))
    if exclude_country:
        checks.append((country != exclude_country.upper(), f"Excluded country {exclude_country}"))

    # 5. Composite Min
    comp_min = _clean_float(criteria.get("composite_min"))
    if comp_min is not None:
        val = s.composite if s else None
        checks.append((val is not None and val >= comp_min, f"Composite {val} < {comp_min}"))

    # 6. Signal Filter
    sig_filter = _clean_str(criteria.get("signal"))
    if sig_filter:
        val = (s.signal or "").lower() if s else ""
        checks.append((val == sig_filter.lower(), f"Signal is {val} (requested {sig_filter})"))

    # 7. Coverage Min
    cov_min = _clean_float(criteria.get("coverage_min"))
    if cov_min is not None:
        val = s.coverage if s else None
        checks.append((val is not None and val >= int(cov_min), f"Coverage {val} < {cov_min}"))

    # 8. P/E Max
    pe = enriched.get("pe_calc")
    pe_max = _clean_float(criteria.get("pe_max"))
    if pe_max is not None:
        checks.append((pe is not None and 0 < pe <= pe_max, f"PE {pe} > {pe_max} or blank"))

    # 9. P/B Max
    pb = enriched.get("pb_calc")
    pb_max = _clean_float(criteria.get("pb_max"))
    if pb_max is not None:
        checks.append((pb is not None and 0 < pb <= pb_max, f"PB {pb} > {pb_max}"))

    # 10. ROE Min
    roe = enriched.get("roe_calc")
    roe_min = _clean_float(criteria.get("roe_min"))
    if roe_min is not None:
        target_roe = roe_min / 100.0 if roe_min > 1.0 else roe_min
        checks.append((roe is not None and roe >= target_roe, f"ROE {roe} < {target_roe}"))

    # 11. FCF Margin Min
    fcf_m = enriched.get("fcfmargin_calc")
    fcf_min = _clean_float(criteria.get("fcf_margin_min"))
    if fcf_min is not None:
        target_fcf = fcf_min / 100.0 if fcf_min > 1.0 else fcf_min
        checks.append((fcf_m is not None and fcf_m >= target_fcf, f"FCF Margin {fcf_m} < {target_fcf}"))

    # 12. ROIC Min (US-0034)
    roic_min = _clean_float(criteria.get("roic_min"))
    if roic_min is not None:
        roic_val = feats.get("roic_calc")
        target_roic = roic_min / 100.0 if roic_min > 1.0 else roic_min
        checks.append((roic_val is not None and roic_val >= target_roic, f"ROIC {roic_val} < {target_roic}"))

    # 13. Debt to EBITDA Max (US-0011)
    de_max = _clean_float(criteria.get("debt_to_ebitda_max"))
    if de_max is not None:
        de_val = feats.get("debt_to_ebitda_calc")
        checks.append((de_val is not None and de_val <= de_max, f"Debt/EBITDA {de_val} > {de_max}"))

    # 14. Interest Coverage Min (US-0011)
    int_min = _clean_float(criteria.get("interest_coverage_min"))
    if int_min is not None:
        int_val = feats.get("interest_coverage_calc")
        checks.append((int_val is not None and int_val >= int_min, f"Interest coverage {int_val} < {int_min}"))

    # 15. Gross Profitability Min (US-0007 Novy-Marx)
    gp_min = _clean_float(criteria.get("gross_profitability_min"))
    if gp_min is not None:
        gp_val = feats.get("gross_profitability")
        checks.append((gp_val is not None and gp_val >= gp_min, f"Gross Profitability {gp_val} < {gp_min}"))

    # 16. SBC Dilution Min / Max (US-0014)
    sbc_max = _clean_float(criteria.get("sbc_dilution_max"))
    if sbc_max is not None:
        sbc_val = feats.get("sbc_ratio")
        target_sbc = sbc_max / 100.0 if sbc_max > 1.0 else sbc_max
        checks.append((sbc_val is not None and sbc_val <= target_sbc, f"SBC {sbc_val} > {target_sbc}"))
    sbc_min = _clean_float(criteria.get("sbc_dilution_min"))
    if sbc_min is not None:
        sbc_val = feats.get("sbc_ratio")
        target_sbc = sbc_min / 100.0 if sbc_min > 1.0 else sbc_min
        checks.append((sbc_val is not None and sbc_val >= target_sbc, f"SBC {sbc_val} < {target_sbc}"))

    # 17. PEG Max (US-0005 GARP)
    peg_max = _clean_float(criteria.get("peg_max"))
    if peg_max is not None:
        peg_val = feats.get("peg")
        checks.append((peg_val is not None and peg_val <= peg_max, f"PEG {peg_val} > {peg_max}"))

    # 18. Market Cap Band & Thin Coverage (US-0020 Small-cap explorer)
    band_filter = _clean_str(criteria.get("market_cap_band"))
    if band_filter and band_filter.lower() != "all":
        checks.append((feats.get("market_cap_band") == band_filter.lower(), f"Market cap band {feats.get('market_cap_band')} != {band_filter}"))
    if criteria.get("thin_coverage_only") is True or str(criteria.get("thin_coverage_only")).lower() == "true":
        checks.append((feats.get("thin_coverage") is True, "Coverage is not thin (>= 3 pillars)"))

    # 19. Net Cash Only (US-0005 GARP)
    if criteria.get("net_cash_only") is True or str(criteria.get("net_cash_only")).lower() == "true":
        checks.append((feats.get("net_cash") is True, "Does not have net cash (debt > cash)"))

    # 20. Turnaround Only (US-0021)
    if criteria.get("turnaround_only") is True or str(criteria.get("turnaround_only")).lower() == "true":
        checks.append((feats.get("is_turnaround") is True, "Not an earnings turnaround with positive cash flow"))

    # 21. Consecutive Dividend Years (US-0003)
    div_yrs_min = _clean_float(criteria.get("consecutive_div_years_min"))
    if div_yrs_min is not None:
        div_yrs = feats.get("consecutive_div_years")
        checks.append((div_yrs is not None and div_yrs >= int(div_yrs_min), f"Dividend years {div_yrs} < {div_yrs_min}"))

    # 22. Dividend Payout Max (US-0003)
    payout_max = _clean_float(criteria.get("payout_ratio_max"))
    if payout_max is not None:
        p_val = feats.get("payout_ratio")
        checks.append((p_val is not None and 0 < p_val <= payout_max, f"Payout ratio {p_val} > {payout_max}"))

    # 23. FCF Payout Max (US-0033)
    fcf_p_max = _clean_float(criteria.get("fcf_payout_max"))
    if fcf_p_max is not None:
        fcf_p_val = feats.get("fcf_payout")
        checks.append((fcf_p_val is not None and 0 < fcf_p_val <= fcf_p_max, f"FCF Payout {fcf_p_val} > {fcf_p_max}"))

    # 24. 3-Year Revenue CAGR Min (US-0025)
    cagr_min = _clean_float(criteria.get("cagr_rev_3y_min"))
    if cagr_min is not None:
        cagr_val = feats.get("cagr_rev_3y")
        target_cagr = cagr_min / 100.0 if cagr_min > 1.0 else cagr_min
        checks.append((cagr_val is not None and cagr_val >= target_cagr, f"Revenue 3Y CAGR {cagr_val} < {target_cagr}"))

    # 25. Mid-Cycle Operating Margins (US-0035)
    mid_cycle_min = _clean_float(criteria.get("mid_cycle_margin_min"))
    if mid_cycle_min is not None:
        mcm = feats.get("mid_cycle_margin")
        target_mcm = mid_cycle_min / 100.0 if mid_cycle_min > 1.0 else mid_cycle_min
        checks.append((mcm is not None and mcm >= target_mcm, f"Mid-cycle margin {mcm} < {target_mcm}"))
    if criteria.get("mid_cycle_normalized") is True or str(criteria.get("mid_cycle_normalized")).lower() == "true":
        checks.append((feats.get("mid_cycle_normalized") is True, "Operating margin peak exceeds 1.5x mid-cycle baseline"))

    # 26. Drawdown Resilience (US-0048)
    if criteria.get("drawdown_resilient") is True or str(criteria.get("drawdown_resilient")).lower() == "true":
        checks.append((feats.get("drawdown_resilient") is True, "Annual revenue decline exceeded 10%"))

    # 27. Altman Safe Only (US-0022)
    if criteria.get("altman_safe_only") is True or str(criteria.get("altman_safe_only")).lower() == "true":
        checks.append((feats.get("altman_zone") == "Safe", f"Altman zone {feats.get('altman_zone')} is not Safe"))

    # 28. Halal Candidate (US-0004)
    if criteria.get("halal_candidate") is True or str(criteria.get("halal_candidate")).lower() == "true":
        checks.append((hf is not None and hf.status == "halal_candidate", "Not an AAOIFI halal candidate"))

    # 29. Growth History Check
    has_growth_filter = criteria.get("has_growth_history")
    if has_growth_filter is not None and not hasattr(has_growth_filter, "default"):
        is_true = has_growth_filter is True or str(has_growth_filter).lower() == "true"
        dated_years = [h for h in entry["history"] if h.get("fiscal_year") is not None]
        has_growth = (s is not None and s.growth is not None) or len(dated_years) >= 3
        checks.append((has_growth == is_true, f"Growth history is {has_growth}"))

    # 30. Theme Tag Filter (US-0046)
    theme_tag = _clean_str(criteria.get("theme_tag"))
    if theme_tag:
        tags = [str(t).upper() for t in (entry.get("universe_tags") or [])]
        checks.append((theme_tag.upper() in tags, f"Theme tag {theme_tag} not in universe tags {tags}"))
    if not checks:
        return True, []

    if logic == "OR":
        # At least one filter condition must be satisfied
        passed = any(c[0] for c in checks)
        failed_reasons = [c[1] for c in checks if not c[0]]
        return passed, failed_reasons

    # Default AND logic: all specified conditions must pass
    passed = all(c[0] for c in checks)
    failed_reasons = [c[1] for c in checks if not c[0]]
    return passed, failed_reasons


def compute_cohort_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculates statistical summary stats over the matched screen cohort (US-0038)."""
    if not items:
        return {
            "median_composite": None,
            "median_pe": None,
            "median_roe": None,
            "top_sectors": [],
            "count": 0,
        }

    composites = sorted([it["composite"] for it in items if it.get("composite") is not None])
    pes = sorted([it["pe_calc"] for it in items if it.get("pe_calc") is not None and it["pe_calc"] > 0])
    roes = sorted([it["roe_calc"] for it in items if it.get("roe_calc") is not None])

    def _median(arr: list[float]) -> float | None:
        if not arr:
            return None
        n = len(arr)
        mid = n // 2
        return arr[mid] if n % 2 == 1 else round((arr[mid - 1] + arr[mid]) / 2.0, 2)

    sector_counts: dict[str, int] = {}
    for it in items:
        sec = it.get("gics_sector") or "Unclassified"
        sector_counts[sec] = sector_counts.get(sec, 0) + 1

    sorted_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:4]

    return {
        "median_composite": _median(composites),
        "median_pe": _median(pes),
        "median_roe": _median(roes),
        "top_sectors": [{"sector": s[0], "count": s[1], "pct": round(s[1] / len(items) * 100.0, 1)} for s in sorted_sectors],
        "count": len(items),
    }


def diagnose_null_reasons(universe_count: int, criteria: dict[str, Any]) -> dict[str, Any]:
    """Provides honest NULL vs zero-match diagnostic warning (US-0049)."""
    reasons: list[str] = []
    if criteria.get("debt_to_ebitda_max") or criteria.get("interest_coverage_min"):
        reasons.append("Debt and leverage metrics are intentionally omitted for commercial banks & insurers per accounting rules.")
    if criteria.get("consecutive_div_years_min"):
        reasons.append("Multi-year dividend history is not recorded for early-stage or non-dividend issuing growth equities.")
    if criteria.get("peg_max") or criteria.get("cagr_rev_3y_min"):
        reasons.append("Growth CAGR requires at least 3 years of consecutive statement filings.")
    if criteria.get("gross_profitability_min"):
        reasons.append("Gross profitability requires balance sheet total assets and reported gross profit.")
    if criteria.get("fcf_payout_max"):
        reasons.append("FCF dividend payout requires recorded dividends and positive reported Free Cash Flow.")
    if criteria.get("mid_cycle_margin_min") or criteria.get("mid_cycle_normalized"):
        reasons.append("Mid-cycle normalization requires multi-year historical statement filings.")
    if criteria.get("drawdown_resilient"):
        reasons.append("Drawdown resilience calculation requires at least 2 consecutive annual statement periods.")

    explanation = None
    if reasons:
        explanation = (
            f"Active criteria returned 0 names across {universe_count} companies. "
            "This may be caused by conservative NULL data handling rather than true absence of fundamental candidates: "
            + " ".join(reasons)
        )

    return {
        "has_null_data_warning": len(reasons) > 0,
        "null_reasons": reasons,
        "explanation": explanation,
    }


def export_screener_csv(items: list[dict[str, Any]], criteria: dict[str, Any], currency_view: str) -> str:
    """Exports screen results to CSV with formula-transparent columns & metadata comments (US-0012, US-0030)."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # Embedded compliance & criteria metadata header (US-0012)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    writer.writerow([f"# Equity Intelligence Screener Export"])
    writer.writerow([f"# Export Timestamp: {now_iso}"])
    writer.writerow([f"# Currency View: {currency_view} (Cross-border comparisons use unitless ratios only)"])
    writer.writerow([f"# Active Filters: {criteria}"])
    writer.writerow([f"# Methodology: Locked weights 0.30 Quality / 0.25 Value / 0.25 Growth / 0.20 Risk with honest NULL handling"])
    writer.writerow([f"# Disclaimer: Personal research software for a single local user. Not investment advice."])
    writer.writerow([])

    # Header columns with explicit formula definitions (US-0030)
    headers = [
        "Company ID",
        "Ticker",
        "Name",
        "Currency",
        "GICS Sector",
        "Custom Industry",
        "Composite Score [Quality*0.30 + Value*0.25 + Growth*0.25 + Risk*0.20 * Penalty]",
        "Signal",
        "P/E Ratio [Market Price / Diluted EPS]",
        "ROE % [Net Income / Book Equity * 100]",
        "ROIC % [NOPAT / Invested Capital * 100]",
        "FCF Margin % [Free Cash Flow / Total Revenue * 100]",
        "EV/EBITDA [Enterprise Value / EBITDA]",
        "Gross Profitability [Gross Profit / Total Assets]",
        "Net Debt/EBITDA [(Total Debt - Cash) / EBITDA]",
        "Interest Coverage [EBIT / Interest Expense]",
        "3Y Revenue CAGR % [((Rev_t / Rev_t-3)^(1/3) - 1) * 100]",
        "Altman Z-Score [1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5]",
        "Altman Zone [Safe > 2.99 | Grey 1.81-2.99 | Distress < 1.81]",
        "Graham Checklist [P/E * P/B <= 25 or NCAV > 0]",
        "Lynch Checklist [PEG <= 1.2 or ROE >= 14% and D/E <= 0.6]",
        "Greenblatt Checklist [ROIC >= 14% and P/E <= 22]",
        "Piotroski Checklist [F-Score >= 6 or Composite >= 6.5]",
    ]
    writer.writerow(headers)

    for it in items:
        ck = it.get("checklists") or {}
        row = [
            it.get("company_id", ""),
            it.get("ticker", ""),
            it.get("name", ""),
            it.get("currency", ""),
            it.get("gics_sector", ""),
            it.get("custom_industry_sheet", ""),
            f"{it['composite']:.2f}" if it.get("composite") is not None else "",
            it.get("signal", ""),
            f"{it['pe_calc']:.2f}" if it.get("pe_calc") is not None else "",
            f"{it['roe_calc'] * 100:.1f}%" if it.get("roe_calc") is not None else "",
            f"{it['roic_calc'] * 100:.1f}%" if it.get("roic_calc") is not None else "",
            f"{it['fcfmargin_calc'] * 100:.1f}%" if it.get("fcfmargin_calc") is not None else "",
            f"{it['ev_to_ebitda_calc']:.2f}" if it.get("ev_to_ebitda_calc") is not None else "",
            f"{it['gross_profitability']:.3f}" if it.get("gross_profitability") is not None else "",
            f"{it['debt_to_ebitda_calc']:.2f}" if it.get("debt_to_ebitda_calc") is not None else "",
            f"{it['interest_coverage_calc']:.2f}" if it.get("interest_coverage_calc") is not None else "",
            f"{it['cagr_rev_3y'] * 100:.1f}%" if it.get("cagr_rev_3y") is not None else "",
            f"{it['altman_z']:.2f}" if it.get("altman_z") is not None else "",
            it.get("altman_zone", ""),
            "PASS" if ck.get("graham") else "FAIL",
            "PASS" if ck.get("lynch") else "FAIL",
            "PASS" if ck.get("greenblatt") else "FAIL",
            "PASS" if ck.get("piotroski") else "FAIL",
        ]
        writer.writerow(row)

    return output.getvalue()
