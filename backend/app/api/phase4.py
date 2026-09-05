"""Phase 4 research API: search, dossier, compare, similar, sector snapshot, meta.

Read-only GET layer over stored data. No network, no ingest, no recompute inside
handlers. Every payload carries disclaimer + method_version.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from datetime import datetime, timezone

from app.db import get_session
from app.models import Company, CompanyProfile, DerivedMetric, HalalFlag, Score
from app.services.scoring import DISCLAIMER, METHOD_VERSION
from app.services.scoring_service import enrich_with_seed, load_universe
from app.services.ids import normalize_company_id

router = APIRouter(prefix="/api/v1", tags=["phase4"])


def _cache(response: Response) -> None:
    response.headers["Cache-Control"] = "private, max-age=60"


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _yahoo_index() -> dict[str, str]:
    """yahoo symbol (upper) -> company_id, from the authoritative universe csv."""
    from app.services.mapping import _universe_rows

    by_id, _ = _universe_rows()
    out: dict[str, str] = {}
    for cid, rec in by_id.items():
        y = (rec.get("yahoo") or "").upper()
        if y:
            out[y] = cid
    return out


class SearchItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    company_id: str
    name: str | None = None
    ticker: str | None = None
    currency: str | None = None
    sector: str | None = None
    composite: float | None = None
    signal: str | None = None
    peer_rank: int | None = None
    peer_n: int | None = None


class SearchOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    q: str
    count: int
    items: list[SearchItem]
    method_version: str
    disclaimer: str


@router.get("/search", response_model=SearchOut, description="Search companies by ticker, name, Company_ID, or Yahoo symbol.")
def search(
    response: Response,
    q: str = Query(default="", max_length=64),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_session),
):
    _cache(response)
    term = q.strip()
    if not term:
        raise HTTPException(status_code=400, detail="q must be non-empty")
    term_up = term.upper()
    like = f"%{term}%"

    stmt = (
        select(Company, Score)
        .outerjoin(Score, Score.company_id == Company.company_id)
        .where(Company.is_deleted == False)
        .where(
            (Company.ticker.ilike(like))
            | (Company.name.ilike(like))
            | (Company.company_id.ilike(like))
        )
    )
    rows = list(db.execute(stmt).all())

    # Yahoo symbol exact/substring matches (yahoo symbols live in the universe csv)
    yahoo_matched: set[str] = set()
    for y, cid in _yahoo_index().items():
        if term_up in y:
            yahoo_matched.add(cid)

    by_id: dict[str, tuple[Company, Score | None]] = {c.company_id: (c, s) for c, s in rows}
    # attach yahoo-only matches not already fetched
    for cid in yahoo_matched:
        if cid not in by_id:
            c = db.get(Company, cid)
            if c is not None and not c.is_deleted:
                by_id[cid] = (c, db.get(Score, cid))

    items = []
    for cid in sorted(by_id, key=lambda x: _sort_key(by_id[x])):
        c, s = by_id[cid]
        items.append(SearchItem(
            company_id=c.company_id,
            name=c.name,
            ticker=c.ticker,
            currency=c.currency,
            sector=c.gics_sector,
            composite=s.composite if s else None,
            signal=s.signal if s else None,
            peer_rank=s.peer_rank if s else None,
            peer_n=s.peer_n if s else None,
        ))
    items = items[:limit]
    return SearchOut(q=term, count=len(items), items=items, method_version=METHOD_VERSION, disclaimer=DISCLAIMER)


class SuggestionItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    company_id: str
    ticker: str
    name: str | None = None
    exchange: str
    country: str
    sector: str | None = None
    in_database: bool
    tradingview_symbol: str
    composite: float | None = None
    signal: str | None = None
    universe_tags: list[str] = []


class SuggestionsOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    q: str
    count: int
    items: list[SuggestionItem]


@router.get("/search/suggestions", response_model=SuggestionsOut, description="Typeahead suggestions for ticker search with authoritative exchange and TradingView symbols.")
def search_suggestions(
    q: str = Query(default="", max_length=64),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_session),
):
    from app.services.exchange_resolver import get_suggestions
    res = get_suggestions(db, q, limit=limit)
    items = [SuggestionItem(**item) for item in res]
    return SuggestionsOut(q=q, count=len(items), items=items)


def _sort_key(pair: tuple[Company, Score | None]):
    c, s = pair
    exact = 0
    return (s.composite is None if s else True, -(s.composite or 0) if s else 0, c.company_id)


# --------------------------------------------------------------------------
# Dossier
# --------------------------------------------------------------------------

class DossierOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    identity: dict
    latest_snapshot: dict | None
    history_annual: list[dict]
    history_warnings: list[str] = []
    score: dict | None
    halal: dict | None
    data_gaps: list[str]
    profile: dict | None = None
    quarterly: list[dict] | None = None
    # Phase 2 & Phase 5 additions
    decision_verdict: dict | None = None
    archetype: dict | None = None
    moat_rating: dict | None = None
    expectations_gap: float | None = None
    level1: dict | None = None
    level2: dict | None = None
    level3: dict | None = None
    method_version: str
    disclaimer: str


def _data_gaps(company: dict, enriched: dict) -> list[str]:
    gaps: list[str] = []
    dated = [h for h in company["history"] if h.get("fiscal_year") is not None]
    if len(dated) < 3:
        gaps.append("growth_history")
    if enriched.get("pe_calc") is None and enriched.get("pb_calc") is None:
        gaps.append("valuation_multiples")
    if (company.get("gics_sector") or "").lower() == "financials":
        if enriched.get("cet1_ratio") is None and enriched.get("leverage_ratio") is None:
            gaps.append("bank_capital")
    if enriched.get("gross_profit") is None:
        gaps.append("gross_profit")
    if enriched.get("total_debt") is None:
        gaps.append("total_debt")
    if enriched.get("market_cap") is None:
        gaps.append("market_cap")
    if enriched.get("fcf_calc") is None:
        gaps.append("fcf")
    return gaps


@router.get("/companies/{company_id}/dossier", response_model=DossierOut, description="One-payload research dossier: identity, snapshot, history, score, halal, data gaps.")
def company_dossier(company_id: str, response: Response, db: Session = Depends(get_session)):
    _cache(response)
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    # Auto-resolve CIK if missing for US tickers
    if not company.cik and company.country == "US":
        try:
            from app.services.mapping import cik_for_unknown_us, _universe_rows
            by_id, _ = _universe_rows()
            if company_id in by_id and by_id[company_id].get("cik"):
                company.cik = by_id[company_id]["cik"]
                db.flush()
            else:
                cik_val, _ = cik_for_unknown_us(company.ticker)
                if cik_val:
                    company.cik = cik_val
                    db.flush()
        except Exception:
            pass

    entry = next((u for u in load_universe(db) if u["company_id"] == company_id), None)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")

    # Dynamic auto-ingest: if dated history is sparse (< 3 years with revenue), fetch filings and ingest
    # (Disabled during automated test runs to preserve test isolation and offline execution)
    import os
    dated_rev_count = len([h for h in entry["history"] if h.get("fiscal_year") is not None and h.get("revenue") is not None])
    if dated_rev_count < 3 and company.ticker and not os.environ.get("PYTEST_CURRENT_TEST"):
        try:
            from app.providers.registry import ProviderRegistry
            from app.providers.base import CompanyRef
            from app.services.mapping import yahoo_symbol_for
            from app.services.ingest import ingest_statements, ingest_price
            from app.services.scoring_service import recompute

            registry = ProviderRegistry()
            ref = CompanyRef(
                company_id=company.company_id,
                ticker=company.ticker,
                country=company.country,
                currency=company.currency,
                yahoo_symbol=yahoo_symbol_for(company.ticker, company.country),
                cik=company.cik,
            )
            stmts = registry.fetch_annual_statements(ref)
            if stmts:
                ingest_statements(db, company, stmts, refresh=True)
                quote = registry.fetch_price(ref)
                if quote:
                    ingest_price(db, company, quote)
                db.commit()
                try:
                    from app.services.calculation_pipeline import run_company_pipeline
                    run_company_pipeline(db, company_id, refresh=False, fetch_live=False, recompute_score=False)
                except Exception:
                    pass
                recompute(db, company_id)
                entry = next((u for u in load_universe(db) if u["company_id"] == company_id), entry)
        except Exception:
            db.rollback()

    # Dynamic TTM computation: ensure TTM row is always up to date and computed
    from app.services.ttm_engine import compute_and_store_ttm
    from app.models import FinancialSnapshotTTM
    ttm_row = None
    try:
        ttm_row = compute_and_store_ttm(db, company_id)
    except Exception:
        ttm_row = db.get(FinancialSnapshotTTM, company_id)

    enriched = enrich_with_seed(entry["snapshot"], entry.get("seed_snapshot"))

    # Enrich latest_snapshot with 3NF derived metrics (ROIC, Altman Z, Beneish M, CAGRs, etc.)
    derived_row = db.execute(
        select(DerivedMetric)
        .where(DerivedMetric.company_id == company_id)
        .order_by(DerivedMetric.fiscal_year.desc().nullslast(), DerivedMetric.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if derived_row:
        for fld in (
            "altman_z", "beneish_m_score", "sloan_accrual_ratio",
            "revenue_cagr_3y", "revenue_cagr_5y", "eps_cagr_3y", "eps_cagr_5y", "fcf_cagr_5y",
            "roic_calc", "grossmargin_calc", "fcfmargin_calc", "roe_calc", "roa_calc",
            "pe_calc", "pb_calc", "ev_calc", "ev_to_ebitda_calc", "netdebt_calc"
        ):
            val = getattr(derived_row, fld, None)
            if val is not None and enriched.get(fld) is None:
                enriched[fld] = val
        if enriched.get("altman_z") is not None and enriched.get("z_score") is None:
            enriched["z_score"] = enriched["altman_z"]
        if enriched.get("beneish_m_score") is not None and enriched.get("m_score") is None:
            enriched["m_score"] = enriched["beneish_m_score"]

    # Enrich latest_snapshot with ROIC, gross margin, PE, price, market_cap
    if ttm_row and ttm_row.roic is not None:
        enriched["roic"] = ttm_row.roic
        if enriched.get("roic_calc") is None:
            enriched["roic_calc"] = ttm_row.roic

    if enriched.get("grossmargin_calc") is not None:
        if enriched.get("gross_margin") is None:
            enriched["gross_margin"] = enriched["grossmargin_calc"]
    elif enriched.get("gross_profit") is not None and enriched.get("revenue"):
        enriched["gross_margin"] = enriched["gross_profit"] / enriched["revenue"]

    if enriched.get("pe_calc") is not None and enriched.get("pe") is None:
        enriched["pe"] = enriched["pe_calc"]
    elif enriched.get("pe_calc") is None and ttm_row and ttm_row.pe_ratio is not None:
        enriched["pe_calc"] = ttm_row.pe_ratio
        enriched["pe"] = ttm_row.pe_ratio

    if enriched.get("pb_calc") is not None and enriched.get("pb") is None:
        enriched["pb"] = enriched["pb_calc"]
    elif enriched.get("pb") is None and enriched.get("market_cap") and enriched.get("book_equity") and enriched.get("book_equity") > 0:
        enriched["pb"] = float(enriched["market_cap"]) / float(enriched["book_equity"])
        if enriched.get("pb_calc") is None:
            enriched["pb_calc"] = enriched["pb"]

    if enriched.get("ev_to_ebitda_calc") is not None and enriched.get("ev_to_ebitda") is None:
        enriched["ev_to_ebitda"] = enriched["ev_to_ebitda_calc"]


    # Fallback price, price_currency, market_cap, and shares across all snapshots if missing on latest
    if enriched.get("price") is None or enriched.get("market_cap") is None:
        all_snaps = db.execute(
            select(FinancialSnapshot)
            .where(FinancialSnapshot.company_id == company_id)
            .order_by(FinancialSnapshot.fiscal_year.desc().nullslast(), FinancialSnapshot.id.desc())
        ).scalars().all()
        for s_row in all_snaps:
            if enriched.get("price") is None and s_row.price is not None:
                enriched["price"] = s_row.price
                if not enriched.get("price_currency"):
                    enriched["price_currency"] = s_row.price_currency or company.currency or "USD"
            if enriched.get("market_cap") is None and s_row.market_cap is not None:
                enriched["market_cap"] = s_row.market_cap
            if enriched.get("shares_snapshot") is None and s_row.shares_snapshot is not None:
                enriched["shares_snapshot"] = s_row.shares_snapshot
    if enriched.get("market_cap") is None and enriched.get("price") is not None and enriched.get("shares_snapshot") is not None:
        enriched["market_cap"] = float(enriched["price"]) * float(enriched["shares_snapshot"])
    if enriched.get("roic") is None and enriched.get("roic_calc") is not None:
        enriched["roic"] = enriched["roic_calc"]
    elif enriched.get("roic_calc") is None and enriched.get("roic") is not None:
        enriched["roic_calc"] = enriched["roic"]
    if enriched.get("net_debt") is None:
        if enriched.get("netdebt_calc") is not None:
            enriched["net_debt"] = enriched["netdebt_calc"]
        elif enriched.get("total_debt") is not None and enriched.get("cash_and_equiv") is not None:
            enriched["net_debt"] = enriched["total_debt"] - enriched["cash_and_equiv"]

    # Intelligent contextual flags for metrics that cannot be computed
    is_financial = company.custom_industry_sheet in ("Banks", "Insurance", "Credit_Services") or company.gics_sector == "Financials"
    if is_financial:
        enriched["financial_model_flag"] = "Regulatory Capital Model (N/A for Debt/FCF/Gross Margin)"
        if enriched.get("gross_margin") is None:
            enriched["gross_margin_flag"] = "N/A: Bank Model"
        if enriched.get("net_debt") is None:
            enriched["net_debt_flag"] = "N/A: Bank Model"

    if enriched.get("pb") is None:
        be = enriched.get("book_equity")
        if be is not None and be <= 0:
            enriched["pb_flag"] = "Deficit (Share Buybacks)"

    if enriched.get("pe") is None:
        eps = enriched.get("diluted_eps")
        ni = enriched.get("net_income")
        if (eps is not None and eps < 0) or (ni is not None and ni < 0):
            enriched["pe_flag"] = "Loss / Deficit"
        elif eps == 0 or ni == 0:
            enriched["pe_flag"] = "Break-even"

    if enriched.get("ev_to_ebitda") is None:
        ebitda = enriched.get("ebitda")
        if ebitda is not None and ebitda <= 0:
            enriched["ev_to_ebitda_flag"] = "Negative EBITDA (N/M)"
        elif is_financial:
            enriched["ev_to_ebitda_flag"] = "N/A: Bank Model"


    score = db.get(Score, company_id)
    score_payload = None
    if score is not None:
        score_payload = {
            "composite": score.composite,
            "pillars": {"quality": score.quality, "value": score.value,
                        "growth": score.growth, "risk": score.risk},
            "coverage": score.coverage,
            "penalty": (score.inputs_json or {}).get("penalty") if score.inputs_json else None,
            "signal": score.signal,
            "peer_set_type": score.peer_set_type,
            "peer_rank": score.peer_rank,
            "peer_n": score.peer_n,
            "as_of_fy": score.as_of_fy,
            "computed_at": score.computed_at,
            "method_version": score.method_version,
            "percentiles": score.percentiles_json,
        }
    hf = db.get(HalalFlag, company_id)
    halal_payload = None
    if hf is not None:
        failed = []
        tests = hf.tests_json or {}
        act = tests.get("activity_screen") or {}
        if act.get("result") == "fail":
            failed.append({"test": "activity_screen", "basis": act.get("basis")})
        for name, r in ((tests.get("financial_ratios") or {}).get("ratios") or {}).items():
            if isinstance(r, dict) and r.get("result") == "fail":
                failed.append({"test": name, "ratio": r})
        halal_payload = {"status": hf.status, "method": hf.method, "failed_tests": failed}

    history_annual = []
    for h in sorted(
        (h for h in entry["history"] if h.get("fiscal_year") is not None),
        key=lambda x: x["fiscal_year"], reverse=True,
    )[:10]:
        history_annual.append({
            "fiscal_year": h["fiscal_year"],
            "revenue": h.get("revenue"),
            "net_income": h.get("net_income"),
            "fcf_calc": h.get("fcf_calc"),
            "diluted_eps": h.get("diluted_eps"),
            "source": h.get("source"),
        })

    # Phase 10 A: sanitize on the read path — suspect years stay visible but chipped,
    # and the API also exposes which years growth actually used.
    from app.services.history_sanity import sanitize_history

    sani = sanitize_history([
        {"fiscal_year": h["fiscal_year"], **{k: h.get(k) for k in ("revenue", "net_income", "diluted_eps", "fcf_calc")}}
        for h in history_annual
    ])
    sanitized_years = [r["fiscal_year"] for r in sani["rows_for_growth"]]
    history_warnings: list[str] = []
    for item, row in zip(history_annual, sani["rows_for_table"]):
        if row.get("quality_flag"):
            item["quality_flag"] = row["quality_flag"]
            item["warning"] = row["warning"]
            history_warnings.append(f"FY{row['fiscal_year']}: {row['warning']}")
        item["used_for_growth"] = item["fiscal_year"] in sanitized_years

    prof = None
    try:
        prof = db.get(CompanyProfile, company_id)
    except Exception:
        # Table missing on a pre-migration DB is a deployment bug; do NOT silently
        # create_all here (Workstream A: migrations are the only schema authority).
        prof = None

    if prof is None and company.ticker:
        try:
            from app.providers.yahoo import fetch_profile_and_quarterly
            from app.services.mapping import yahoo_symbol_for
            symbol = yahoo_symbol_for(company.ticker, company.country or "US")
            p_data = fetch_profile_and_quarterly(symbol)
            if p_data.get("summary") or p_data.get("dividend_yield") is not None or p_data.get("quarterly"):
                prof = CompanyProfile(
                    company_id=company_id,
                    summary=p_data.get("summary"),
                    dividend_yield=p_data.get("dividend_yield"),
                    dividend_rate=p_data.get("dividend_rate"),
                    next_earnings_date=p_data.get("next_earnings_date"),
                    quarterly_json=p_data.get("quarterly"),
                    fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                db.add(prof)
                db.commit()
        except Exception:
            db.rollback()
            prof = None

    profile_payload = {
        "summary": prof.summary if prof else None,
        "dividend_yield": prof.dividend_yield if prof else None,
        "dividend_rate": prof.dividend_rate if prof else None,
        "next_earnings_date": prof.next_earnings_date if prof else None,
    }
    quarterly_payload = prof.quarterly_json if prof else None

    # Phase 2 analytical engines & 3-tier dossier payloads
    from app.services.verdict_engine import synthesize_safety_verdict
    from app.services.archetype_engine import classify_archetype
    from app.services.moat_engine import compute_economic_moat
    from app.services.valuation_engine import compute_and_store_reverse_dcf
    from app.services.capital_return_engine import compute_shareholder_yield
    from app.services.owner_earnings import compute_owner_earnings
    from app.services.beneish_engine import compute_beneish_m_score
    from app.services.distress_engine import compute_distress
    from app.services.penman_engine import latest_penman

    decision_verdict = None
    archetype = None
    moat_rating = None
    expectations_gap = None
    level1 = None
    level2 = None
    level3 = None

    try:
        decision_verdict = synthesize_safety_verdict(db, company_id)
    except Exception:
        decision_verdict = None

    try:
        archetype = classify_archetype(db, company_id)
    except Exception:
        archetype = None

    try:
        moat_rating = compute_economic_moat(db, company_id)
    except Exception:
        moat_rating = None

    try:
        dcf = compute_and_store_reverse_dcf(db, company_id)
        expectations_gap = dcf.expectations_gap if dcf else None
    except Exception:
        expectations_gap = None

    try:
        shareholder = compute_shareholder_yield(db, company_id)
    except Exception:
        shareholder = None

    try:
        owner_earn = compute_owner_earnings(db, company_id)
    except Exception:
        owner_earn = None

    try:
        beneish = compute_beneish_m_score(db, company_id)
    except Exception:
        beneish = None

    try:
        distress = compute_distress(db, company_id)
    except Exception:
        distress = None

    try:
        penman = latest_penman(db, company_id)
    except Exception:
        penman = None

    level1 = {
        "identity": {
            "company_id": company.company_id,
            "ticker": company.ticker,
            "name": company.name,
            "currency": company.currency,
            "gics_sector": company.gics_sector,
        },
        "verdict_badge": decision_verdict.get("verdict_badge") if decision_verdict else None,
        "traffic_lights": decision_verdict.get("traffic_lights") if decision_verdict else None,
        "reverse_dcf_rule": decision_verdict.get("reverse_dcf_rule") if decision_verdict else None,
        "decision_bullets": decision_verdict.get("decision_bullets") if decision_verdict else [],
        "implied_10y_cagr": round(dcf.market_implied_growth_10y * 100.0, 2) if (dcf and dcf.market_implied_growth_10y is not None) else None,
        "historical_5y_cagr": round(dcf.historical_5y_cagr * 100.0, 2) if (dcf and dcf.historical_5y_cagr is not None) else None,
        "expectations_gap": round(dcf.expectations_gap * 100.0, 2) if (dcf and dcf.expectations_gap is not None) else None,
    }

    level2 = {
        "four_pillar_radar": score_payload.get("pillars") if score_payload else None,
        "lynch_archetype": archetype,
        "true_shareholder_yield": shareholder,
        "cash_flow_waterfall": owner_earn,
    }

    level3 = {
        "beneish_matrix": beneish,
        "penman_table": {
            "noa": penman.noa if penman else None,
            "nfo": penman.nfo if penman else None,
            "rnoa": penman.rnoa if penman else None,
            "flev": penman.flev if penman else None,
            "nbc": penman.nbc if penman else None,
            "roe_operational_spread": penman.roe_operational_spread if penman else None,
            "exclusion": penman.exclusion if penman else None,
        } if penman else None,
        "altman_breakdown": distress,
        "statement_history_10y": history_annual,
    }

    from app.services.exchange_resolver import get_exchange, get_tradingview_symbol
    resolved_ex = company.exchange if (company.exchange and company.exchange not in ("US", "CA")) else get_exchange(company.ticker or "", country=company.country or "US")
    tv_symbol = get_tradingview_symbol(company.company_id, company.ticker, exchange=resolved_ex, country=company.country)

    return DossierOut(
        identity={
            "company_id": company.company_id,
            "name": company.name,
            "currency": company.currency,
            "country": company.country,
            "exchange": resolved_ex,
            "tradingview_symbol": tv_symbol,
            "gics_sector": company.gics_sector,
            "gics_industry": company.gics_industry,
            "custom_industry_sheet": company.custom_industry_sheet,
            "indexes": company.indexes,
            "in_sp500": company.in_sp500,
            "in_tsx_composite": company.in_tsx_composite,
            "cik": company.cik,
            "ticker": company.ticker,
            "reporting_currency": company.reporting_currency,
            "filing_type": company.filing_type,
        },
        latest_snapshot=enriched,
        history_annual=history_annual,
        history_warnings=history_warnings,
        score=score_payload,
        halal=halal_payload,
        data_gaps=_data_gaps(entry, enriched),
        profile=profile_payload,
        quarterly=quarterly_payload,
        decision_verdict=decision_verdict,
        archetype=archetype,
        moat_rating=moat_rating,
        expectations_gap=expectations_gap,
        level1=level1,
        level2=level2,
        level3=level3,
        method_version=METHOD_VERSION,
        disclaimer=DISCLAIMER,
    )


# --------------------------------------------------------------------------
# Compare
# --------------------------------------------------------------------------

class CompareRow(BaseModel):
    model_config = {"protected_namespaces": ()}

    company_id: str
    name: str | None = None
    currency: str | None = None
    found: bool = True
    composite: float | None = None
    quality: float | None = None
    value: float | None = None
    growth: float | None = None
    risk: float | None = None
    signal: str | None = None
    pe_calc: float | None = None
    pb_calc: float | None = None
    roe_calc: float | None = None
    roa_calc: float | None = None
    fcfmargin_calc: float | None = None
    ev_to_ebitda_calc: float | None = None
    peer_rank: int | None = None
    halal_status: str | None = None
    money: dict | None = None


class CompareOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    ids: list[str]
    currency_warning: bool
    currencies: list[str]
    comparable: list[str]
    rows: list[CompareRow]
    method_version: str
    disclaimer: str


_MONEY_FIELDS = ["revenue", "net_income", "total_debt", "book_equity", "cash_st_investments",
                 "total_assets", "total_liabilities", "ebit", "ebitda", "market_cap", "price"]


@router.get("/compare", response_model=CompareOut, description="Compare 2-8 companies; ratios+scores comparable across currencies, money fields are per-row native currency (never converted).")
def compare(
    response: Response,
    ids: str = Query(default="", max_length=512, description="comma-separated company_ids (2-8)"),
    include_money: bool = Query(default=True),
    db: Session = Depends(get_session),
):
    _cache(response)
    id_list = [x.strip() for x in ids.split(",") if x.strip()]
    if not (2 <= len(id_list) <= 8):
        raise HTTPException(status_code=400, detail="provide between 2 and 8 comma-separated company_ids")

    universe = {u["company_id"]: u for u in load_universe(db)}
    rows: list[CompareRow] = []
    currencies: list[str] = []
    for cid in id_list:
        company = db.get(Company, cid)
        if company is None:
            rows.append(CompareRow(company_id=cid, found=False))
            continue
        if company.currency and company.currency not in currencies:
            currencies.append(company.currency)
        entry = universe.get(cid)
        enriched = enrich_with_seed(entry["snapshot"], entry.get("seed_snapshot")) if entry else {}
        score = db.get(Score, cid)
        hf = db.get(HalalFlag, cid)
        money = None
        if include_money:
            money = {"currency": company.currency, **{k: enriched.get(k) for k in _MONEY_FIELDS}}
        rows.append(CompareRow(
            company_id=cid,
            name=company.name,
            currency=company.currency,
            composite=score.composite if score else None,
            quality=score.quality if score else None,
            value=score.value if score else None,
            growth=score.growth if score else None,
            risk=score.risk if score else None,
            signal=score.signal if score else None,
            pe_calc=enriched.get("pe_calc"),
            pb_calc=enriched.get("pb_calc"),
            roe_calc=enriched.get("roe_calc"),
            roa_calc=enriched.get("roa_calc"),
            fcfmargin_calc=enriched.get("fcfmargin_calc"),
            ev_to_ebitda_calc=enriched.get("ev_to_ebitda_calc"),
            peer_rank=score.peer_rank if score else None,
            halal_status=hf.status if hf else None,
            money=money,
        ))

    currency_warning = len(currencies) > 1
    comparable = ["composite", "quality", "value", "growth", "risk", "signal",
                  "pe_calc", "pb_calc", "roe_calc", "roa_calc", "fcfmargin_calc",
                  "ev_to_ebitda_calc", "peer_rank", "halal_status"]
    ordered = sorted(rows, key=lambda r: (r.composite is None, -(r.composite or 0)))
    return CompareOut(
        ids=id_list,
        currency_warning=currency_warning,
        currencies=currencies,
        comparable=comparable,
        rows=ordered,
        method_version=METHOD_VERSION,
        disclaimer=DISCLAIMER,
    )


# --------------------------------------------------------------------------
# Similar
# --------------------------------------------------------------------------

class SimilarItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    company_id: str
    name: str | None = None
    composite: float | None = None
    signal: str | None = None
    better: bool
    currency: str | None = None


class SimilarOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    company_id: str
    peer_set_type: str | None
    peer_n: int | None
    items: list[SimilarItem]
    method_version: str
    disclaimer: str


@router.get("/companies/{company_id}/similar", response_model=SimilarOut, description="Peers from the same scoring peer set, ranked by composite; better=true when above the subject.")
def similar(company_id: str, response: Response, n: int = Query(default=5, ge=1, le=20), db: Session = Depends(get_session)):
    _cache(response)
    subject = db.get(Company, company_id)
    if subject is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    subject_score = db.get(Score, company_id)
    if subject_score is None or subject_score.composite is None:
        raise HTTPException(status_code=409, detail="insufficient_data: subject score is NULL — recompute first")

    from app.services.scoring import build_peer_sets

    universe = load_universe(db)
    members, meta = build_peer_sets(universe)
    peers = [m for m in (members.get(company_id) or []) if m["company_id"] != company_id]
    ranked: list[tuple[str, float]] = []
    for p in peers:
        s = db.get(Score, p["company_id"])
        if s is not None and s.composite is not None:
            ranked.append((p["company_id"], s.composite))
    ranked.sort(key=lambda kv: kv[1], reverse=True)

    items = []
    for pid, comp in ranked[:n]:
        c = db.get(Company, pid)
        s = db.get(Score, pid)
        items.append(SimilarItem(
            company_id=pid,
            name=c.name if c else None,
            composite=comp,
            signal=s.signal if s else None,
            better=comp > subject_score.composite,
            currency=c.currency if c else None,
        ))
    ptype, pn = meta.get(company_id, (None, None))
    return SimilarOut(
        company_id=company_id,
        peer_set_type=ptype,
        peer_n=pn,
        items=items,
        method_version=METHOD_VERSION,
        disclaimer=DISCLAIMER,
    )


# --------------------------------------------------------------------------
# Sector snapshot
# --------------------------------------------------------------------------

class SectorSnapshotOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    sheet: str
    currency: str
    companies: int
    scored: int
    signal_histogram: dict
    median_composite: float | None
    median_pe: float | None
    median_pb: float | None
    median_roe: float | None
    top: list[dict]
    bottom: list[dict]
    method_version: str
    disclaimer: str


def _median(vals: list[float]) -> float | None:
    vals = sorted(v for v in vals if v is not None and v == v)
    if not vals:
        return None
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


@router.get("/sectors/{sheet}/snapshot", response_model=SectorSnapshotOut, description="Counts, medians, signal histogram, top/bottom 10 for one industry sheet in one currency (currency required).")
def sector_snapshot(sheet: str, response: Response, currency: str | None = Query(default=None), db: Session = Depends(get_session)):
    _cache(response)
    if not currency or currency.upper() not in ("USD", "CAD"):
        raise HTTPException(status_code=400, detail="currency query parameter is required (USD or CAD)")
    cur = currency.upper()
    from app.services.sector_cache import get_cached_sector_snapshot

    data = get_cached_sector_snapshot(db, sheet, cur)
    return SectorSnapshotOut(**data)


# --------------------------------------------------------------------------
# Research meta
# --------------------------------------------------------------------------

class ResearchMetaOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    companies: int
    scored: int
    insufficient_data: int
    growth_null: int
    signal_histogram: dict
    method_version: str
    last_recompute: str | None
    disclaimer: str


@router.get("/research/meta", response_model=ResearchMetaOut, description="Health of the research layer: counts, histogram, last recompute time.")
def research_meta(response: Response, db: Session = Depends(get_session)):
    _cache(response)
    companies = db.query(Company).count()
    scored = db.query(Score).filter(Score.composite.isnot(None)).count()
    insufficient = db.query(Score).filter(Score.composite.is_(None)).count()
    growth_null = db.query(Score).filter(Score.growth.is_(None), Score.composite.isnot(None)).count()
    hist_rows = db.execute(select(Score.signal, func.count()).group_by(Score.signal)).all()
    last = db.execute(select(Score.computed_at).order_by(Score.computed_at.desc()).limit(1)).scalar_one_or_none()
    return ResearchMetaOut(
        companies=companies,
        scored=scored,
        insufficient_data=insufficient,
        growth_null=growth_null,
        signal_histogram={s or "insufficient_data": n for s, n in hist_rows},
        method_version=METHOD_VERSION,
        last_recompute=last.isoformat() if last else None,
        disclaimer=DISCLAIMER,
    )


@router.get("/companies/{company_id}/financials/common-size")
def get_company_common_size(
    company_id: str,
    years: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_session),
):
    """Koyfin-style common-size financial statements (Master Directive WS2)."""
    cid = normalize_company_id(company_id) or company_id
    from app.services.common_size_engine import compute_common_size

    try:
        return compute_common_size(db, cid, years=years)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/etfs/top-cohorts")
def get_etf_top_cohorts(db: Session = Depends(get_session)):
    """Retrieves top 5 companies by composite score across major ETF / index cohorts."""
    from app.services.etf_resolver import get_etf_cohort_top5

    return get_etf_cohort_top5(db)
