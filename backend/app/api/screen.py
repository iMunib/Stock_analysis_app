"""Screener API: read-only deterministic screening over scores and latest snapshots.

No FX conversion. currency=ALL returns scores and ratios together with money columns
hidden (never blended across currencies). Single-currency modes (USD/CAD) include native
money metrics.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import HalalFlag, Score
from app.services.scoring import DISCLAIMER, METHOD_VERSION
from app.services.scoring_service import enrich_with_seed, load_universe

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


class ScreenOut(BaseModel):
    total: int
    count: int
    currency_view: str
    items: list[ScreenItem]
    method_version: str
    disclaimer: str


def _is_bank(gics_sector: str | None, custom_industry: str | None) -> bool:
    sec = (gics_sector or "").strip().lower()
    ind = (custom_industry or "").strip().lower()
    if sec == "financials":
        return True
    if "bank" in ind or ind in {"insurance", "credit_services", "financial_services", "diversified_financials"}:
        return True
    return False


@router.get("/screen", response_model=ScreenOut, description="Screen the universe with AND filters on scores and snapshot ratios.")
def screen_universe(
    response: Response,
    currency: str = Query(default="ALL", pattern="^(ALL|USD|CAD|all|usd|cad)$"),
    sector: str | None = Query(default=None, description="GICS sector"),
    industry: str | None = Query(default=None, description="Custom industry sheet"),
    signal: str | None = Query(default=None, description="Deterministic score signal"),
    composite_min: float | None = Query(default=None, ge=0.0, le=10.0, description="Minimum composite score"),
    pe_max: float | None = Query(default=None, ge=0.0, description="Maximum P/E (blanks/nulls excluded)"),
    roe_min: float | None = Query(default=None, description="Minimum ROE (e.g. 0.15 or 15)"),
    fcf_margin_min: float | None = Query(default=None, description="Minimum FCF margin (e.g. 0.10 or 10)"),
    coverage_min: int | None = Query(default=None, ge=1, le=4, description="Minimum pillars covered (1-4)"),
    has_growth_history: bool | None = Query(default=None, description="Filter for companies with growth history"),
    exclude_banks: bool | None = Query(default=False, description="Exclude banks and financials"),
    preset: str | None = Query(default=None, description="Certified investment literature preset (Task 4.1)"),
    sort_by: str = Query(default="composite", pattern="^(composite|name|ticker|currency|signal|pe|roe|fcf_margin|peer_rank)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=1000, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    _cache(response)
    cur_up = currency.upper()

    universe = load_universe(db)
    scores = {s.company_id: s for s in db.execute(select(Score)).scalars().all()}
    halal_flags = {h.company_id: h for h in db.execute(select(HalalFlag)).scalars().all()}

    # Normalize ratio filters (handle percentage input like 15 for 0.15)
    target_roe: float | None = None
    if roe_min is not None:
        target_roe = roe_min / 100.0 if roe_min > 1.0 else roe_min

    target_fcf: float | None = None
    if fcf_margin_min is not None:
        target_fcf = fcf_margin_min / 100.0 if fcf_margin_min > 1.0 else fcf_margin_min

    filtered: list[ScreenItem] = []

    for entry in universe:
        cid = entry["company_id"]
        c_cur = (entry.get("currency") or "").upper()
        c_sec = entry.get("gics_sector")
        c_ind = entry.get("custom_industry_sheet")
        s = scores.get(cid)
        hf = halal_flags.get(cid)

        # 1. Currency filter (USD | CAD | ALL)
        if cur_up != "ALL" and c_cur != cur_up:
            continue

        # 2. Sector filter (GICS)
        if sector and (c_sec or "").strip().lower() != sector.strip().lower():
            continue

        # 3. Industry filter (custom sheet)
        if industry and (c_ind or "").strip().lower() != industry.strip().lower():
            continue

        # 4. Signal filter
        if signal and (s is None or (s.signal or "").strip().lower() != signal.strip().lower()):
            continue

        # 5. Composite min
        if composite_min is not None:
            if s is None or s.composite is None or s.composite < composite_min:
                continue

        # 6. Coverage min
        if coverage_min is not None:
            if s is None or s.coverage is None or s.coverage < coverage_min:
                continue

        # Snapshot data & ratios
        enriched = enrich_with_seed(entry["snapshot"], entry.get("seed_snapshot"))
        pe = enriched.get("pe_calc")
        roe = enriched.get("roe_calc")
        fcfmargin = enriched.get("fcfmargin_calc")

        # 7. PE max (blank excluded)
        if pe_max is not None:
            if pe is None or pe <= 0 or pe > pe_max:
                continue

        # 8. ROE min
        if target_roe is not None:
            if roe is None or roe < target_roe:
                continue

        # 9. FCF margin min
        if target_fcf is not None:
            if fcfmargin is None or fcfmargin < target_fcf:
                continue

        # 10. Growth history
        dated_years = [h for h in entry["history"] if h.get("fiscal_year") is not None]
        has_growth = (s is not None and s.growth is not None) or len(dated_years) >= 3
        if has_growth_history is True and not has_growth:
            continue
        if has_growth_history is False and has_growth:
            continue

        # 11. Exclude banks
        is_bank_company = _is_bank(c_sec, c_ind)
        if exclude_banks and is_bank_company:
            continue

        # 12. Certified Literature Presets (Phase 4 Task 4.1)
        if preset:
            p_lower = preset.strip().lower()
            if p_lower in ("greenblatt_magic_formula", "greenblatt"):
                # Top Return on Capital + Top Earnings Yield
                pcts = s.percentiles_json or {} if s else {}
                qual_pct = pcts.get("roe") or (roe * 100.0 if roe else None)
                val_pct = pcts.get("pe_ratio")
                if qual_pct is not None and qual_pct < 70:
                    continue
                if (roe is None or roe < 0.15) or (pe is None or pe <= 0 or pe > 25.0):
                    continue
            elif p_lower in ("graham_net_net_bargains", "graham", "graham_net_nets"):
                ca = enriched.get("current_assets") or 0.0
                tl = enriched.get("total_liabilities") or 0.0
                mcap = enriched.get("market_cap") or 0.0
                ncav = ca - tl
                if ncav <= 0 or mcap <= 0 or mcap > ncav:
                    continue
            elif p_lower in ("peter_lynch_growth_compounders", "peter_lynch", "lynch"):
                tot_debt = enriched.get("total_debt") or 0.0
                equity = enriched.get("book_equity") or 0.0
                de = (tot_debt / equity) if equity > 0 else 1.0
                if (roe is None or roe < 0.15) or de > 0.5:
                    continue
            elif p_lower in ("piotroski_high_quality_turnarounds", "piotroski"):
                if s is None or s.composite is None or s.composite < 6.0:
                    continue
            elif p_lower in ("true_shareholder_yield_leaders", "shareholder_yield", "tsy"):
                pcts = s.percentiles_json or {} if s else {}
                tsy = pcts.get("total_shareholder_yield")
                if tsy is None or tsy < 6.0:
                    continue
            elif p_lower in ("aaoifi_halal_candidates", "halal", "spus"):
                if hf is None or hf.status != "halal_candidate":
                    continue

        # Money columns: hidden when ALL, native when USD or CAD
        money_dict: dict | None = None
        if cur_up != "ALL":
            money_dict = {
                "revenue": enriched.get("revenue"),
                "net_income": enriched.get("net_income"),
                "fcf_calc": enriched.get("fcf_calc"),
                "market_cap": enriched.get("market_cap"),
                "total_debt": enriched.get("total_debt"),
            }

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

        # Nulls always sort last regardless of asc/desc
        if v is None:
            return (1, 0)
        return (0, -v if reverse else v) if isinstance(v, (int, float)) else (0, str(v).lower())

    filtered.sort(key=_sort_val)

    total = len(filtered)
    paged = filtered[offset : offset + limit]

    return ScreenOut(
        total=total,
        count=len(paged),
        currency_view=cur_up,
        items=paged,
        method_version=METHOD_VERSION,
        disclaimer=DISCLAIMER,
    )
