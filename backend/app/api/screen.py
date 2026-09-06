"""Screener API: read-only deterministic screening over scores and latest snapshots.

Enhanced for Wave 2 (Epic 7: 28 User Stories):
- Supports canonical literature presets (Graham, Lynch, Greenblatt, Piotroski, etc.)
- Multi-metric AND/OR criteria engine (US-0010)
- Statistical 'Why These Matched' cohort summaries (US-0038)
- 5-year revenue sparklines in pure SVG/CSS (US-0039)
- Academic book checklist scoring (US-0041)
- NULL vs zero-match diagnostic explanation (US-0049)
- Formula-transparent CSV export with audit metadata (US-0012, US-0030)
- Preserves strict currency segregation (no mixed-currency money amounts in ALL view).
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import HalalFlag, Score
from app.services.scoring import DISCLAIMER, METHOD_VERSION
from app.services.scoring_service import enrich_with_seed, load_universe
from app.services.screener_bundle import (
    CANONICAL_PRESETS,
    compute_cohort_summary,
    compute_company_features,
    diagnose_null_reasons,
    evaluate_filter_criteria,
    export_screener_csv,
    fetch_screening_context,
)

router = APIRouter(prefix="/api/v1", tags=["screener"])


def _cache(response: Response) -> None:
    response.headers["Cache-Control"] = "private, max-age=60"


class ScreenItem(BaseModel):
    company_id: str
    name: str | None = None
    ticker: str | None = None
    currency: str | None = None
    gics_sector: str | None = None
    custom_industry_sheet: str | None = None
    composite: float | None = None
    signal: str | None = None
    pe_calc: float | None = None
    roe_calc: float | None = None
    fcfmargin_calc: float | None = None
    peer_rank: int | None = None
    peer_n: int | None = None
    coverage: int | None = None
    has_growth_history: bool = False
    is_bank: bool = False
    halal_status: str | None = None
    money: dict | None = None

    # Wave 2 rich metrics (Epic 7):
    market_cap: float | None = None
    market_cap_band: str | None = None
    roic_calc: float | None = None
    ev_to_ebitda_calc: float | None = None
    debt_to_ebitda_calc: float | None = None
    interest_coverage_calc: float | None = None
    gross_profitability: float | None = None
    sbc_ratio: float | None = None
    cagr_rev_3y: float | None = None
    altman_z: float | None = None
    altman_zone: str | None = None
    is_turnaround: bool = False
    revenue_sparkline: list[float] = []
    checklists: dict[str, bool] = {}


class WhyMatchedSummary(BaseModel):
    median_composite: float | None = None
    median_pe: float | None = None
    median_roe: float | None = None
    top_sectors: list[dict[str, Any]] = []
    count: int = 0


class NullWarning(BaseModel):
    has_null_data_warning: bool = False
    null_reasons: list[str] = []
    explanation: str | None = None


class ScreenOut(BaseModel):
    total: int
    count: int
    currency_view: str
    items: list[ScreenItem]
    method_version: str
    disclaimer: str
    why_matched_summary: WhyMatchedSummary | None = None
    null_warning: NullWarning | None = None


def _is_bank(gics_sector: str | None, custom_industry: str | None) -> bool:
    sec = (gics_sector or "").strip().lower()
    ind = (custom_industry or "").strip().lower()
    if sec == "financials":
        return True
    if "bank" in ind or ind in {"insurance", "credit_services", "financial_services", "diversified_financials"}:
        return True
    return False


def execute_screen(
    db: Session,
    currency: str = "ALL",
    sector: str | None = None,
    industry: str | None = None,
    signal: str | None = None,
    composite_min: float | None = None,
    pe_max: float | None = None,
    pb_max: float | None = None,
    roe_min: float | None = None,
    fcf_margin_min: float | None = None,
    coverage_min: int | None = None,
    has_growth_history: bool | None = None,
    exclude_banks: bool = False,
    preset: str | None = None,
    criteria_logic: str = "AND",
    market_cap_band: str | None = None,
    roic_min: float | None = None,
    ev_ebitda_max: float | None = None,
    debt_to_ebitda_max: float | None = None,
    interest_coverage_min: float | None = None,
    gross_profitability_min: float | None = None,
    sbc_dilution_max: float | None = None,
    peg_max: float | None = None,
    consecutive_div_years_min: int | None = None,
    payout_ratio_max: float | None = None,
    cagr_rev_3y_min: float | None = None,
    turnaround_only: bool | None = None,
    altman_safe_only: bool | None = None,
    theme_tag: str | None = None,
    exclude_sector: str | None = None,
    exclude_country: str | None = None,
    net_cash_only: bool | None = None,
    thin_coverage_only: bool | None = None,
    sbc_dilution_min: float | None = None,
    fcf_payout_max: float | None = None,
    mid_cycle_margin_min: float | None = None,
    mid_cycle_normalized: bool | None = None,
    drawdown_resilient: bool | None = None,
    sort_by: str = "composite",
    sort_dir: str = "desc",
    limit: int = 1000,
    offset: int = 0,
) -> ScreenOut:
    """Core screening logic decoupled from FastAPI Query defaults."""
    cur_up = (currency or "ALL").upper()

    universe = load_universe(db)
    scores = {s.company_id: s for s in db.execute(select(Score)).scalars().all()}
    halal_flags = {h.company_id: h for h in db.execute(select(HalalFlag)).scalars().all()}
    ctx = fetch_screening_context(db)

    # Build active criteria dictionary
    criteria_dict: dict[str, Any] = {
        "currency": cur_up if cur_up != "ALL" else None,
        "sector": sector,
        "industry": industry,
        "signal": signal,
        "composite_min": composite_min,
        "pe_max": pe_max,
        "pb_max": pb_max,
        "roe_min": roe_min,
        "fcf_margin_min": fcf_margin_min,
        "coverage_min": coverage_min,
        "has_growth_history": has_growth_history,
        "exclude_banks": exclude_banks,
        "criteria_logic": criteria_logic.upper() if criteria_logic else "AND",
        "market_cap_band": market_cap_band,
        "roic_min": roic_min,
        "ev_ebitda_max": ev_ebitda_max,
        "debt_to_ebitda_max": debt_to_ebitda_max,
        "interest_coverage_min": interest_coverage_min,
        "gross_profitability_min": gross_profitability_min,
        "sbc_dilution_max": sbc_dilution_max,
        "sbc_dilution_min": sbc_dilution_min,
        "peg_max": peg_max,
        "consecutive_div_years_min": consecutive_div_years_min,
        "payout_ratio_max": payout_ratio_max,
        "fcf_payout_max": fcf_payout_max,
        "cagr_rev_3y_min": cagr_rev_3y_min,
        "turnaround_only": turnaround_only,
        "altman_safe_only": altman_safe_only,
        "theme_tag": theme_tag,
        "exclude_sector": exclude_sector,
        "exclude_country": exclude_country,
        "net_cash_only": net_cash_only,
        "thin_coverage_only": thin_coverage_only,
        "mid_cycle_margin_min": mid_cycle_margin_min,
        "mid_cycle_normalized": mid_cycle_normalized,
        "drawdown_resilient": drawdown_resilient,
    }

    # Merge preset criteria if specified
    if preset:
        p_clean = preset.strip().lower()
        matched_preset = next(
            (p for p in CANONICAL_PRESETS if p["id"] == p_clean or p["name"].lower() == p_clean or p_clean in p["id"]),
            None,
        )
        if matched_preset:
            for k, v in matched_preset["criteria"].items():
                if k == "exclude_banks" and v is True:
                    criteria_dict["exclude_banks"] = True
                elif criteria_dict.get(k) is None:
                    criteria_dict[k] = v

    filtered: list[ScreenItem] = []

    for entry in universe:
        cid = entry["company_id"]
        c_cur = (entry.get("currency") or "").upper()
        c_sec = entry.get("gics_sector")
        c_ind = entry.get("custom_industry_sheet")
        s = scores.get(cid)
        hf = halal_flags.get(cid)
        enriched = enrich_with_seed(entry["snapshot"], entry.get("seed_snapshot"))
        stmts = ctx["statements"].get(cid, [])
        derived = ctx["derived"].get(cid)

        # Compute full suite of quantitative features
        feats = compute_company_features(entry, enriched, s, stmts, derived)

        # Evaluate against active criteria
        passed, _ = evaluate_filter_criteria(entry, s, hf, enriched, feats, criteria_dict)
        if not passed:
            continue

        pe = enriched.get("pe_calc")
        roe = enriched.get("roe_calc")
        fcfmargin = enriched.get("fcfmargin_calc")
        is_bank_company = _is_bank(c_sec, c_ind)

        # Money columns: hidden when ALL, native when USD or CAD (Rule #2)
        money_dict: dict | None = None
        if cur_up != "ALL":
            money_dict = {
                "revenue": enriched.get("revenue"),
                "net_income": enriched.get("net_income"),
                "fcf_calc": enriched.get("fcf_calc"),
                "market_cap": enriched.get("market_cap"),
                "total_debt": enriched.get("total_debt"),
            }

        dated_years = [h for h in entry["history"] if h.get("fiscal_year") is not None]
        has_growth = (s is not None and s.growth is not None) or len(dated_years) >= 3

        filtered.append(
            ScreenItem(
                company_id=cid,
                name=entry.get("name"),
                ticker=cid.split(":")[1] if ":" in cid else cid,
                currency=c_cur,
                gics_sector=c_sec,
                custom_industry_sheet=c_ind,
                composite=s.composite if s else None,
                signal=s.signal if s else None,
                pe_calc=pe,
                roe_calc=roe,
                fcfmargin_calc=fcfmargin,
                peer_rank=s.peer_rank if s else None,
                peer_n=s.peer_n if s else None,
                coverage=s.coverage if s else None,
                has_growth_history=has_growth,
                is_bank=is_bank_company,
                halal_status=hf.status if hf else None,
                money=money_dict,
                market_cap=feats["market_cap"],
                market_cap_band=feats["market_cap_band"],
                roic_calc=feats["roic_calc"],
                ev_to_ebitda_calc=feats["ev_to_ebitda_calc"],
                debt_to_ebitda_calc=feats["debt_to_ebitda_calc"],
                interest_coverage_calc=feats["interest_coverage_calc"],
                gross_profitability=feats["gross_profitability"],
                sbc_ratio=feats["sbc_ratio"],
                cagr_rev_3y=feats["cagr_rev_3y"],
                altman_z=feats["altman_z"],
                altman_zone=feats["altman_zone"],
                is_turnaround=feats["is_turnaround"],
                revenue_sparkline=feats["sparkline"],
                checklists=feats["checklists"],
            )
        )

    # Sort
    reverse = (sort_dir == "desc")

    def _sort_val(item: ScreenItem):
        v = getattr(item, sort_by, None)
        if sort_by == "pe":
            v = item.pe_calc
        elif sort_by == "roe":
            v = item.roe_calc
        elif sort_by == "fcf_margin":
            v = item.fcfmargin_calc
        elif sort_by == "roic":
            v = item.roic_calc
        elif sort_by == "debt_to_ebitda":
            v = item.debt_to_ebitda_calc
        elif sort_by == "ev_ebitda":
            v = item.ev_to_ebitda_calc
        elif sort_by == "gross_profitability":
            v = item.gross_profitability
        elif sort_by == "altman_z":
            v = item.altman_z
        elif sort_by == "market_cap":
            v = item.market_cap

        if v is None:
            return (1, 0)
        return (0, -v if reverse else v) if isinstance(v, (int, float)) else (0, str(v).lower())

    filtered.sort(key=_sort_val)

    total = len(filtered)
    paged = filtered[offset : offset + limit]

    # Compute Statistical Summary (US-0038)
    cohort_dict = compute_cohort_summary([it.model_dump() for it in filtered])
    why_summary = WhyMatchedSummary(**cohort_dict)

    # Compute NULL Diagnostic Warning if zero matches (US-0049)
    null_warning = None
    if total == 0:
        diag = diagnose_null_reasons(len(universe), criteria_dict)
        null_warning = NullWarning(**diag)

    return ScreenOut(
        total=total,
        count=len(paged),
        currency_view=cur_up,
        items=paged,
        method_version=METHOD_VERSION,
        disclaimer=DISCLAIMER,
        why_matched_summary=why_summary,
        null_warning=null_warning,
    )


@router.get("/screen", response_model=ScreenOut, description="Screen the universe with AND/OR filters on scores and snapshot ratios.")
def screen_universe(
    response: Response,
    currency: str = Query(default="ALL", pattern="^(ALL|USD|CAD|all|usd|cad)$"),
    sector: str | None = Query(default=None, description="GICS sector"),
    industry: str | None = Query(default=None, description="Custom industry sheet"),
    signal: str | None = Query(default=None, description="Deterministic score signal"),
    composite_min: float | None = Query(default=None, ge=0.0, le=10.0, description="Minimum composite score"),
    pe_max: float | None = Query(default=None, ge=0.0, description="Maximum P/E (blanks/nulls excluded)"),
    pb_max: float | None = Query(default=None, ge=0.0, description="Maximum P/B"),
    roe_min: float | None = Query(default=None, description="Minimum ROE (e.g. 0.15 or 15)"),
    fcf_margin_min: float | None = Query(default=None, description="Minimum FCF margin (e.g. 0.10 or 10)"),
    coverage_min: int | None = Query(default=None, ge=1, le=4, description="Minimum pillars covered (1-4)"),
    has_growth_history: bool | None = Query(default=None, description="Filter for companies with growth history"),
    exclude_banks: bool | None = Query(default=False, description="Exclude banks and financials"),
    preset: str | None = Query(default=None, description="Certified investment literature preset"),
    criteria_logic: str = Query(default="AND", pattern="^(AND|OR|and|or)$", description="Logic operator for criteria combining (US-0010)"),
    market_cap_band: str | None = Query(default=None, description="Market cap band (micro, small, mid, large) (US-0020)"),
    roic_min: float | None = Query(default=None, description="Minimum ROIC (e.g. 0.15 or 15) (US-0034)"),
    ev_ebitda_max: float | None = Query(default=None, description="Maximum EV/EBITDA multiple"),
    debt_to_ebitda_max: float | None = Query(default=None, description="Maximum Debt-to-EBITDA (US-0011)"),
    interest_coverage_min: float | None = Query(default=None, description="Minimum Interest Coverage (US-0011)"),
    gross_profitability_min: float | None = Query(default=None, description="Minimum Gross Profitability GP/Assets (US-0007)"),
    sbc_dilution_max: float | None = Query(default=None, description="Maximum SBC / Revenue % (US-0014)"),
    sbc_dilution_min: float | None = Query(default=None, description="Minimum SBC / Revenue % (US-0014)"),
    peg_max: float | None = Query(default=None, description="Maximum PEG ratio (US-0005)"),
    consecutive_div_years_min: int | None = Query(default=None, description="Minimum consecutive dividend years (US-0003)"),
    payout_ratio_max: float | None = Query(default=None, description="Maximum dividend payout ratio (US-0003)"),
    fcf_payout_max: float | None = Query(default=None, description="Maximum FCF dividend payout ratio (US-0033)"),
    cagr_rev_3y_min: float | None = Query(default=None, description="Minimum 3-Year revenue CAGR (US-0025)"),
    turnaround_only: bool | None = Query(default=None, description="Filter for earnings turnaround with positive cash flow (US-0021)"),
    altman_safe_only: bool | None = Query(default=None, description="Require Altman Z in Safe zone (US-0022)"),
    theme_tag: str | None = Query(default=None, description="Filter by theme or index tag (US-0046)"),
    exclude_sector: str | None = Query(default=None, description="Exclude a specific sector for diversification (US-0047)"),
    exclude_country: str | None = Query(default=None, description="Exclude country for diversification (US-0047)"),
    net_cash_only: bool | None = Query(default=None, description="Require net cash (cash >= total debt) (US-0005)"),
    thin_coverage_only: bool | None = Query(default=None, description="Require thin coverage (coverage <= 2) (US-0020)"),
    mid_cycle_margin_min: float | None = Query(default=None, description="Minimum mid-cycle operating margin (US-0035)"),
    mid_cycle_normalized: bool | None = Query(default=None, description="Require normalized mid-cycle margin (US-0035)"),
    drawdown_resilient: bool | None = Query(default=None, description="Require drawdown resilience (max revenue decline <= 10%) (US-0048)"),
    sort_by: str = Query(default="composite", pattern="^(composite|name|ticker|currency|signal|pe|roe|fcf_margin|peer_rank|roic|debt_to_ebitda|ev_ebitda|gross_profitability|altman_z|market_cap)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=1000, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    _cache(response)
    return execute_screen(
        db=db,
        currency=currency,
        sector=sector,
        industry=industry,
        signal=signal,
        composite_min=composite_min,
        pe_max=pe_max,
        pb_max=pb_max,
        roe_min=roe_min,
        fcf_margin_min=fcf_margin_min,
        coverage_min=coverage_min,
        has_growth_history=has_growth_history,
        exclude_banks=bool(exclude_banks),
        preset=preset,
        criteria_logic=criteria_logic,
        market_cap_band=market_cap_band,
        roic_min=roic_min,
        ev_ebitda_max=ev_ebitda_max,
        debt_to_ebitda_max=debt_to_ebitda_max,
        interest_coverage_min=interest_coverage_min,
        gross_profitability_min=gross_profitability_min,
        sbc_dilution_max=sbc_dilution_max,
        sbc_dilution_min=sbc_dilution_min,
        peg_max=peg_max,
        consecutive_div_years_min=consecutive_div_years_min,
        payout_ratio_max=payout_ratio_max,
        fcf_payout_max=fcf_payout_max,
        cagr_rev_3y_min=cagr_rev_3y_min,
        turnaround_only=turnaround_only,
        altman_safe_only=altman_safe_only,
        theme_tag=theme_tag,
        exclude_sector=exclude_sector,
        exclude_country=exclude_country,
        net_cash_only=net_cash_only,
        thin_coverage_only=thin_coverage_only,
        mid_cycle_margin_min=mid_cycle_margin_min,
        mid_cycle_normalized=mid_cycle_normalized,
        drawdown_resilient=drawdown_resilient,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/screen/export", summary="Export screen results to CSV with embedded filter metadata and formula transparency (US-0012, US-0030)")
def export_screen(
    currency: str = Query(default="ALL"),
    sector: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    signal: str | None = Query(default=None),
    composite_min: float | None = Query(default=None),
    pe_max: float | None = Query(default=None),
    pb_max: float | None = Query(default=None),
    roe_min: float | None = Query(default=None),
    fcf_margin_min: float | None = Query(default=None),
    coverage_min: int | None = Query(default=None),
    has_growth_history: bool | None = Query(default=None),
    exclude_banks: bool = Query(default=False),
    preset: str | None = Query(default=None),
    criteria_logic: str = Query(default="AND"),
    market_cap_band: str | None = Query(default=None),
    roic_min: float | None = Query(default=None),
    ev_ebitda_max: float | None = Query(default=None),
    debt_to_ebitda_max: float | None = Query(default=None),
    interest_coverage_min: float | None = Query(default=None),
    gross_profitability_min: float | None = Query(default=None),
    sbc_dilution_max: float | None = Query(default=None),
    sbc_dilution_min: float | None = Query(default=None),
    peg_max: float | None = Query(default=None),
    consecutive_div_years_min: int | None = Query(default=None),
    payout_ratio_max: float | None = Query(default=None),
    fcf_payout_max: float | None = Query(default=None),
    cagr_rev_3y_min: float | None = Query(default=None),
    turnaround_only: bool | None = Query(default=None),
    altman_safe_only: bool | None = Query(default=None),
    theme_tag: str | None = Query(default=None),
    exclude_sector: str | None = Query(default=None),
    exclude_country: str | None = Query(default=None),
    net_cash_only: bool | None = Query(default=None),
    thin_coverage_only: bool | None = Query(default=None),
    mid_cycle_margin_min: float | None = Query(default=None),
    mid_cycle_normalized: bool | None = Query(default=None),
    drawdown_resilient: bool | None = Query(default=None),
    sort_by: str = Query(default="composite"),
    sort_dir: str = Query(default="desc"),
    db: Session = Depends(get_session),
) -> Response:
    """Generates an audit-ready CSV export containing metadata header comments and calculation methodology."""
    res = execute_screen(
        db=db,
        currency=currency,
        sector=sector,
        industry=industry,
        signal=signal,
        composite_min=composite_min,
        pe_max=pe_max,
        pb_max=pb_max,
        roe_min=roe_min,
        fcf_margin_min=fcf_margin_min,
        coverage_min=coverage_min,
        has_growth_history=has_growth_history,
        exclude_banks=exclude_banks,
        preset=preset,
        criteria_logic=criteria_logic,
        market_cap_band=market_cap_band,
        roic_min=roic_min,
        ev_ebitda_max=ev_ebitda_max,
        debt_to_ebitda_max=debt_to_ebitda_max,
        interest_coverage_min=interest_coverage_min,
        gross_profitability_min=gross_profitability_min,
        sbc_dilution_max=sbc_dilution_max,
        sbc_dilution_min=sbc_dilution_min,
        peg_max=peg_max,
        consecutive_div_years_min=consecutive_div_years_min,
        payout_ratio_max=payout_ratio_max,
        fcf_payout_max=fcf_payout_max,
        cagr_rev_3y_min=cagr_rev_3y_min,
        turnaround_only=turnaround_only,
        altman_safe_only=altman_safe_only,
        theme_tag=theme_tag,
        exclude_sector=exclude_sector,
        exclude_country=exclude_country,
        net_cash_only=net_cash_only,
        thin_coverage_only=thin_coverage_only,
        mid_cycle_margin_min=mid_cycle_margin_min,
        mid_cycle_normalized=mid_cycle_normalized,
        drawdown_resilient=drawdown_resilient,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=1000,
        offset=0,
    )

    criteria: dict[str, Any] = {
        k: v
        for k, v in {
            "currency": currency,
            "preset": preset,
            "sector": sector,
            "industry": industry,
            "signal": signal,
            "composite_min": composite_min,
            "pe_max": pe_max,
            "pb_max": pb_max,
            "roe_min": roe_min,
            "fcf_margin_min": fcf_margin_min,
            "coverage_min": coverage_min,
            "exclude_banks": exclude_banks,
            "criteria_logic": criteria_logic,
            "roic_min": roic_min,
            "debt_to_ebitda_max": debt_to_ebitda_max,
            "gross_profitability_min": gross_profitability_min,
            "market_cap_band": market_cap_band,
            "turnaround_only": turnaround_only,
            "theme_tag": theme_tag,
        }.items()
        if v is not None and v is not False
    }

    csv_data = export_screener_csv([it.model_dump() for it in res.items], criteria, res.currency_view)
    filename = f"screener_export_{currency.lower()}_{preset or 'custom'}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
