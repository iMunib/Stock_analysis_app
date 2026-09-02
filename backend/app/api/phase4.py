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
from app.models import Company, CompanyProfile, HalalFlag, Score
from app.services.scoring import DISCLAIMER, METHOD_VERSION
from app.services.scoring_service import enrich_with_seed, load_universe

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
    entry = next((u for u in load_universe(db) if u["company_id"] == company_id), None)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    enriched = enrich_with_seed(entry["snapshot"], entry.get("seed_snapshot"))

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
        try:
            from app.db import Base, engine
            Base.metadata.create_all(bind=engine, tables=[CompanyProfile.__table__])
            db.rollback()
            prof = db.get(CompanyProfile, company_id)
        except Exception:
            prof = None

    if prof is None and company.ticker:
        try:
            from app.providers.yahoo import fetch_profile_and_quarterly
            symbol = company.ticker + (".TO" if company.country == "CA" else "")
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

    return DossierOut(
        identity={
            "company_id": company.company_id,
            "name": company.name,
            "currency": company.currency,
            "country": company.country,
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

    stmt = (
        select(Company, Score)
        .outerjoin(Score, Score.company_id == Company.company_id)
        .where(
            (func.lower(Company.custom_industry_sheet) == sheet.lower())
            | (func.lower(Company.gics_sector) == sheet.removeprefix("GICS_").lower())
        )
        .where(Company.currency == cur)
    )
    rows = list(db.execute(stmt).all())

    # one row per company_id (Extra/GICS placements never enter `companies`)
    seen: set[str] = set()
    uniq: list[tuple[Company, Score | None]] = []
    for c, s in rows:
        if c.company_id not in seen:
            seen.add(c.company_id)
            uniq.append((c, s))

    hist: dict[str, int] = {}
    composites: list[float] = []
    for _c, s in uniq:
        if s is not None and s.composite is not None:
            composites.append(s.composite)
            hist[s.signal or "unknown"] = hist.get(s.signal or "unknown", 0) + 1
        else:
            hist["score_missing"] = hist.get("score_missing", 0) + 1

    scored = [(c, s) for c, s in uniq if s is not None and s.composite is not None]
    scored.sort(key=lambda cs: cs[1].composite, reverse=True)

    def _entry(c, s):
        return {"company_id": c.company_id, "name": c.name, "composite": s.composite, "signal": s.signal}

    universe = {u["company_id"]: u for u in load_universe(db)}
    med_rows = []
    for c, _s in uniq:
        entry = universe.get(c.company_id)
        if entry:
            med_rows.append(enrich_with_seed(entry["snapshot"], entry.get("seed_snapshot")))

    return SectorSnapshotOut(
        sheet=sheet,
        currency=cur,
        companies=len(uniq),
        scored=len(scored),
        signal_histogram=hist,
        median_composite=_median(composites),
        median_pe=_median([r.get("pe_calc") for r in med_rows if r.get("pe_calc") is not None]),
        median_pb=_median([r.get("pb_calc") for r in med_rows if r.get("pb_calc") is not None]),
        median_roe=_median([r.get("roe_calc") for r in med_rows if r.get("roe_calc") is not None]),
        top=[_entry(c, s) for c, s in scored[:10]],
        bottom=[_entry(c, s) for c, s in scored[-10:][::-1]],
        method_version=METHOD_VERSION,
        disclaimer=DISCLAIMER,
    )


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
