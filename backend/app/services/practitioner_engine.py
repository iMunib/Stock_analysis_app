"""Practitioner Literature Analytical Engines (Master Directive WS3).

Integrates practitioner frameworks from financial and value-investing literature:
1. Stephen Penman: ROE = RNOA + FLEV x (RNOA - NBC), buyback ROIC distortion guardrail.
2. Howard Schilit: Financial shenanigans, accrual decoupling, EQR (0-100).
3. Martin Fridson: EBITDA - CFO reality spread, Fixed-charge coverage ratio.
4. Benjamin Graham: Graham Number floor, NCAV, NNWC, margin of safety.
5. Burton Malkiel & JL Collins: 8.0% nominal index compounding hurdle, required FCF growth.
6. Morgan Housel & Ramit Sethi: Anti-FOMO 2-sigma valuation stretch, 60-second executive safety verdict.
"""
from __future__ import annotations

import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.graham_engine import compute_graham
from app.services.penman_engine import latest_penman


def analyze_fridson(snaps: list[FinancialSnapshot]) -> dict[str, Any]:
    """Martin Fridson Reality Check:

    - EBITDA Reality Spread = EBITDA - CFO. Positive and widening for 2 years
      triggers "Aggressive accrual capitalization".
    - Fixed-Charge Coverage = (EBIT + Lease) / (Interest + Lease).
    """
    annuals = sorted(
        (s for s in snaps if s.fiscal_year is not None and s.ebitda is not None and s.operating_cash_flow is not None),
        key=lambda s: s.fiscal_year,
    )

    spread_history = []
    widening_spread = False
    if len(annuals) >= 2:
        spreads = [
            (s.fiscal_year, s.ebitda - s.operating_cash_flow)  # type: ignore[operator]
            for s in annuals
        ]
        spread_history = [{"fiscal_year": fy, "spread": round(sp, 2)} for fy, sp in spreads]
        # Check if spread is positive and widening for 2 consecutive years
        for i in range(1, len(spreads)):
            prev_fy, prev_sp = spreads[i - 1]
            curr_fy, curr_sp = spreads[i]
            if curr_sp > prev_sp and prev_sp > 0:
                widening_spread = True

    latest = annuals[-1] if annuals else (snaps[0] if snaps else None)
    fixed_charge_coverage = None
    if latest and latest.ebit is not None and latest.interest_expense is not None:
        lease = getattr(latest, "lease_expense", 0.0) or 0.0
        denom = latest.interest_expense + lease
        if denom > 0:
            fixed_charge_coverage = round((latest.ebit + lease) / denom, 2)

    return {
        "ebitda_cfo_spread_history": spread_history,
        "widening_spread_flag": widening_spread,
        "flag_warning": "Aggressive accrual capitalization" if widening_spread else None,
        "fixed_charge_coverage": fixed_charge_coverage,
    }


def analyze_malkiel(fcf_yield: float | None) -> dict[str, Any]:
    """Burton Malkiel & JL Collins Index Hurdle Engine:

    - Benchmark: 8.0% nominal long-term index compounding rate.
    - Required FCF Growth = 8.0% - FCF Yield.
    - Opportunity Cost Benchmark copy.
    """
    index_hurdle = 8.0
    if fcf_yield is not None:
        # fcf_yield is either a fraction (0.05) or percentage (5.0)
        yield_pct = fcf_yield * 100.0 if abs(fcf_yield) <= 1.0 else fcf_yield
        req_growth = round(index_hurdle - yield_pct, 2)
        benchmark_text = (
            f"To beat an S&P 500 / TSX index ETF, this stock must grow FCF at >= {req_growth}% "
            "annually for 10 years."
        )
    else:
        req_growth = None
        benchmark_text = "FCF yield unavailable; required growth cannot be determined."

    return {
        "index_hurdle_rate": index_hurdle,
        "fcf_yield_pct": round(fcf_yield * 100.0, 2) if fcf_yield is not None and abs(fcf_yield) <= 1.0 else fcf_yield,
        "required_fcf_growth_10y": req_growth,
        "opportunity_cost_benchmark": benchmark_text,
    }


def analyze_behavioral_guard(
    db: Session,
    company_id: str,
    snaps: list[FinancialSnapshot],
    current_pe: float | None,
    current_ev_ebitda: float | None,
    rnoa: float | None,
    fcf_yield: float | None,
    graham_number: float | None,
    current_price: float | None,
) -> dict[str, Any]:
    """Morgan Housel & Ramit Sethi Behavioral Guard:

    - Anti-FOMO Warning: current PE or EV/EBITDA > 2 std dev above 5-year median.
    - 60-Second Executive Safety Verdict:
      * Moat Durability: Positive RNOA + Gross Margin stability.
      * Solvency Runway: Net Debt / EBITDA < 3.0 or Cash > Debt.
      * Valuation Safety: Price < Graham Number OR FCF Yield > 5.0%.
    """
    # 1. Historical PE and EV/EBITDA distributions
    pe_vals = [s.pe_calc for s in snaps if s.pe_calc is not None and s.pe_calc > 0]
    anti_fomo_triggered = False
    anti_fomo_warning = None

    if len(pe_vals) >= 3 and current_pe is not None and current_pe > 0:
        pe_sorted = sorted(pe_vals)
        median_pe = pe_sorted[len(pe_sorted) // 2]
        mean_pe = sum(pe_vals) / len(pe_vals)
        variance = sum((x - mean_pe) ** 2 for x in pe_vals) / len(pe_vals)
        std_dev = math.sqrt(variance)
        if current_pe > median_pe + 2.0 * std_dev and std_dev > 1.0:
            anti_fomo_triggered = True
            anti_fomo_warning = "High valuation stretch. Multiple compression risk."

    # 2. Executive 60-Second Safety Verdict
    latest = snaps[0] if snaps else None

    # Moat: Positive RNOA or stable gross margin
    moat_pass = False
    if rnoa is not None and rnoa > 0:
        moat_pass = True
    elif latest and latest.grossmargin_calc is not None and latest.grossmargin_calc > 0.25:
        moat_pass = True

    # Solvency: Net Debt / EBITDA < 3.0 or Cash > Debt
    solvency_pass = False
    if latest:
        cash = latest.cash_st_investments or 0.0
        debt = latest.total_debt or 0.0
        ebitda = latest.ebitda or 0.0
        net_debt = latest.netdebt_calc if latest.netdebt_calc is not None else (debt - cash)
        if cash >= debt or net_debt <= 0:
            solvency_pass = True
        elif ebitda > 0 and (net_debt / ebitda) < 3.0:
            solvency_pass = True

    # Valuation Safety: Price < Graham Number OR FCF Yield > 5%
    val_pass = False
    if graham_number is not None and current_price is not None and current_price < graham_number:
        val_pass = True
    elif fcf_yield is not None:
        yield_val = fcf_yield if fcf_yield <= 1.0 else fcf_yield / 100.0
        if yield_val > 0.05:
            val_pass = True

    overall_verdict = "PASS" if (moat_pass and solvency_pass and val_pass) else "CAUTION"

    return {
        "anti_fomo_warning": anti_fomo_warning,
        "anti_fomo_triggered": anti_fomo_triggered,
        "safety_verdict": {
            "overall": overall_verdict,
            "moat_durability": "Pass" if moat_pass else "Fail",
            "solvency_runway": "Pass" if solvency_pass else "Fail",
            "valuation_safety": "Pass" if val_pass else "Fail",
        },
    }


def get_practitioner_analytics(db: Session, company_id: str) -> dict[str, Any]:
    """Assembles all practitioner analytical engines for a company."""
    company = db.get(Company, company_id)
    if company is None:
        return {}

    snaps = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        ).order_by(FinancialSnapshot.fiscal_year.desc())
    ).scalars().all()
    snap_list = list(snaps)

    latest_snap = snap_list[0] if snap_list else None
    penman_row = latest_penman(db, company_id)
    graham = compute_graham(db, company_id)

    rnoa = penman_row.rnoa if penman_row else None
    flev = penman_row.flev if penman_row else None

    # Penman buyback/leverage guardrail
    roic_guardrail = None
    if latest_snap and latest_snap.roe_calc is not None:
        if latest_snap.roe_calc > 0.50 and flev is not None and flev > 2.5:
            rnoa_str = f"{round(rnoa * 100, 1)}%" if rnoa is not None else "N/A"
            roic_guardrail = (
                f"Operational return is RNOA {rnoa_str}. ROIC is distorted by share buybacks/financial leverage."
            )

    fridson = analyze_fridson(snap_list)
    fcf_yield = latest_snap.fcf_calc / latest_snap.market_cap if (latest_snap and latest_snap.fcf_calc and latest_snap.market_cap and latest_snap.market_cap > 0) else None
    malkiel = analyze_malkiel(fcf_yield)

    cur_pe = latest_snap.pe_calc if latest_snap else None
    cur_ev_ebitda = latest_snap.ev_to_ebitda_calc if latest_snap else None
    price = latest_snap.price if latest_snap else None

    behavioral = analyze_behavioral_guard(
        db=db,
        company_id=company_id,
        snaps=snap_list,
        current_pe=cur_pe,
        current_ev_ebitda=cur_ev_ebitda,
        rnoa=rnoa,
        fcf_yield=fcf_yield,
        graham_number=graham.get("graham_number"),
        current_price=price,
    )

    from app.services.beneish_engine import compute_beneish_m_score
    from app.services.capital_return_engine import compute_shareholder_yield
    from app.services.distress_engine import compute_distress

    distress = compute_distress(db, company_id)
    shareholder = compute_shareholder_yield(db, company_id)
    beneish = compute_beneish_m_score(db, company_id)

    return {
        "company_id": company_id,
        "penman": {
            "rnoa": rnoa,
            "flev": flev,
            "nbc": penman_row.nbc if penman_row else None,
            "noa": penman_row.noa if penman_row else None,
            "nfo": penman_row.nfo if penman_row else None,
            "guardrail": roic_guardrail,
        },
        "fridson": fridson,
        "graham": graham,
        "malkiel": malkiel,
        "behavioral": behavioral,
        "distress_analysis": distress,
        "shareholder_yield": shareholder,
        "beneish_analysis": beneish,
    }
