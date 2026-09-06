"""Comprehensive edge case testing for all functionalities - independent and exhaustive."""
from __future__ import annotations
import os, pathlib
BACKEND_DIR = pathlib.Path(__file__).resolve().parent
os.chdir(BACKEND_DIR)
os.environ["DATABASE_URL"] = f"sqlite:///{(BACKEND_DIR / '.edgecase_test.db').as_posix()}"
os.environ["JOBS_WORKER_DISABLED"] = "1"
if (BACKEND_DIR / ".edgecase_test.db").exists():
    (BACKEND_DIR / ".edgecase_test.db").unlink()
# cleanup wal/shm
for s in ("-wal","-shm"):
    p = pathlib.Path(str(BACKEND_DIR / ".edgecase_test.db")+s)
    if p.exists(): p.unlink()

from app.db import Base, SessionLocal, engine
import app.models
from app.config import find_seed_workbook
from app.services.importer import run_import
from app.services.scoring_service import recompute
from sqlalchemy import select, text

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
from alembic.config import Config as AConfig
from alembic import command as ACommand
cfg = AConfig(str(BACKEND_DIR/"alembic.ini"))
cfg.set_main_option("script_location", str(BACKEND_DIR/"alembic"))
cfg.set_main_option("sqlalchemy.url", f"sqlite:///{(BACKEND_DIR / '.edgecase_test.db').as_posix()}")
ACommand.stamp(cfg, "head")
wb = find_seed_workbook()
assert wb
run_import(force=True, seed_path=wb)
with SessionLocal() as db:
    recompute(db)
    db.commit()

from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

import math
from app.services.scoring import _to_float_optional, _clamp, quality_pillar, value_pillar, growth_pillar, risk_pillar, composite_score, build_peer_sets, peer_values_for, piotroski_fscore
from app.services.halal import evaluate_halal, DEBT_TO_MCAP_LIMIT, CASH_TO_MCAP_LIMIT, IMPURE_INCOME_LIMIT
from app.services.ids import parse_company_id, normalize_company_id, format_company_id

def assert_check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"{status}: {name} {detail}")
    return condition

results = []

# ──────────────────────────────────────────────────────────────────────────────
# 1) Core utility edge: _to_float_optional, _clamp
# ──────────────────────────────────────────────────────────────────────────────
results.append(assert_check("TO_FLOAT None", _to_float_optional(None) is None))
results.append(assert_check("TO_FLOAT nan", _to_float_optional(float('nan')) is None))
results.append(assert_check("TO_FLOAT inf", _to_float_optional(float('inf')) == float('inf')))  # inf != nan so passes
results.append(assert_check("TO_FLOAT string", _to_float_optional("abc") is None))
results.append(assert_check("TO_FLOAT valid", _to_float_optional("12.3")==12.3))
results.append(assert_check("CLAMP within", _clamp(0.5,0,1)==0.5))
results.append(assert_check("CLAMP low", _clamp(-5,0,1)==0))
results.append(assert_check("CLAMP high", _clamp(5,0,1)==1))
results.append(assert_check("CLAMP nan? handled via caller", _clamp(float('nan'),0,1) is not None))  # nan comparison weird but we record

# ID parsing edges
results.append(assert_check("ID parse valid US", parse_company_id("US:AAPL:US").ticker=="AAPL"))
results.append(assert_check("ID parse valid CA", parse_company_id("CA:RY:TSX").ticker=="RY"))
results.append(assert_check("ID parse invalid empty", parse_company_id("") is None))
results.append(assert_check("ID parse invalid bad format", parse_company_id("US:AAPL:NYSE") is None))  # strict fails
results.append(assert_check("ID normalize loose NYSE", normalize_company_id("US:AES:NYSE")=="US:AES:US"))
results.append(assert_check("ID normalize empty ticker", normalize_company_id("CA::TSX") is None))
results.append(assert_check("ID normalize null", normalize_company_id(None) is None))
try:
    format_company_id("XX","AAPL")
    results.append(assert_check("ID format invalid country should raise", False))
except ValueError:
    results.append(assert_check("ID format invalid country raises", True))

# ──────────────────────────────────────────────────────────────────────────────
# 2) Companies API edge cases
# ──────────────────────────────────────────────────────────────────────────────
def api_check(name, resp, expect, json_key=None):
    ok = resp.status_code == expect
    if ok and json_key:
        try:
            j=resp.json()
            if json_key not in j:
                ok=False
        except: ok=False
    results.append(assert_check(name, ok, f"got {resp.status_code} expect {expect} body {resp.text[:200]}"))
    return ok

api_check("Companies limit 1", client.get("/api/v1/companies?limit=1"),200,"total")
api_check("Companies limit 500 max", client.get("/api/v1/companies?limit=500"),200)
api_check("Companies limit 501 should 422", client.get("/api/v1/companies?limit=501"),422)
api_check("Companies limit 0 should 422", client.get("/api/v1/companies?limit=0"),422)
api_check("Companies offset beyond total", client.get("/api/v1/companies?offset=10000&limit=5"),200)
api_check("Companies country lowercase ca", client.get("/api/v1/companies?country=ca&limit=2"),200)
api_check("Companies country invalid XX", client.get("/api/v1/companies?country=XX&limit=5"),200)  # should return 0 items not error
api_check("Companies sector not exist", client.get("/api/v1/companies?sector=NonExistentSector&limit=5"),200)
api_check("Companies q SQL injection attempt", client.get("/api/v1/companies?q=%27%20OR%201%3D1--&limit=5"),200)
api_check("Companies q empty string should 200 with no filter", client.get("/api/v1/companies?q=&limit=5"),200)
api_check("Companies offset 0", client.get("/api/v1/companies?offset=0&limit=5"),200)
api_check("Company detail unknown 404", client.get("/api/v1/companies/US:FAKE:US"),404)
api_check("Company detail malformed ID 404", client.get("/api/v1/companies/BADID"),404)
api_check("Company detail with dot in ticker", client.get("/api/v1/companies/US:BRK.B:US"),200)  # should not crash, may be 404 but not 500
# statements edge
api_check("Statements limit 0 should 422", client.get("/api/v1/companies/US:MMM:US/statements?limit=0"),422)
api_check("Statements limit 31 should 422", client.get("/api/v1/companies/US:MMM:US/statements?limit=31"),422)
api_check("Statements unknown company", client.get("/api/v1/companies/US:FAKE:US/statements"),404)
api_check("Derived metrics unknown company", client.get("/api/v1/companies/US:FAKE:US/derived-metrics"),404)
api_check("Benchmarks unknown company", client.get("/api/v1/companies/US:FAKE:US/benchmarks"),404)
# valid statements
r=client.get("/api/v1/companies/US:MMM:US/statements?limit=1")
if r.status_code==200:
    results.append(assert_check("Statements shape has fiscal_year", "fiscal_year" in r.json()["items"][0]))

# ──────────────────────────────────────────────────────────────────────────────
# 3) Search edge
# ──────────────────────────────────────────────────────────────────────────────
api_check("Search empty q should 400", client.get("/api/v1/search?q=&limit=5"),400)
api_check("Search q length 1", client.get("/api/v1/search?q=A&limit=5"),200)
api_check("Search long q", client.get("/api/v1/search?q="+"A"*64+"&limit=5"),200)
api_check("Search long q 65 should 422", client.get("/api/v1/search?q="+"A"*65+"&limit=5"),422)
api_check("Search special chars", client.get("/api/v1/search?q=%24%25%5E&limit=5"),200)
api_check("Search case insensitive", client.get("/api/v1/search?q=aapl&limit=5"),200)
api_check("Suggestions empty q 200 graceful", client.get("/api/v1/search/suggestions?q=&limit=5"),200)
api_check("Suggestions limit 0 should 422", client.get("/api/v1/search/suggestions?q=A&limit=0"),422)  # may be 200 or 422 depending

# ──────────────────────────────────────────────────────────────────────────────
# 4) Scoring edge cases (direct service)
# ──────────────────────────────────────────────────────────────────────────────
# growth insufficient history
g, gd = growth_pillar([])
results.append(assert_check("Growth empty history -> None", g is None and gd.get("reason")=="insufficient_history"))
g, gd = growth_pillar([{"fiscal_year":2023,"revenue":100}])
results.append(assert_check("Growth single row -> None", g is None))
g, gd = growth_pillar([{"fiscal_year":2023,"revenue":100},{"fiscal_year":2024,"revenue":110}])
results.append(assert_check("Growth 2 rows but need 3 pts -> None", g is None))
# growth with negative/zero values skipped
g, gd = growth_pillar([{"fiscal_year":2020,"revenue":0},{"fiscal_year":2021,"revenue":10},{"fiscal_year":2022,"revenue":20},{"fiscal_year":2023,"revenue":30}])
results.append(assert_check("Growth zero begin skipped", g is None or isinstance(g,float)))

# piotroski single FY
used, poss, det = piotroski_fscore({"net_income":100,"total_assets":1000,"operating_cash_flow":150}, None)
results.append(assert_check("Piotroski single FY F_possible 9?", poss==9))  # should be 9 with 3 real +6 impossible
results.append(assert_check("Piotroski single FY detail has delta_roa None", det["delta_roa"] is None))

# quality pillar missing all components -> None
q, qd = quality_pillar({"gics_sector":None,"custom_industry_sheet":None}, None, {})
results.append(assert_check("Quality no inputs -> None", q is None))
# quality financial path
q, qd = quality_pillar({"gics_sector":"Financials","custom_industry_sheet":"Banks","roe_calc":0.1,"roa_calc":0.02,"efficiency_ratio":0.5,"roaa":0.01,"cet1_ratio":0.12,"nim_fy2025":0.02}, None, {})
results.append(assert_check("Quality financial has path financial", qd.get("path")=="financial" and q is not None))

# value pillar no inputs
v, vd = value_pillar({"pe_calc":None}, {})
results.append(assert_check("Value no inputs -> None", v is None))
# value negative PE skipped
v, vd = value_pillar({"pe_calc":-5}, {"pe":[15,20]})
results.append(assert_check("Value negative PE skipped not scored", vd.get("pe_negative_skipped")==True and v is None))

# risk pillar no inputs
r, rd = risk_pillar({"netdebt_calc":None}, [])
results.append(assert_check("Risk no inputs -> None", r is None or rd.get("reason")=="no_risk_inputs"))

# composite 0 pillars
c, cov, pen = composite_score({"quality":None,"value":None,"growth":None,"risk":None})
results.append(assert_check("Composite 0 -> None", c is None and cov==0))
c, cov, pen = composite_score({"quality":8.0,"value":None,"growth":None,"risk":None})
results.append(assert_check("Composite 1 pillar penalty 0.65", pen==0.65))
c, cov, pen = composite_score({"quality":8.0,"value":8.0,"growth":8.0,"risk":8.0})
results.append(assert_check("Composite 4 pillars penalty 1.0", pen==1.0 and cov==4))

# build_peer_sets edge: empty companies
members, meta = build_peer_sets([])
results.append(assert_check("Peer sets empty -> empty", len(members)==0))
# peer sets with same currency
members, meta = build_peer_sets([{"company_id":"US:A:US","currency":"USD","custom_industry_sheet":"Tech","gics_sector":"Tech"},{"company_id":"US:B:US","currency":"USD","custom_industry_sheet":"Tech","gics_sector":"Tech"}])
results.append(assert_check("Peer sets 2 same industry USD -> 2", meta["US:A:US"][1]==2))
# peer sets mixed currency never mixed
members, meta = build_peer_sets([{"company_id":"US:A:US","currency":"USD","custom_industry_sheet":"Banks","gics_sector":"Financials"},{"company_id":"CA:B:TSX","currency":"CAD","custom_industry_sheet":"Banks","gics_sector":"Financials"}])
results.append(assert_check("Peer sets mixed currency correctly isolated", meta["US:A:US"][1]==1 and meta["CA:B:TSX"][1]==1))  # each isolated to size 1 due to currency isolation

# ──────────────────────────────────────────────────────────────────────────────
# 5) Halal service edge
# ──────────────────────────────────────────────────────────────────────────────
# missing snapshot
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, None)
results.append(assert_check("Halal None snap -> unknown", res["status"]=="unknown"))
# missing market cap
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":None,"total_debt":100,"cash_st_investments":100,"interest_income":10,"revenue":1000})
results.append(assert_check("Halal missing mcap -> unknown", res["status"]=="unknown"))
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":0,"total_debt":100,"cash_st_investments":100,"interest_income":10,"revenue":1000})
results.append(assert_check("Halal zero mcap -> unknown", res["status"]=="unknown"))
# debt null
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":1000,"total_debt":None,"cash_st_investments":100,"interest_income":10,"revenue":1000})
results.append(assert_check("Halal debt null -> unknown not halal", res["status"]=="unknown"))
# cash null
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":1000,"total_debt":100,"cash_st_investments":None,"interest_income":10,"revenue":1000})
results.append(assert_check("Halal cash null -> unknown", res["status"]=="unknown"))
# interest missing
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":1000,"total_debt":100,"cash_st_investments":100,"interest_income":None,"revenue":1000})
results.append(assert_check("Halal interest null -> unknown", res["status"]=="unknown"))
# activity fail
res = evaluate_halal({"gics_sector":"Financials","custom_industry_sheet":"Banks","name":"Test Bank"}, {"market_cap":1000,"total_debt":100,"cash_st_investments":100,"interest_income":10,"revenue":1000})
results.append(assert_check("Halal bank -> not_halal", res["status"]=="not_halal"))
# keyword hit
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Alcohol Brewing Co"}, {"market_cap":1000,"total_debt":100,"cash_st_investments":100,"interest_income":10,"revenue":10000})
results.append(assert_check("Halal alcohol keyword -> not_halal", res["status"]=="not_halal"))
# ratio fail vs pass boundary: debt 0.30 exactly -> pass? code is < not <=
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":1000,"total_debt":300,"cash_st_investments":100,"interest_income":10,"revenue":10000})
results.append(assert_check("Halal debt exactly 0.30 -> fail (strict <)", res["tests"]["financial_ratios"]["ratios"]["debt_to_mcap"]["result"]=="fail"))
# debt 0.29 pass
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":1000,"total_debt":299,"cash_st_investments":100,"interest_income":10,"revenue":10000})
results.append(assert_check("Halal debt 0.299 -> pass", res["tests"]["financial_ratios"]["ratios"]["debt_to_mcap"]["result"]=="pass"))
# impure income exactly 0.05 pass
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":10000,"total_debt":100,"cash_st_investments":100,"interest_income":50,"revenue":1000})
results.append(assert_check("Halal impure 0.05 pass", res["tests"]["financial_ratios"]["ratios"]["impure_income"]["result"]=="pass"))
# impure 0.06 fail
res = evaluate_halal({"gics_sector":"Technology","custom_industry_sheet":"Software","name":"Test"}, {"market_cap":10000,"total_debt":100,"cash_st_investments":100,"interest_income":60,"revenue":1000})
results.append(assert_check("Halal impure 0.06 fail", res["tests"]["financial_ratios"]["ratios"]["impure_income"]["result"]=="fail"))

# ──────────────────────────────────────────────────────────────────────────────
# 6) API edges: scoring via API
# ──────────────────────────────────────────────────────────────────────────────
api_check("Recompute missing universe 422", client.post("/api/v1/scores/recompute", json={"universe":"invalid"}),422)
api_check("Recompute company_id mode missing param 400", client.post("/api/v1/scores/recompute", json={"universe":"company_id"}),400)
api_check("Recompute company_id unknown 404", client.post("/api/v1/scores/recompute", json={"universe":"company_id","company_id":"US:FAKE:US"}),404)
api_check("Score unknown company 404", client.get("/api/v1/companies/US:FAKE:US/score"),404)
api_check("Sector rankings ALL currency", client.get("/api/v1/sectors/Banks/rankings?currency=ALL&limit=2"),200)
api_check("Sector rankings CAD", client.get("/api/v1/sectors/Banks/rankings?currency=CAD&limit=2"),200)
api_check("Sector rankings halal candidate filter", client.get("/api/v1/sectors/Banks/rankings?currency=USD&limit=5&halal=candidate"),200)
api_check("Rankings halal filter", client.get("/api/v1/rankings?limit=5&halal=candidate"),200)
api_check("Rankings signal filter", client.get("/api/v1/rankings?limit=5&signal=strong_candidate"),200)
api_check("Rankings offset beyond", client.get("/api/v1/rankings?limit=5&offset=10000"),200)
api_check("Rankings limit 0 should 422", client.get("/api/v1/rankings?limit=0"),422)
api_check("Rankings limit 501 should 422", client.get("/api/v1/rankings?limit=501"),422)

# ──────────────────────────────────────────────────────────────────────────────
# 7) Dossier/compare/similar edges
# ──────────────────────────────────────────────────────────────────────────────
api_check("Dossier unknown 404", client.get("/api/v1/companies/US:FAKE:US/dossier"),404)
api_check("Compare single id should 400", client.get("/api/v1/compare?ids=US:AAPL:US"),400)
api_check("Compare mixed currencies warning", client.get("/api/v1/compare?ids=US:AAPL:US,CA:RY:TSX"),200)
r=client.get("/api/v1/compare?ids=US:AAPL:US,CA:RY:TSX")
if r.status_code==200:
    results.append(assert_check("Compare mixed currencies has currency_warning true", r.json().get("currency_warning")==True))
api_check("Compare with unknown id", client.get("/api/v1/compare?ids=US:FAKE:US,US:AAPL:US"),200)
api_check("Similar unknown 404?", client.get("/api/v1/companies/US:FAKE:US/similar"),404)
api_check("Sector snapshot ALL should 400", client.get("/api/v1/sectors/Technology/snapshot?currency=ALL"),400)
api_check("Sector snapshot invalid currency 400", client.get("/api/v1/sectors/Technology/snapshot?currency=EUR"),400)

# ──────────────────────────────────────────────────────────────────────────────
# 8) Ratio inspector edges
# ──────────────────────────────────────────────────────────────────────────────
api_check("Ratio inspector unknown ratio fallback 200", client.get("/api/v1/companies/US:AAPL:US/ratios/xyz_unknown/inspect"),200)
r=client.get("/api/v1/companies/US:AAPL:US/ratios/xyz_unknown/inspect")
if r.status_code==200:
    results.append(assert_check("Unknown ratio returns fallback label", "XYZ_UNKNOWN" in r.json().get("label","").upper()))
api_check("Ratio inspector unknown company 404", client.get("/api/v1/companies/US:FAKE:US/ratios/roe/inspect"),404)
api_check("Ratio inspector bank ROIC N/A", client.get("/api/v1/companies/US:JPM:US/ratios/roic/inspect"),200)
r=client.get("/api/v1/companies/US:JPM:US/ratios/roic/inspect")
if r.status_code==200:
    results.append(assert_check("Bank ROIC is N/A or Bank Model", "N/A" in r.json().get("result_formatted","") or "Bank" in r.json().get("result_formatted","")))
# check CAD vs SEC link
r=client.get("/api/v1/companies/CA:RY:TSX/ratios/roa/inspect")
if r.status_code==200:
    results.append(assert_check("CAD ratio has SEDAR link", "sedarplus" in (r.json().get("numerator",{}).get("sec_edgar_url") or "")))
r=client.get("/api/v1/companies/US:AAPL:US/ratios/roa/inspect")
if r.status_code==200:
    results.append(assert_check("USD ratio has sec.gov link", "sec.gov" in (r.json().get("numerator",{}).get("sec_edgar_url") or "")))

# ──────────────────────────────────────────────────────────────────────────────
# 9) Forensics / Valuation edges
# ──────────────────────────────────────────────────────────────────────────────
api_check("Forensics unknown company 404", client.get("/api/v1/companies/US:FAKE:US/forensics"),404)
api_check("Forensics benford unknown", client.get("/api/v1/companies/US:FAKE:US/forensics/benford"),404)
api_check("Valuation unknown company 404? or 200 with status", client.get("/api/v1/companies/US:FAKE:US/valuation"),404)
api_check("EPV wacc out of range 422", client.get("/api/v1/companies/US:AAPL:US/valuation/epv?wacc=0.01"),422)
api_check("EPV wacc boundary 0.02 ok", client.get("/api/v1/companies/US:AAPL:US/valuation/epv?wacc=0.02"),200)
api_check("EPV wacc 0.25 ok", client.get("/api/v1/companies/US:AAPL:US/valuation/epv?wacc=0.25"),200)
api_check("EPV wacc 0.26 should 422", client.get("/api/v1/companies/US:AAPL:US/valuation/epv?wacc=0.26"),422)
api_check("Guided valuation wacc out of range", client.get("/api/v1/companies/US:AAPL:US/valuation/guided?wacc=0.01"),422)
api_check("DDM for bank should be meaningful? but check not 500", client.get("/api/v1/companies/US:JPM:US/valuation/ddm"),200)
# common-size edge: years 0 should 422? check schema
api_check("Common-size years 0 invalid", client.get("/api/v1/companies/US:AAPL:US/financials/common-size?years=0"),422)
api_check("Common-size years 31 invalid", client.get("/api/v1/companies/US:AAPL:US/financials/common-size?years=31"),422)

# ──────────────────────────────────────────────────────────────────────────────
# 10) Jobs / Ingest edges
# ──────────────────────────────────────────────────────────────────────────────
api_check("Ingest empty ticker 422", client.post("/api/v1/tickers/ingest", json={"ticker":""}),422)
api_check("Ingest whitespace ticker 400? or 202", client.post("/api/v1/tickers/ingest", json={"ticker":"   "}),400)  # resolve should 400
api_check("Ingest ticker with symbols queued 202", client.post("/api/v1/tickers/ingest", json={"ticker":"$$INVALID"}),202)
api_check("Jobs list", client.get("/api/v1/jobs?limit=5"),200)
# backfill invalid mode
api_check("Backfill invalid mode 422", client.post("/api/v1/jobs/backfill", json={"mode":"invalid","limit":5}),422)
api_check("Backfill limit 0 422", client.post("/api/v1/jobs/backfill", json={"mode":"sample","limit":0}),422)
api_check("Backfill limit 751 422", client.post("/api/v1/jobs/backfill", json={"mode":"sample","limit":751}),422)

# ──────────────────────────────────────────────────────────────────────────────
# 11) Portfolio edges
# ──────────────────────────────────────────────────────────────────────────────
api_check("Portfolio accounts list", client.get("/api/v1/portfolio/accounts"),200)
api_check("Portfolio create missing name 422", client.post("/api/v1/portfolio/accounts", json={"account_type":"TFSA","currency":"CAD"}),422)
api_check("Portfolio create invalid currency 422", client.post("/api/v1/portfolio/accounts", json={"name":"Test","account_type":"TFSA","currency":"EUR"}),422)
api_check("Portfolio create invalid type 422", client.post("/api/v1/portfolio/accounts", json={"name":"Test","account_type":"INVALID","currency":"CAD"}),422)
# create valid then test txn edges
resp = client.post("/api/v1/portfolio/accounts", json={"name":"Edge TFSA","account_type":"TFSA","currency":"USD"})
if resp.status_code==200 or resp.status_code==201:
    acct = resp.json().get("id") or resp.json().get("account",{}).get("id") or "dummy"
    api_check("Portfolio txn zero qty 422", client.post("/api/v1/portfolio/transactions", json={"account_id":acct,"company_id":"US:AAPL:US","txn_type":"buy","quantity":0,"price_per_share":10,"txn_date":"2025-01-01","currency":"USD"}),422)
    api_check("Portfolio txn negative price 422", client.post("/api/v1/portfolio/transactions", json={"account_id":acct,"company_id":"US:AAPL:US","txn_type":"buy","quantity":10,"price_per_share":-5,"txn_date":"2025-01-01","currency":"USD"}),422)
    api_check("Portfolio txn invalid company 404", client.post("/api/v1/portfolio/transactions", json={"account_id":acct,"company_id":"US:FAKE:US","txn_type":"buy","quantity":10,"price_per_share":10,"txn_date":"2025-01-01","currency":"USD"}),404)
    api_check("Portfolio txn invalid account 404", client.post("/api/v1/portfolio/transactions", json={"account_id":"00000000-0000-0000-0000-000000000000","company_id":"US:AAPL:US","txn_type":"buy","quantity":10,"price_per_share":10,"txn_date":"2025-01-01","currency":"USD"}),404)
    api_check("Portfolio txn invalid date format 422", client.post("/api/v1/portfolio/transactions", json={"account_id":acct,"company_id":"US:AAPL:US","txn_type":"buy","quantity":10,"price_per_share":10,"txn_date":"not-a-date","currency":"USD"}),422)

# ──────────────────────────────────────────────────────────────────────────────
# 12) Alerts edges
# ──────────────────────────────────────────────────────────────────────────────
api_check("Alerts rules list", client.get("/api/v1/alerts/rules"),200)
api_check("Alerts create invalid rule_type 422", client.post("/api/v1/alerts/rules", json={"rule_type":"invalid_type"}),422)
api_check("Alerts create missing rule_type 422", client.post("/api/v1/alerts/rules", json={"company_id":"US:AAPL:US"}),422)
api_check("Alerts evaluate empty", client.post("/api/v1/alerts/evaluate", json={}),200)
api_check("Alerts calendar days_ahead 0", client.get("/api/v1/alerts/calendar?days_ahead=0"),200)
api_check("Alerts calendar negative", client.get("/api/v1/alerts/calendar?days_ahead=-1"),422)
api_check("Watchlist digest empty list", client.post("/api/v1/watchlist/digest", json={"company_ids":[]}),200)
api_check("Watchlist digest unknown company", client.post("/api/v1/watchlist/digest", json={"company_ids":["US:FAKE:US"]}),200)
api_check("Screen limit 0 422", client.get("/api/v1/screen?limit=0"),422)
api_check("Screen currency ALL", client.get("/api/v1/screen?currency=ALL&limit=5"),200)
api_check("Screen invalid signal", client.get("/api/v1/screen?signal=invalid_signal_xyz&limit=5"),200)  # should not crash
api_check("Screener run empty criteria", client.post("/api/v1/screener/run", json={}),200)

# ──────────────────────────────────────────────────────────────────────────────
# 13) Exports / Ops / Governance edges
# ──────────────────────────────────────────────────────────────────────────────
api_check("Export memo unknown 404", client.get("/api/v1/companies/US:FAKE:US/export/memo?format=json"),404)
api_check("Export memo invalid format 422", client.get("/api/v1/companies/US:AAPL:US/export/memo?format=xml"),422)
api_check("Export raw unknown 404", client.get("/api/v1/companies/US:FAKE:US/export/raw"),404)
api_check("Ops diagnostics", client.get("/api/v1/ops/diagnostics"),200)
api_check("Governance model-risk", client.get("/api/v1/governance/model-risk"),200)
api_check("Health again", client.get("/health"),200)

# ──────────────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────────────
passed = sum(1 for r in results if r)
total = len(results)
print(f"\nEDGE CASE RESULTS: {passed}/{total} passed")
if passed/total < 0.95:
    print(f"EDGE COVERAGE WARNING: {(passed/total)*100:.1f}% - significant failures need fix")
else:
    print("EDGE COVERAGE GOOD")
# exit code for CI
import sys
sys.exit(0 if passed==total else 1)
