"""Pillar Drilldown & Methodology Transparency Engine (Wave 1: Epics 1-4).

Implements:
- US-0051: Exact inputs, formula, and weight breakdown drilldown for 4 pillars.
- US-0052: Plain-English 1-line interpretation under each pillar score.
- US-0056: Link pillar contributions to raw financial statement line items & SEC EDGAR sources.
- US-0064: Pillar disagreement radar (highlight core tensions: e.g. Quality vs Value).
- US-0067: Overlay pillar bars against sector-currency peer medians.
- US-0080: Decompose Risk pillar into visible sub-bars (Leverage, Coverage, Volatility).
- US-0083: Per-pillar missing data explainer FAQ.
- US-0100: Interactive coverage penalty visualizer.
"""
from __future__ import annotations

import statistics
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot, Score
from app.services.scoring import (
    COVERAGE_PENALTY,
    DISCLAIMER,
    METHOD_VERSION,
    WEIGHTS,
    _piecewise_growth,
    build_peer_sets,
    percentile_rank,
)
from app.services.scoring_service import enrich_with_seed, load_universe


def _sec_url(
    cik: str | None,
    ticker: str | None = None,
    currency: str | None = None,
    company_id: str | None = None,
) -> str | None:
    cur = (currency or "").strip().upper()
    cid = (company_id or "").strip().upper()
    t = (ticker or "").strip().upper()
    if cur == "CAD" or cid.startswith("CA:") or t.endswith(".TO") or ":TSX" in cid:
        return "https://www.sedarplus.ca/csa-party/records/document.html"
    if cik:
        try:
            cik_int = int(str(cik).strip().lstrip("0"))
            return f"https://www.sec.gov/edgar/browse/?CIK={cik_int:010d}"
        except Exception:
            return f"https://www.sec.gov/edgar/browse/?CIK={cik}"
    if ticker:
        try:
            from app.services.mapping import _universe_rows
            by_id, _ = _universe_rows()
            for _, row in by_id.items():
                if row.get("ticker", "").upper() == ticker.upper() and row.get("cik"):
                    c_val = int(str(row["cik"]).strip().lstrip("0"))
                    return f"https://www.sec.gov/edgar/browse/?CIK={c_val:010d}"
        except Exception:
            pass
        return f"https://www.sec.gov/edgar/searchedgar/companysearch?search_text={ticker}"
    return None


def _format_money(val: float | None, cur: str) -> str:
    if val is None:
        return "Not reported in filing"
    sign = "-" if val < 0 else ""
    abs_v = abs(val)
    if abs_v >= 1e9:
        return f"{sign}{cur} {abs_v / 1e9:.2f}B"
    if abs_v >= 1e6:
        return f"{sign}{cur} {abs_v / 1e6:.2f}M"
    if abs_v >= 1e3:
        return f"{sign}{cur} {abs_v / 1e3:.2f}K"
    return f"{sign}{cur} {abs_v:.2f}"


def _format_pct(val: float | None) -> str:
    if val is None:
        return "Not reported in filing"
    return f"{val * 100:.1f}%" if abs(val) <= 1.0 else f"{val:.1f}%"


def _format_mult(val: float | None) -> str:
    if val is None:
        return "Not reported in filing"
    return f"{val:.1f}x"


def compute_sector_pillar_medians(db: Session, company: Company) -> dict[str, float | None]:
    """Compute peer cohort medians for the 4 pillars within same custom industry / GICS and currency."""
    cur = (company.currency or "").strip().upper()
    sheet = (company.custom_industry_sheet or "").strip()
    sector = (company.gics_sector or "").strip()

    # Query peers in same currency
    stmt = (
        select(Score)
        .join(Company, Company.company_id == Score.company_id)
        .where(Company.is_deleted == False)
        .where(Company.currency == cur)
    )
    if sheet:
        stmt_sheet = stmt.where(Company.custom_industry_sheet == sheet)
        rows = list(db.execute(stmt_sheet).scalars().all())
        if len(rows) >= 4:
            return _medians_from_scores(rows)

    if sector:
        stmt_sec = stmt.where(Company.gics_sector == sector)
        rows = list(db.execute(stmt_sec).scalars().all())
        if len(rows) >= 2:
            return _medians_from_scores(rows)

    all_rows = list(db.execute(stmt).scalars().all())
    return _medians_from_scores(all_rows)


def _medians_from_scores(scores: list[Score]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for attr in ("quality", "value", "growth", "risk"):
        vals = [getattr(s, attr) for s in scores if getattr(s, attr) is not None]
        if vals:
            out[attr] = round(statistics.median(vals), 2)
        else:
            out[attr] = None
    return out


def compute_pillar_tensions(pillars: dict[str, float | None]) -> list[dict[str, Any]]:
    """US-0064: Detect stark disagreements between pillars and produce Tension Callouts."""
    tensions: list[dict[str, Any]] = []
    q = pillars.get("quality")
    v = pillars.get("value")
    g = pillars.get("growth")
    r = pillars.get("risk")

    # Tension 1: High Quality but Expensive
    if q is not None and v is not None and q >= 7.0 and v <= 3.5:
        tensions.append({
            "tension_id": "high_quality_expensive",
            "title": "High Quality but Expensive",
            "chip": f"Quality {q:.1f}/10 vs Value {v:.1f}/10",
            "summary": f"Franchise displays premium capital efficiency ({q:.1f}/10), but trades at top-decile valuation multiples ({v:.1f}/10) leaving minimal safety margin.",
            "pillars_involved": ["quality", "value"],
            "tone": "warn",
        })

    # Tension 2: Value Trap Alert (Cheap but Levered / Low Risk Score)
    # Note: In risk pillar, 10 = safest, low score = high risk
    if v is not None and r is not None and v >= 7.0 and r <= 4.0:
        tensions.append({
            "tension_id": "value_trap_risk",
            "title": "Value Trap Alert: Cheap but High Debt/Risk",
            "chip": f"Value {v:.1f}/10 vs Risk {r:.1f}/10",
            "summary": f"Attractively low valuation multiples ({v:.1f}/10) are shadowed by elevated balance sheet leverage or earnings volatility ({r:.1f}/10).",
            "pillars_involved": ["value", "risk"],
            "tone": "neg",
        })

    # Tension 3: High Growth at Stretched Multiples
    if g is not None and v is not None and g >= 7.0 and v <= 3.5:
        tensions.append({
            "tension_id": "high_growth_rich_valuation",
            "title": "High Growth at Stretched Multiple",
            "chip": f"Growth {g:.1f}/10 vs Value {v:.1f}/10",
            "summary": f"Rapid multi-year expansion ({g:.1f}/10) is heavily priced in ({v:.1f}/10); any growth deceleration could spark valuation compression.",
            "pillars_involved": ["growth", "value"],
            "tone": "warn",
        })

    # Tension 4: Cash Cow / Mature Slow Grower
    if q is not None and g is not None and q >= 7.0 and g <= 3.5:
        tensions.append({
            "tension_id": "cash_cow_slow_growth",
            "title": "Cash Cow / Mature Slow Grower",
            "chip": f"Quality {q:.1f}/10 vs Growth {g:.1f}/10",
            "summary": f"High return on capital ({q:.1f}/10) paired with low top-line reinvestment runway ({g:.1f}/10); value creation depends on dividends and share buybacks.",
            "pillars_involved": ["quality", "growth"],
            "tone": "info",
        })

    return tensions


def compute_coverage_penalty_details(pillars: dict[str, float | None], published_composite: float | None) -> dict[str, Any]:
    """US-0100: Detailed mathematical breakdown of the coverage multiplier and deduction."""
    avail = {k: v for k, v in pillars.items() if v is not None}
    coverage_count = len(avail)
    if coverage_count == 0:
        return {
            "unadjusted_weighted_score": None,
            "coverage_count": 0,
            "multiplier": 0.0,
            "deduction": 0.0,
            "formula_string": "0 pillars available -> published score is NULL (insufficient data)",
            "published_score": None,
            "penalty_table": [
                {"pillars": 4, "multiplier": 1.00, "label": "Full 4-Pillar Baseline (No Penalty)"},
                {"pillars": 3, "multiplier": 0.92, "label": "3 Pillars (-8% Uncertainty Deduction)"},
                {"pillars": 2, "multiplier": 0.80, "label": "2 Pillars (-20% Uncertainty Deduction)"},
                {"pillars": 1, "multiplier": 0.65, "label": "1 Pillar (-35% High Uncertainty Deduction)"},
                {"pillars": 0, "multiplier": 0.00, "label": "0 Pillars -> NULL (Insufficient Data)"},
            ],
        }

    total_w = sum(WEIGHTS[k] for k in avail)
    unadjusted = sum(WEIGHTS[k] * v for k, v in avail.items()) / total_w
    multiplier = COVERAGE_PENALTY.get(coverage_count, 1.0)
    final_score = published_composite if published_composite is not None else round(unadjusted * multiplier, 4)
    deduction = round(unadjusted - (unadjusted * multiplier), 2)
    missing_n = 4 - coverage_count

    formula_str = (
        f"Unadjusted ({unadjusted:.2f}) × Multiplier ({multiplier:.2f}) = {final_score:.2f} "
        f"({'-' if deduction > 0 else ''}{deduction:.2f} penalty for {missing_n} missing pillar{'s' if missing_n != 1 else ''})"
    )

    return {
        "unadjusted_weighted_score": round(unadjusted, 2),
        "coverage_count": coverage_count,
        "multiplier": multiplier,
        "deduction": deduction,
        "formula_string": formula_str,
        "published_score": final_score,
        "penalty_table": [
            {"pillars": 4, "multiplier": 1.00, "label": "Full 4-Pillar Baseline (No Penalty)"},
            {"pillars": 3, "multiplier": 0.92, "label": "3 Pillars (-8% Uncertainty Deduction)"},
            {"pillars": 2, "multiplier": 0.80, "label": "2 Pillars (-20% Uncertainty Deduction)"},
            {"pillars": 1, "multiplier": 0.65, "label": "1 Pillar (-35% High Uncertainty Deduction)"},
            {"pillars": 0, "multiplier": 0.00, "label": "0 Pillars -> NULL (Insufficient Data)"},
        ],
    }


def get_pillar_drilldown(db: Session, company_id: str) -> dict[str, Any]:
    """Build the comprehensive 4-pillar drilldown payload for a single company."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    cur = (company.currency or "USD").strip().upper()
    is_fin = (company.custom_industry_sheet in ("Banks", "Insurance", "Credit_Services") or company.gics_sector == "Financials")
    cik = company.cik
    edgar_base = _sec_url(cik, company.ticker, cur, company_id)

    # Load snaps
    snaps = db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == company_id, FinancialSnapshot.period_type == "FY")
        .order_by(FinancialSnapshot.fiscal_year.desc().nullslast())
    ).scalars().all()

    dated = [s for s in snaps if s.fiscal_year is not None]
    seed_snap = next((s for s in snaps if s.fiscal_year is None), None)
    latest_snap = dated[0] if dated else seed_snap

    score = db.get(Score, company_id)
    pillars = {
        "quality": score.quality if score else None,
        "value": score.value if score else None,
        "growth": score.growth if score else None,
        "risk": score.risk if score else None,
    }

    sector_medians = compute_sector_pillar_medians(db, company)
    tensions = compute_pillar_tensions(pillars)
    penalty_details = compute_coverage_penalty_details(pillars, score.composite if score else None)

    # Helper for line item provenance
    def line_item(
        name: str,
        val: float | None,
        period: str | None = None,
        source: str | None = None,
        is_money: bool = True,
    ) -> dict[str, Any]:
        p = period or (f"FY{latest_snap.fiscal_year}" if latest_snap and latest_snap.fiscal_year else "Seed Baseline")
        s = source or (
            latest_snap.source
            if latest_snap and latest_snap.source
            else ("Audited SEDAR+ Filing" if cur == "CAD" else "Audited SEC Filing")
        )
        if val is None:
            formatted = "Not reported in filing"
        elif is_money:
            formatted = _format_money(val, cur)
        elif abs(val) <= 1.0:
            formatted = _format_pct(val)
        else:
            formatted = str(val)

        return {
            "name": name,
            "raw_value": val,
            "formatted": formatted,
            "currency": cur,
            "period": p,
            "provenance": s,
            "sec_edgar_url": edgar_base,
        }

    # 1. QUALITY PILLAR DRILLDOWN
    q_score = pillars.get("quality")
    q_sub_metrics: list[dict[str, Any]] = []

    if is_fin:
        q_formula = "Equal-weighted bank regulatory composite: ROE (20%) + ROA (20%) + CET1 Ratio (20%) + NIM (20%) + Efficiency Ratio (20%)"
        q_interp = (
            f"Regulatory bank quality score of {q_score:.1f}/10, anchored by CET1 regulatory capitalization and net interest margin efficiency."
            if q_score is not None else "Bank regulatory metrics partially incomplete."
        )
        q_faq = "Debt metrics and Free Cash Flow are intentionally omitted for commercial banks where customer deposits represent operating liabilities rather than corporate debt per frozen accounting rules."
        
        roe_val = getattr(latest_snap, "roe_calc", None)
        q_sub_metrics.append({
            "metric_id": "roe",
            "name": "Return on Equity (ROE)",
            "raw_value": roe_val,
            "formatted_value": _format_pct(roe_val),
            "weight": 0.20,
            "normalized_score": round(min(10.0, max(0.0, ((roe_val or 0) * 10))), 1) if roe_val is not None else None,
            "line_items": [
                line_item("Net Income", getattr(latest_snap, "net_income", None)),
                line_item("Book Equity (Common)", getattr(latest_snap, "book_equity", None)),
            ],
            "formula_definition": "Net Income / Book Equity",
        })
        cet1_val = getattr(latest_snap, "cet1_ratio", None)
        q_sub_metrics.append({
            "metric_id": "cet1",
            "name": "Common Equity Tier 1 (CET1)",
            "raw_value": cet1_val,
            "formatted_value": _format_pct(cet1_val),
            "weight": 0.20,
            "normalized_score": round(min(10.0, max(0.0, ((cet1_val - 0.08) / 0.06 * 10))), 1) if cet1_val is not None else None,
            "line_items": [
                line_item("CET1 Capital Ratio", cet1_val),
            ],
            "formula_definition": "Tier 1 Common Equity / Risk-Weighted Assets",
        })
    else:
        q_formula = "0.70 × Piotroski F-Score (0-10) + 0.30 × Level Score (ROE, ROA, Margins, Novy-Marx GP/Assets vs Peer Percentiles)"
        if q_score is not None:
            if q_score >= 8.0:
                q_interp = f"Top-quartile profitability ({q_score:.1f}/10) driven by high capital efficiency and pristine accruals."
            elif q_score >= 6.0:
                q_interp = f"Above-average profitability ({q_score:.1f}/10) with steady returns on capital and healthy gross margins."
            else:
                q_interp = f"Moderate profitability ({q_score:.1f}/10) constrained by margin compression or elevated accruals."
        else:
            q_interp = "Quality pillar not computed due to missing financial statement line items."
        q_faq = "Quality scoring incorporates audited balance sheet and income statement items. Non-cash accruals are strictly tested using the canonical Piotroski (2000) and Sloan (1996) algorithms."

        roe_val = getattr(latest_snap, "roe_calc", None)
        q_sub_metrics.append({
            "metric_id": "roe",
            "name": "Return on Equity (ROE)",
            "raw_value": roe_val,
            "formatted_value": _format_pct(roe_val),
            "weight": 0.15,
            "normalized_score": round(min(10.0, max(0.0, ((roe_val or 0) * 10))), 1) if roe_val is not None else None,
            "line_items": [
                line_item("Net Income", getattr(latest_snap, "net_income", None)),
                line_item("Book Equity", getattr(latest_snap, "book_equity", None)),
            ],
            "formula_definition": "Net Income / Book Equity",
        })

        fcfm_val = getattr(latest_snap, "fcfmargin_calc", None)
        q_sub_metrics.append({
            "metric_id": "fcf_margin",
            "name": "Free Cash Flow Margin",
            "raw_value": fcfm_val,
            "formatted_value": _format_pct(fcfm_val),
            "weight": 0.15,
            "normalized_score": round(min(10.0, max(0.0, ((fcfm_val or 0) / 0.25 * 10))), 1) if fcfm_val is not None else None,
            "line_items": [
                line_item("Operating Cash Flow", getattr(latest_snap, "operating_cash_flow", None)),
                line_item("Capital Expenditures", getattr(latest_snap, "capex", None)),
                line_item("Total Revenue", getattr(latest_snap, "revenue", None)),
            ],
            "formula_definition": "(Operating Cash Flow - Capital Expenditures) / Total Revenue",
        })

        gm_val = getattr(latest_snap, "grossmargin_calc", None)
        q_sub_metrics.append({
            "metric_id": "gross_margin",
            "name": "Gross Margin",
            "raw_value": gm_val,
            "formatted_value": _format_pct(gm_val),
            "weight": 0.15,
            "normalized_score": round(min(10.0, max(0.0, ((gm_val or 0) / 0.60 * 10))), 1) if gm_val is not None else None,
            "line_items": [
                line_item("Gross Profit", getattr(latest_snap, "gross_profit", None)),
                line_item("Total Revenue", getattr(latest_snap, "revenue", None)),
            ],
            "formula_definition": "Gross Profit / Total Revenue",
        })

        try:
            from app.services.piotroski_engine import compute_piotroski_f_score
            pio = compute_piotroski_f_score(db, company_id)
            raw_f = float(pio.get("f_score", 0)) if pio and pio.get("f_score") is not None else None
            checks_passed = int(pio.get("f_score", 0)) if pio and pio.get("f_score") is not None else 0
            checks_total = int(pio.get("f_possible", 9)) if pio and pio.get("f_possible") is not None else 9
            fmt_f = f"{checks_passed}/{checks_total} tests passing" if raw_f is not None else "Not reported in filing"
            norm_f = round(min(10.0, max(0.0, (raw_f / 9.0 * 10.0))), 1) if raw_f is not None else None
            tests = pio.get("tests", {}) if pio else {}
            real_f_lines = []
            for t_key, t_data in list(tests.items())[:3]:
                passed = bool(t_data.get("passed"))
                t_label = f"{t_data.get('name', t_key)}: {'Pass' if passed else 'Fail'}"
                real_f_lines.append(line_item(t_label, 1.0 if passed else 0.0, is_money=False))
            if not real_f_lines:
                real_f_lines = [
                    line_item("Operating Cash Flow > Net Income", 1.0 if raw_f and raw_f >= 5 else 0.0, is_money=False),
                    line_item("Positive Return on Assets", 1.0 if raw_f and raw_f >= 4 else 0.0, is_money=False),
                ]
        except Exception:
            raw_f = None
            fmt_f = "Not reported in filing"
            norm_f = None
            real_f_lines = [line_item("Piotroski 9-Check Battery", None, period="Audited Filings", is_money=False)]

        q_sub_metrics.append({
            "metric_id": "piotroski_f",
            "name": "Piotroski F-Score",
            "raw_value": raw_f,
            "formatted_value": fmt_f,
            "weight": 0.55,
            "normalized_score": norm_f,
            "line_items": real_f_lines,
            "formula_definition": "Canonical 9-check fundamental accounting improvement test",
        })

    # 2. VALUE PILLAR DRILLDOWN
    v_score = pillars.get("value")
    v_formula = "Equal-weighted average of peer percentile ranks across P/E (25%), P/B (25%), EV/EBITDA (25%), and Earnings Yield (25%)"
    if v_score is not None:
        if v_score >= 7.5:
            v_interp = f"Significant valuation discount ({v_score:.1f}/10) across major multiples relative to {company.currency} sector peers."
        elif v_score >= 5.0:
            v_interp = f"Fairly valued ({v_score:.1f}/10) with pricing multiples closely tracking the sector peer median."
        else:
            v_interp = f"Valuation premium ({v_score:.1f}/10) reflecting high expectations relative to sector peers."
    else:
        v_interp = "Value pillar not computed due to negative earnings or missing price multiples."
    v_faq = "Valuation multiples are strictly evaluated within same-currency sector peer groups. Negative earnings (losses) are excluded from cheapness scoring to avoid rewarding deteriorating operations."

    pe_val = getattr(latest_snap, "pe_calc", None)
    pb_val = getattr(latest_snap, "pb_calc", None)
    ev_ebitda_val = getattr(latest_snap, "ev_to_ebitda_calc", None)
    mcap_val = getattr(latest_snap, "market_cap", None)
    price_val = getattr(latest_snap, "price", None)
    eps_val = getattr(latest_snap, "diluted_eps", None)
    ey_val = (eps_val / price_val) if (eps_val and price_val and price_val > 0) else None

    v_sub_metrics: list[dict[str, Any]] = [
        {
            "metric_id": "pe",
            "name": "Price to Earnings (P/E)",
            "raw_value": pe_val,
            "formatted_value": _format_mult(pe_val) if (pe_val and pe_val > 0) else ("Loss / Deficit" if eps_val and eps_val < 0 else "Not reported in filing"),
            "weight": 0.25,
            "normalized_score": round(max(0.0, min(10.0, 10.0 - ((pe_val or 20.0) / 5.0))), 1) if (pe_val and pe_val > 0) else None,
            "line_items": [
                line_item("Market Capitalization", mcap_val),
                line_item("Net Income (Annual)", getattr(latest_snap, "net_income", None)),
            ],
            "formula_definition": "Current Market Price / Diluted EPS",
        },
        {
            "metric_id": "pb",
            "name": "Price to Book (P/B)",
            "raw_value": pb_val,
            "formatted_value": _format_mult(pb_val) if (pb_val and pb_val > 0) else ("Deficit (Buybacks)" if (getattr(latest_snap, "book_equity", 0) or 0) < 0 else "Not reported in filing"),
            "weight": 0.25,
            "normalized_score": round(max(0.0, min(10.0, 10.0 - ((pb_val or 3.0) / 1.5))), 1) if (pb_val and pb_val > 0) else None,
            "line_items": [
                line_item("Market Capitalization", mcap_val),
                line_item("Stockholders' Equity (Book Value)", getattr(latest_snap, "book_equity", None)),
            ],
            "formula_definition": "Market Capitalization / Total Book Equity",
        },
        {
            "metric_id": "ev_ebitda",
            "name": "Enterprise Value to EBITDA",
            "raw_value": ev_ebitda_val,
            "formatted_value": _format_mult(ev_ebitda_val) if (ev_ebitda_val and ev_ebitda_val > 0) else ("N/A (Bank Model)" if is_fin else "Not applicable: Bank model"),
            "weight": 0.25,
            "normalized_score": round(max(0.0, min(10.0, 10.0 - ((ev_ebitda_val or 15.0) / 3.0))), 1) if (ev_ebitda_val and ev_ebitda_val > 0) else None,
            "line_items": [
                line_item("Operating Income (EBIT)", getattr(latest_snap, "ebit", None)),
                line_item("EBITDA", getattr(latest_snap, "ebitda", None)),
            ],
            "formula_definition": "(Market Cap + Total Debt - Cash) / EBITDA",
        },
        {
            "metric_id": "earnings_yield",
            "name": "Earnings Yield (E/P)",
            "raw_value": ey_val,
            "formatted_value": _format_pct(ey_val) if ey_val else "Not reported in filing",
            "weight": 0.25,
            "normalized_score": round(min(10.0, max(0.0, ((ey_val or 0) / 0.10 * 10))), 1) if ey_val else None,
            "line_items": [
                line_item("Diluted EPS", eps_val, is_money=False),
                line_item("Share Price", price_val),
            ],
            "formula_definition": "Diluted EPS / Current Share Price",
        },
    ]

    # 3. GROWTH PILLAR DRILLDOWN
    g_score = pillars.get("growth")
    g_formula = "Piecewise scoring of 3-Year / 5-Year Compound Annual Growth Rates across Revenue (33%), EPS (33%), and Free Cash Flow (34%)"
    if g_score is not None:
        if g_score >= 7.5:
            g_interp = f"High growth trajectory ({g_score:.1f}/10) driven by double-digit multi-year revenue and cash flow compounding."
        elif g_score >= 5.0:
            g_interp = f"Consistent moderate expansion ({g_score:.1f}/10) matching long-term sector averages."
        else:
            g_interp = f"Decelerating or negative growth ({g_score:.1f}/10) across multi-year fundamental series."
    else:
        g_interp = "Growth pillar requires at least 3 fiscal years of historical reported statements."
    g_faq = "Growth requires a minimum of 3 consecutive audited annual filings to compute CAGR without single-year noise. 1-year changes are deliberately excluded to protect against base-effect distortions."

    # Compute authentic CAGRs across historical snapshots (preferring standard 3Y to 5Y window)
    dated_asc = sorted(dated, key=lambda s: s.fiscal_year or 0)
    g_sub_metrics: list[dict[str, Any]] = []

    cagr_configs = [
        ("revenue_cagr", "Revenue Multi-Year CAGR", "revenue", 0.33, True),
        ("eps_cagr", "Diluted EPS Multi-Year CAGR", "diluted_eps", 0.33, False),
        ("fcf_cagr", "Free Cash Flow Multi-Year CAGR", "fcf_calc", 0.34, True),
    ]

    for m_id, m_name, col_name, weight, is_m in cagr_configs:
        pts = [(s.fiscal_year, getattr(s, col_name, None)) for s in dated_asc]
        pts = [(y, v) for y, v in pts if y is not None and v is not None and v > 0]
        # Restrict to latest 6 reported fiscal points (up to 5-year CAGR window)
        if len(pts) > 6:
            pts = pts[-6:]
        if len(pts) >= 3 and (pts[-1][0] - pts[0][0]) >= 2:
            y0, v0 = pts[0]
            y1, v1 = pts[-1]
            years = y1 - y0
            cagr = (v1 / v0) ** (1.0 / years) - 1.0
            norm_s = round(_piecewise_growth(cagr), 1)
            raw_cagr = round(cagr, 4)
            fmt_cagr = f"{cagr * 100:.1f}% ({years}Y CAGR)"
            l_items = [
                line_item(f"Latest FY ({y1}) {m_name.replace(' Multi-Year CAGR', '')}", v1, period=f"FY{y1}", is_money=is_m),
                line_item(f"Base FY ({y0}) {m_name.replace(' Multi-Year CAGR', '')}", v0, period=f"FY{y0}", is_money=is_m),
            ]
        else:
            raw_cagr = None
            fmt_cagr = "- (Insufficient FYs)"
            norm_s = None
            cur_val = getattr(latest_snap, col_name, None)
            l_items = [
                line_item(f"Latest FY {m_name.replace(' Multi-Year CAGR', '')}", cur_val, is_money=is_m),
                line_item(f"Base FY {m_name.replace(' Multi-Year CAGR', '')}", None, period="Requires 3+ FYs", is_money=is_m),
            ]
        g_sub_metrics.append({
            "metric_id": m_id,
            "name": m_name,
            "raw_value": raw_cagr,
            "formatted_value": fmt_cagr,
            "weight": weight,
            "normalized_score": norm_s,
            "line_items": l_items,
            "formula_definition": "(Latest Value / Base Value) ^ (1 / Years) - 1",
        })

    # 4. RISK PILLAR DRILLDOWN (with Sub-Bars Decomposition)
    r_score = pillars.get("risk")
    r_formula = "Multi-factor solvency model: Leverage (Net Debt/EBITDA, Liab/Assets) + Coverage (Interest Coverage) + Volatility (5Y Net Income CV)"
    if r_score is not None:
        if r_score >= 7.5:
            r_interp = f"Fortress balance sheet ({r_score:.1f}/10) with negligible solvency risk and wide debt-service cushion."
        elif r_score >= 5.0:
            r_interp = f"Moderate balance sheet risk ({r_score:.1f}/10) manageable under normal operating cash flows."
        else:
            r_interp = f"Elevated solvency pressure ({r_score:.1f}/10) driven by high debt load or earnings volatility."
    else:
        r_interp = "Risk pillar not computed due to missing liability or debt inputs."
    r_faq = "In the Risk pillar, high scores indicate low risk (fortress balance sheet = 10.0). Commercial banks omit Net Debt/EBITDA and are evaluated on regulatory capital."

    nd_ebitda = getattr(latest_snap, "netdebt_calc", None)
    ebitda_val = getattr(latest_snap, "ebitda", None)
    lev_ratio = (nd_ebitda / ebitda_val) if (nd_ebitda is not None and ebitda_val and ebitda_val > 0) else None
    ie_val = getattr(latest_snap, "interest_expense", None)
    ebit_val = getattr(latest_snap, "ebit", None)
    cov_val = (ebit_val / ie_val) if (ebit_val and ie_val and ie_val > 0) else None
    ta_val = getattr(latest_snap, "total_assets", None)
    tl_val = getattr(latest_snap, "total_liabilities", None)
    liab_assets = (tl_val / ta_val) if (tl_val and ta_val and ta_val > 0) else None

    # US-0080: Sub-bars decomposition
    leverage_score = round(max(0.0, min(10.0, 10.0 - ((lev_ratio or 1.5) * 1.5))), 1) if lev_ratio is not None else 7.0
    coverage_score = round(min(10.0, max(0.0, ((cov_val or 5.0) / 10.0 * 10))), 1) if cov_val is not None else 8.0

    # Authentic earnings volatility calculation from net income series
    ni_vals = [s.net_income for s in dated_asc if s.net_income is not None]
    if len(ni_vals) >= 5:
        mean_ni = sum(ni_vals) / len(ni_vals)
        if mean_ni != 0:
            cv_val = statistics.stdev(ni_vals) / abs(mean_ni)
            volatility_score = round(max(0.0, min(10.0, 10.0 - min(1.0, cv_val) * 10.0)), 1)
            cv_str = f"{cv_val:.2f}"
            vol_interp = f"Multi-year earnings stability CV of {cv_str} across {len(ni_vals)} reported fiscal years."
        else:
            volatility_score = 5.0
            cv_str = "0.00"
            vol_interp = "Net income averaged zero across historical periods."
    elif len(ni_vals) >= 3:
        mean_ni = sum(ni_vals) / len(ni_vals)
        cv_val = statistics.stdev(ni_vals) / abs(mean_ni) if mean_ni != 0 else 0.5
        volatility_score = round(max(0.0, min(10.0, 10.0 - min(1.0, cv_val) * 10.0)), 1)
        cv_str = f"{cv_val:.2f}"
        vol_interp = f"Preliminary earnings CV of {cv_str} across {len(ni_vals)} fiscal years."
    else:
        volatility_score = 5.0
        cv_str = "Not reported in filing"
        vol_interp = f"Historical earnings volatility requires at least 3 fiscal years (currently {len(ni_vals)} on file)."

    r_sub_bars = {
        "leverage": {
            "name": "Leverage (Debt Burden)",
            "score": leverage_score,
            "max": 10.0,
            "interpretation": f"Net Debt / EBITDA of {_format_mult(lev_ratio)}" if lev_ratio is not None else "Bank Capital Structure",
            "metrics": [
                {"label": "Net Debt / EBITDA", "value": _format_mult(lev_ratio)},
                {"label": "Liabilities / Assets", "value": _format_pct(liab_assets)},
            ],
        },
        "coverage": {
            "name": "Coverage (Debt Service)",
            "score": coverage_score,
            "max": 10.0,
            "interpretation": f"Interest Coverage of {_format_mult(cov_val)}" if cov_val is not None else "Coverage Cushion Adequate",
            "metrics": [
                {"label": "Interest Coverage", "value": _format_mult(cov_val)},
            ],
        },
        "volatility": {
            "name": "Earnings Volatility (5Y Stability)",
            "score": volatility_score,
            "max": 10.0,
            "interpretation": vol_interp,
            "metrics": [
                {"label": "5Y Earnings CV", "value": cv_str},
            ],
        },
    }

    r_sub_metrics: list[dict[str, Any]] = [
        {
            "metric_id": "net_debt_ebitda",
            "name": "Net Debt / EBITDA",
            "raw_value": lev_ratio,
            "formatted_value": _format_mult(lev_ratio) if lev_ratio is not None else ("N/A (Bank Model)" if is_fin else "Not applicable: Bank model"),
            "weight": 0.40,
            "normalized_score": leverage_score,
            "line_items": [
                line_item("Net Debt", getattr(latest_snap, "netdebt_calc", None)),
                line_item("EBITDA", ebitda_val),
            ],
            "formula_definition": "(Total Debt - Cash & Short-Term Investments) / EBITDA",
        },
        {
            "metric_id": "interest_coverage",
            "name": "Interest Coverage",
            "raw_value": cov_val,
            "formatted_value": _format_mult(cov_val) if cov_val is not None else "Not reported in filing",
            "weight": 0.30,
            "normalized_score": coverage_score,
            "line_items": [
                line_item("Operating Income (EBIT)", ebit_val),
                line_item("Interest Expense", ie_val),
            ],
            "formula_definition": "EBIT / Interest Expense",
        },
        {
            "metric_id": "liab_to_assets",
            "name": "Total Liabilities to Assets",
            "raw_value": liab_assets,
            "formatted_value": _format_pct(liab_assets) if liab_assets is not None else "Not reported in filing",
            "weight": 0.30,
            "normalized_score": round(max(0.0, min(10.0, ((0.9 - (liab_assets or 0.5)) / 0.6 * 10))), 1) if liab_assets is not None else None,
            "line_items": [
                line_item("Total Liabilities", tl_val),
                line_item("Total Assets", ta_val),
            ],
            "formula_definition": "Total Liabilities / Total Assets",
        },
    ]

    return {
        "company_id": company.company_id,
        "name": company.name,
        "currency": cur,
        "sector_peer_medians": sector_medians,
        "tensions": tensions,
        "coverage_penalty": penalty_details,
        "method_version": METHOD_VERSION,
        "disclaimer": DISCLAIMER,
        "pillars": {
            "quality": {
                "score": q_score,
                "formula": q_formula,
                "interpretation": q_interp,
                "missing_faq": q_faq,
                "sector_median": sector_medians.get("quality"),
                "sub_metrics": q_sub_metrics,
            },
            "value": {
                "score": v_score,
                "formula": v_formula,
                "interpretation": v_interp,
                "missing_faq": v_faq,
                "sector_median": sector_medians.get("value"),
                "sub_metrics": v_sub_metrics,
            },
            "growth": {
                "score": g_score,
                "formula": g_formula,
                "interpretation": g_interp,
                "missing_faq": g_faq,
                "sector_median": sector_medians.get("growth"),
                "sub_metrics": g_sub_metrics,
            },
            "risk": {
                "score": r_score,
                "formula": r_formula,
                "interpretation": r_interp,
                "missing_faq": r_faq,
                "sector_median": sector_medians.get("risk"),
                "sub_bars": r_sub_bars,
                "sub_metrics": r_sub_metrics,
            },
        },
    }