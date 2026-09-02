# PHASE4_REPORT.md

**Task:** Phase 4 — complete the research API: search, dossier, compare, similar, sector snapshot, research/meta
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-02 (America/Toronto)
**Verdict: PASS**

## EXIT CHECK results

| # | Requirement | Result | Evidence |
|---|-------------|--------|----------|
| 1 | PHASE4_REPORT.md exists | PASS | this file |
| 2 | All six endpoint families work live | PASS | see JSON summaries below |
| 3 | Mixed-currency compare warns and does not convert | PASS | `currency_warning=true`, money per-row native currency, ratios/scores comparable |
| 4 | Sector snapshot currency-gated and de-duplicated | PASS | missing currency → 400; one row per company_id |
| 5 | No UI spa, no LLM, no weight changes, no scrape | PASS | read-only GETs; no network/ingest/recompute in handlers; weights untouched |

## Live JSON summaries (abridged — not full dumps)

**search?q=AAPL** → `{"count":1, items:[{company_id:"US:AAPL:US", composite:5.0499, signal:"mixed", peer_rank:12, peer_n:26}]}`
**search?q=RY** → `{"count":9, ...}` includes `CA:RY:TSX` (Royal Bank of Canada).

**dossier US:AAPL:US** → identity USD; score composite 5.0499; history_annual 10 rows; data_gaps [] (seed row fills debt/PE/PB/etc.).

**compare?ids=US:AAPL:US,CA:RY:TSX** → `currency_warning=true`, `currencies:["USD","CAD"]`, rows ordered desc: CA:RY:TSX=5.2643 then US:AAPL:US=5.0499.

**similar US:MMM:US n=3** → 3 peers (US:AOS:US 6.58, US:SNA:US 6.51, US:CPRT:US 6.40), all `better=true` (MMM composite 3.40).

**sectors/Software/snapshot?currency=USD** → companies=21, scored=21, median_composite=4.81, top1=US:ACN:US.
**sectors/Banks/snapshot?currency=CAD** → companies=8, scored=8, median_roe=0.1089.

**research/meta** → companies=720, scored=718, insufficient_data=2, growth_null=713 (matches Phase 3 histogram).

Seed xlsx mtime unchanged: 2026-08-22 21:28:20.

## Implementation

- `app/api/phase4.py` — six read-only endpoints, all with `Cache-Control: private, max-age=60`,
  OpenAPI descriptions, and `response_model`. Every payload carries `disclaimer` + `method_version=v1`.
- `app/services/scoring_service.py` — exposed `load_universe` / `snapshot_dict` /
  `enrich_with_seed` (single source of truth for seed-row enrichment, shared by scoring and the API).
- Search matches ticker / name / Company_ID / Yahoo symbol (Yahoo symbols indexed from universe_master.csv).
- Dossier = identity + seed-enriched snapshot + up to 10 FY history + score + halal (with failed tests) + data_gaps.
- Compare: 2–8 ids (else 400), mixed currency → warning + per-row money, ratio/score columns comparable, ordered desc with NULL last.
- Similar: same peer set as scoring, non-null composites only, `better` flag; NULL subject score → 409 insufficient_data.
- Sector snapshot: currency required (400), null-safe medians (composite/PE/PB/ROE), signal histogram, top/bottom 10, de-duplicated.
- Tests: 15 new network-free tests (79 total). Empty-scores-table path verified (endpoints still respond, scores null).

## Deviations / decisions logged

1. **No subagents were dispatchable** (`sessions_spawn` has no agent IDs in this session:
   `agents_list` → `allowAny:false, agents:[]`). Recorded `cluster_bypass_reason` in `.cluster/phase4/plan.md`; implemented solo with full pytest + docker + live verification.
2. `/frontend-design` was invoked, but the Phase 4 master prompt explicitly forbids building the UI
   ("Do not build the real UI (Phase 5)", "No UI spa"); the skill's guidance applies in Phase 5.
3. Empty-`q` and missing-`currency` return 400 (manual checks) rather than FastAPI's 422, matching the spec.
4. Search shows `ticker` as stored (e.g. RY.TO for CA:RY:TSX per the seed's Primary_Ticker); Company_ID stays frozen `CA:RY:TSX`.

## Verification run

- `pytest`: **79 passed** (P1+P2+P3+P4), Python 3.13.7 host venv.
- `docker compose up --build -d`: rebuilt, `invest-api Up (healthy)`.
- All six families hit live on :8000 (summaries above).
- Seed xlsx mtime unchanged: 2026-08-22 21:28:20.

STOP — Phase 4 complete, do not start Phase 5.
