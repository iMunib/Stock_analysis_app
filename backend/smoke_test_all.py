"""Independent API smoke tests for all router groups - no assumptions, pure functional verification."""
from __future__ import annotations
import os, pathlib, sys
BACKEND_DIR = pathlib.Path(__file__).resolve().parent
os.chdir(BACKEND_DIR)
os.environ["DATABASE_URL"] = f"sqlite:///{(BACKEND_DIR / '.smoke_test.db').as_posix()}"
os.environ["JOBS_WORKER_DISABLED"] = "1"
if (BACKEND_DIR / ".smoke_test.db").exists():
    (BACKEND_DIR / ".smoke_test.db").unlink()

from app.db import Base, SessionLocal, engine
import app.models  # noqa: F401
from app.config import find_seed_workbook
from app.services.importer import run_import
from app.services.scoring_service import recompute
from sqlalchemy import text

# Setup - mimic conftest's isolated DB pattern (Workstream A: create_all + stamp)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
from alembic import command as _alembic_command
from alembic.config import Config as _AlembicConfig
_cfg = _AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{(BACKEND_DIR / '.smoke_test.db').as_posix()}")
_alembic_command.stamp(_cfg, "head")
wb = find_seed_workbook()
assert wb is not None, "seed workbook missing"
run_import(force=True, seed_path=wb)
# also create scores
with SessionLocal() as db:
    recompute(db)
    db.commit()

from fastapi.testclient import TestClient
from app.main import app
# Bypass lifespan alembic check by mocking? The app's lifespan will run but we have no alembic_version table - need to stamp
# Instead we directly create client without lifespan
from app.main import app as raw_app
client = TestClient(raw_app, raise_server_exceptions=False)

def check(name, resp, expect=200, json_keys=None):
    status = resp.status_code
    ok = status == expect
    detail = ""
    if not ok:
        detail = f" got {status} body={resp.text[:400]}"
    else:
        if json_keys:
            try:
                j = resp.json()
                for k in json_keys:
                    if k not in j:
                        ok = False
                        detail = f" missing key {k} in {list(j.keys())}"
                        break
            except Exception as e:
                ok = False
                detail = f" json parse fail {e}"
    icon = "PASS" if ok else "FAIL"
    print(f"{icon} {name}: {status}{detail}")
    return ok

results = []
# 1 Meta / Health
results.append(check("GET /health", client.get("/health"), 200, ["status"]))
results.append(check("GET /ready", client.get("/ready"), 200, ["status"]))
results.append(check("GET /api/v1/meta/disclaimer", client.get("/api/v1/meta/disclaimer"), 200, ["disclaimer"]))
results.append(check("GET /api/v1/stats", client.get("/api/v1/stats"), 200, ["companies"]))
# coverage endpoint is /api/v1/coverage (from financials)
results.append(check("GET /api/v1/coverage", client.get("/api/v1/coverage"), 200, ["companies"]))
# 2 Companies / Search
results.append(check("GET /api/v1/companies", client.get("/api/v1/companies?limit=5"), 200, ["total","items"]))
results.append(check("GET /api/v1/companies?country=CA", client.get("/api/v1/companies?country=CA&limit=2"), 200))
results.append(check("GET /api/v1/search", client.get("/api/v1/search?q=AAPL&limit=5"), 200, ["items"]))
results.append(check("GET /api/v1/search/suggestions", client.get("/api/v1/search/suggestions?q=MSFT&limit=5"), 200, ["items"]))
results.append(check("GET /api/v1/companies/US:MMM:US", client.get("/api/v1/companies/US:MMM:US"), 200, ["company_id"]))
results.append(check("GET /api/v1/companies/US:MMM:US/financials", client.get("/api/v1/companies/US:MMM:US/financials?years=3"), 200, ["items"]))
results.append(check("GET /api/v1/companies/US:MMM:US/statements", client.get("/api/v1/companies/US:MMM:US/statements?limit=3"), 200, ["items"]))
results.append(check("GET /api/v1/companies/US:MMM:US/derived-metrics", client.get("/api/v1/companies/US:MMM:US/derived-metrics?limit=3"), 200, ["items"]))
results.append(check("GET /api/v1/companies/US:MMM:US/benchmarks", client.get("/api/v1/companies/US:MMM:US/benchmarks"), 200, ["items"]))
# 3 Scoring / Metrics
results.append(check("POST /api/v1/scores/recompute", client.post("/api/v1/scores/recompute", json={"universe":"seed"}), 200, ["scored"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/score", client.get("/api/v1/companies/US:AAPL:US/score"), 200, ["composite"]))
results.append(check("GET /api/v1/sectors/Banks/rankings", client.get("/api/v1/sectors/Banks/rankings?currency=USD&limit=5"), 200, ["items"]))
results.append(check("GET /api/v1/rankings", client.get("/api/v1/rankings?limit=5"), 200, ["items"]))
results.append(check("GET /api/v1/scores/summary", client.get("/api/v1/scores/summary"), 200, ["scores_total"]))
results.append(check("GET /api/v1/sectors", client.get("/api/v1/sectors"), 200, ["custom_industries"]))
results.append(check("GET /api/v1/sectors/rotation", client.get("/api/v1/sectors/rotation?currency=ALL"), 200))
results.append(check("GET /api/v1/sectors/Banks/histogram", client.get("/api/v1/sectors/Banks/histogram?currency=USD&metric=composite"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/peer-matrix", client.get("/api/v1/companies/US:AAPL:US/peer-matrix"), 200, ["peer_group"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/pillar-drilldown", client.get("/api/v1/companies/US:AAPL:US/pillar-drilldown"), 200, ["pillars"]))
# 4 Dossier / compare / similar
results.append(check("GET /api/v1/companies/US:AAPL:US/dossier", client.get("/api/v1/companies/US:AAPL:US/dossier"), 200, ["identity"]))
results.append(check("GET /api/v1/compare", client.get("/api/v1/compare?ids=US:AAPL:US,US:MSFT:US"), 200, ["rows"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/similar", client.get("/api/v1/companies/US:AAPL:US/similar?n=3"), 200, ["items"]))
results.append(check("GET /api/v1/sectors/Technology/snapshot", client.get("/api/v1/sectors/Technology/snapshot?currency=USD"), 200, ["companies"]))
# ratio inspector for 12 ratios
for ratio in ["roe","roa","pe","pb","roic","ev_ebitda","current_ratio","interest_coverage","gross_margin","fcf_margin","net_debt_ebitda","net_debt_fcf"]:
    results.append(check(f"GET /api/v1/companies/US:AAPL:US/ratios/{ratio}/inspect", client.get(f"/api/v1/companies/US:AAPL:US/ratios/{ratio}/inspect"), 200, ["ratio_id","numerator"]))
# also CAD
results.append(check("GET /api/v1/companies/CA:RY:TSX/ratios/pb/inspect", client.get("/api/v1/companies/CA:RY:TSX/ratios/pb/inspect"), 200, ["ratio_id"]))
results.append(check("GET /api/v1/coverage/health", client.get("/api/v1/coverage/health"), 200, ["universe_summary"]))
results.append(check("GET /api/v1/factors/evidence", client.get("/api/v1/factors/evidence"), 200, ["canonical_factors"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/bear-case", client.get("/api/v1/companies/US:AAPL:US/bear-case"), 200, ["bear_thesis_narrative"]))
# 5 Forensics
results.append(check("GET /api/v1/companies/US:AAPL:US/forensics", client.get("/api/v1/companies/US:AAPL:US/forensics"), 200, ["sloan_accrual_ratio"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/forensics/summary", client.get("/api/v1/companies/US:AAPL:US/forensics/summary"), 200, ["forensic_health_score"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/forensics/benford", client.get("/api/v1/companies/US:AAPL:US/forensics/benford"), 200, ["verdict"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/forensics/timeline", client.get("/api/v1/companies/US:AAPL:US/forensics/timeline"), 200, ["timeline"]))
results.append(check("GET /api/v1/forensics/rank", client.get("/api/v1/forensics/rank?ids=US:AAPL:US,US:MSFT:US"), 200, ["ranked"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/restatements", client.get("/api/v1/companies/US:AAPL:US/restatements"), 200, ["items"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/trajectory", client.get("/api/v1/companies/US:AAPL:US/trajectory"), 200, ["points"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/working-capital", client.get("/api/v1/companies/US:AAPL:US/working-capital"), 200, ["series"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/goodwill-risk", client.get("/api/v1/companies/US:AAPL:US/goodwill-risk"), 200, ["goodwill"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/dilution", client.get("/api/v1/companies/US:AAPL:US/dilution"), 200, ["series"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/piotroski", client.get("/api/v1/companies/US:AAPL:US/piotroski"), 200, ["f_score"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/dupont", client.get("/api/v1/companies/US:AAPL:US/dupont"), 200, ["is_bank"]))
# 6 Valuation
results.append(check("GET /api/v1/companies/US:AAPL:US/valuation", client.get("/api/v1/companies/US:AAPL:US/valuation"), 200, ["status"]))
results.append(check("GET /api/v1/companies/US:AAPL:US/valuation/epv", client.get("/api/v1/companies/US:AAPL:US/valuation/epv"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/valuation/ddm", client.get("/api/v1/companies/US:AAPL:US/valuation/ddm"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/valuation/guided", client.get("/api/v1/companies/US:AAPL:US/valuation/guided"), 200, ["status"]))
results.append(check("GET /api/v1/valuation/rank", client.get("/api/v1/valuation/rank?ids=US:AAPL:US,US:MSFT:US"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/penman", client.get("/api/v1/companies/US:AAPL:US/penman"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/practitioner", client.get("/api/v1/companies/US:AAPL:US/practitioner"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/financials/common-size", client.get("/api/v1/companies/US:AAPL:US/financials/common-size?years=3"), 200, ["income_statement_common_size"]))
# 7 Portfolio / Alerts / Exports / Screen / Watchlist
results.append(check("GET /api/v1/portfolio/accounts", client.get("/api/v1/portfolio/accounts"), 200))
# create account
resp_acct = client.post("/api/v1/portfolio/accounts", json={"name":"Test TFSA","account_type":"TFSA","currency":"CAD"})
results.append(check("POST /api/v1/portfolio/accounts", resp_acct, 200))
acct_id = None
try:
    acct_id = resp_acct.json().get("id") or resp_acct.json().get("account",{}).get("id")
except: pass
# if creation succeeded, try holdings
results.append(check("GET /api/v1/portfolio/holdings", client.get("/api/v1/portfolio/holdings"), 200))
# create transaction if account
if acct_id:
    # use US:MMM:US as holding
    resp_txn = client.post("/api/v1/portfolio/transactions", json={"account_id": acct_id, "company_id":"US:MMM:US", "txn_type":"buy", "quantity":10, "price_per_share":150.0, "txn_date":"2025-01-15", "currency":"USD"})
    results.append(check("POST /api/v1/portfolio/transactions", resp_txn, 200))
results.append(check("GET /api/v1/portfolio/journal", client.get("/api/v1/portfolio/journal"), 200))
results.append(check("GET /api/v1/alerts/rules", client.get("/api/v1/alerts/rules"), 200))
resp_rule = client.post("/api/v1/alerts/rules", json={"company_id":"US:AAPL:US","rule_type":"distress","params":{"severity":"elevated"}})
results.append(check("POST /api/v1/alerts/rules", resp_rule, 200))
results.append(check("POST /api/v1/alerts/evaluate", client.post("/api/v1/alerts/evaluate", json={}), 200))
results.append(check("GET /api/v1/alerts/calendar", client.get("/api/v1/alerts/calendar?days_ahead=30"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/export/memo", client.get("/api/v1/companies/US:AAPL:US/export/memo?format=json"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/export/raw", client.get("/api/v1/companies/US:AAPL:US/export/raw"), 200))
results.append(check("POST /api/v1/watchlist/digest", client.post("/api/v1/watchlist/digest", json={"company_ids":["US:AAPL:US"]}), 200))
results.append(check("GET /api/v1/screen", client.get("/api/v1/screen?currency=USD&limit=5"), 200, ["items"]))
results.append(check("GET /api/v1/etfs/top-cohorts", client.get("/api/v1/etfs/top-cohorts"), 200))
# 8 Canada / Insiders / Technicals
results.append(check("GET /api/v1/canada/companies/CA:RY:TSX/tax-placement", client.get("/api/v1/canada/companies/CA:RY:TSX/tax-placement"), 200))
results.append(check("GET /api/v1/canada/companies/CA:RY:TSX/canadian-metrics", client.get("/api/v1/canada/companies/CA:RY:TSX/canadian-metrics"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/technicals", client.get("/api/v1/companies/US:AAPL:US/technicals"), 200))
results.append(check("GET /api/v1/companies/US:AAPL:US/insiders", client.get("/api/v1/companies/US:AAPL:US/insiders"), 200))
results.append(check("GET /api/v1/insiders/cluster", client.get("/api/v1/insiders/cluster?ids=US:AAPL:US,US:MSFT:US"), 200))
# 9 Jobs / LLM / Ops / Governance
results.append(check("GET /api/v1/jobs", client.get("/api/v1/jobs?limit=5"), 200, ["items"]))
# ingest enqueue
resp_ing = client.post("/api/v1/tickers/ingest", json={"ticker":"AAPL","refresh":False})
results.append(check("POST /api/v1/tickers/ingest", resp_ing, 202))
results.append(check("GET /api/v1/research/meta", client.get("/api/v1/research/meta"), 200, ["companies"]))
results.append(check("GET /api/v1/ops/diagnostics", client.get("/api/v1/ops/diagnostics"), 200))
results.append(check("GET /api/v1/ops/backups", client.get("/api/v1/ops/backups"), 200))
results.append(check("GET /api/v1/governance/model-risk", client.get("/api/v1/governance/model-risk"), 200))
results.append(check("GET /api/v1/governance/canon-map", client.get("/api/v1/governance/canon-map"), 200))
# check 404 handling
results.append(check("GET /api/v1/companies/US:FAKE:US 404", client.get("/api/v1/companies/US:FAKE:US"), 404))
results.append(check("GET /api/v1/companies/US:AAPL:US/ratios/unknown_ratio/inspect unknown handles", client.get("/api/v1/companies/US:AAPL:US/ratios/unknown_ratio/inspect"), 200, ["ratio_id"]))
# Search negative
results.append(check("GET /api/v1/search?q=nonexistentxyz", client.get("/api/v1/search?q=nonexistentxyz&limit=5"), 200, ["items"]))

print("\n" + "="*70)
passed = sum(results)
total = len(results)
print(f"SMOKE RESULT: {passed}/{total} passed")
if passed == total:
    print("ALL APIS FUNCTIONAL - CLEAN CODE CHANGES VERIFIED")
else:
    print(f"FAILED: {total-passed} endpoints")
    sys.exit(1)
