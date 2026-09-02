# TRUST_REPORT.md

**Sprint:** Trust, Freshness, and Clean-Room Verification (Workstreams A–E)
**Repository:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-02
**Verdict: ALL WORKSTREAMS DELIVERED — ALL VERIFICATION GATES PASS**

## Final test suite counts

| Suite | Count | Notes |
|---|---|---|
| Backend pytest (full) | **151 passed** | includes clean-room, golden battery, screener, TTM/valuation, history-sanity |
| — Clean-room runner (`test_clean_room.py`) | 1 | runs `python -m app.jobs.verify_clean_room` as a real subprocess |
| — Golden ticker battery (`test_zz_golden_tickers.py` + directive-named alias) | 10 + 2 | 10 golden paths; alias re-runs the 2 pure read-only paths in-process |
| Frontend vitest | **86 passed** | includes ReverseDCFCard/ForensicCard suites (hooks-order regression caught & fixed) |
| `npm run build` (tsc + vite) | 0 errors | strict TypeScript |
| Playwright e2e | 10 passed (+ known timing flakes pass on retry) | dossier grid, suspect chips, compare %, screener |

## Clean-room verification proof

`python -m app.jobs.verify_clean_room` (exit 0):

```
[clean-room] booting isolated temporary SQLite database
[clean-room] alembic upgrade head from empty file
[clean-room] schema verified (N tables), stamp=('e9f2a7b3c501',)
[clean-room] running real importer on owner workbook
[clean-room] imported: 720 companies (500 USD / 220 CAD), 1506 placements, 2026 quality flags
[clean-room] scoring US:MSFT:US (USD) and CA:RY:TSX (CAD)
[clean-room] TestClient smoke: /health, /api/v1/stats, MSFT dossier
[clean-room] teardown complete
CLEAN-ROOM OK: zero -> migrated -> imported (720/1506) -> scored -> served
```

Zero `create_all` remains on any production boot path (only the ephemeral pytest
fixture + the clean-room's own assertion harness touch metadata directly; the
runner invokes real Alembic migrations from an empty file).

## AAPL ROIC & MSFT history verification outcomes

- **US:AAPL:US** — reverse-DCF inputs healthy but book equity shrunk by buybacks:
  live TTM row carries `roic_confidence="low"`,
  `roic_interpretation="distorted_low_denominator"`,
  `roic_warning_reason="small_invested_capital_denominator"`. The ForensicCard and
  Screener suppress the green MOAT / "ROIC 20%+" badge for every low-confidence
  row and render the amber "ROIC distorted" chip with the buyback explanation.
- **US:MSFT:US** — history trust intact after the EDGAR duration-gate fix: the
  $23–31B "FY2017–2019" rows stay flagged `SCALE_OR_TAG_SUSPECT`, are excluded
  from growth CAGR and bars, remain visible with chips, and the dossier payload
  reports `history_warnings` for FY2017/18/19. Trusted FY revenue asserted > $60B.
- Live telemetry snapshot (`GET /api/v1/system/health/telemetry`):
  `migration_revision == alembic_head == e9f2a7b3c501`, `schema_verified: true`,
  `low_confidence_roic_count: 125`, `stale_price_count: 720/720 priced`
  (local-first snapshot; prices age honestly — refresh jobs update them).

## Golden ticker suite matrix

| # | Ticker | Rule | Result |
|---|---|---|---|
| 1 | US:MSFT:US | duration gate; suspect chipped, growth excluded, never deleted | PASS |
| 2 | US:AAPL:US | ROIC > 1.0 / tiny IC => confidence low; no unqualified MOAT badge | PASS |
| 3 | US:PYPL:US | payments = commercial metrics; ROIC suppressed where classified | PASS |
| 4 | CA:RY:TSX | CAD only; CET1/efficiency preserved; ROIC `bank_excluded` | PASS |
| 5 | CA:KITS:TSX | `KITS.TO` → frozen id; on-demand universe entry | PASS |
| 6 | US:BABA:US | CNY statements + USD price → multiples suppressed with reason | PASS |
| 7 | US:AFL:US | insurer: debt/gross profit not force-filled; ROIC n/m | PASS |
| 8 | CA:IIP.UN:TSX | sparse data: composite None + `insufficient_data`, no crash | PASS |
| 9 | US:AMD:US | ingest 202 → state machine → terminal; score on success | PASS |
| 10 | INVALID_TICKER_XYZ | `failed` + `SYMBOL_NOT_FOUND` + actionable copy | PASS |

Details: `docs/GOLDEN_TICKERS.md`.

## Residual provider rate limits and local SQLite considerations

- **Rate limits:** EDGAR requires a declared User-Agent (`SEC_USER_AGENT`);
  full-720 refreshes are throttled by design (async 202 jobs, one backfill at a
  time, 409 while busy). Yahoo is used without a key and may rate-limit bursts —
  the job worker isolates per-ticker failures so one 429 cannot kill a batch.
- **SQLite (WAL):** single-writer; the app relies on `busy_timeout=5000` +
  WAL for concurrent readers. The job worker is the only writer thread; API
  writes are limited to job enqueue/score recompute. For heavier refresh
  schedules, run refreshes off-peak (REFRESH_ENABLED + REFRESH_INTERVAL_HOURS).
- **Price staleness is honest:** every valuation surfaces `price_freshness`
  (green/amber/red) and the reverse-DCF card warns + offers "Refresh Price &
  Recompute" instead of silently trusting old prices.
- Known timing flakes in Playwright (Banks-All, compare %) pass individually and
  on retry; unrelated to trust logic.

STOP — trust sprint complete.

---

# Addendum: Analytical Engines Sprint (2026-09-02, WS2-WS6)

New engines and their verification, appended to the trust report:

## Engines delivered
- **Penman reformulation** (`penman_engine.py`, migration `f4c8d9e2a603`):
  NOA/NFO split with equity identity check (5%-of-assets tolerance), NOPAT
  (tax clamped 15-30%), RNOA, FLEV, NBC, DuPont spread. Materialized for 396
  complete rows + 100 `financial_institution_excluded`; 36 rows flagged
  `leverage_distortion`. Answers WS2's AAPL question directly: AAPL's ROIC
  distortion is now decomposed as RNOA 81.8% with FLEV 0.74 — the naive ROIC
  vs RNOA gap is shown side by side in `PenmanCard`.
- **Schilit shenanigans** (`forensic_engine.py`): CFO/NI decoupling computed
  across FY pairs; DSO/inventory/AQI honestly reported as `data_available:
  false` (schema lacks AR/inventory/current-asset lines — no fabrication).
  EQR 0-100 stored on TTM rows, filterable via screener `eqr_min`/`eqr_max`.
  AMD: EQR 75 with `RED_FLAG_CFO_EARNINGS_DECOUPLING` (verified live).
- **Graham floors** (`graham_engine.py`): Graham Number, NCAV, NNWC (35%
  proxy documented where detail is absent), margin-of-safety, deep-net-net
  chip. MSFT: Graham Number $155.12 vs $483.24 price (MoS −67.9%).
- **Malkiel/Collins index hurdle** (ReverseDCFCard): owner FCF yield vs 4.5%
  baseline, required growth for the 8% compounding hurdle, ETF takeaway.
- **Ittelson cash bridge** (`viz/CashFlowBridge.tsx`): pure-SVG waterfall with
  tabular fallback; no chart libraries.

## API additions
`GET /companies/{id}/penman` · `/schilit` · `/graham`; screener criteria
`eqr_min`/`eqr_max`; screener rows now carry `eqr`.

## Verification (all pass on the rebuilt stack)
| Gate | Result |
|---|---|
| `python -m app.jobs.verify_clean_room` | CLEAN-ROOM OK, exit 0 (720/1506) |
| `pytest backend/ -q` | **154 passed** (3 new golden paths: Penman AAPL-vs-RY, Schilit MSFT clean, Graham MSFT) |
| `npx vitest run` | **86 passed** (mocks extended for the new api methods) |
| `npm run build` | 0 errors |
| `npx playwright test` | 14 passed (0 failures on rebuilt stack) |
| Live smoke | AAPL penman RNOA 81.8% · RY excluded · AMD EQR 75 · MSFT Graham $155.12 · screener `eqr_max=99` returns exactly AMD |

Invariants preserved: MATH v1 weights untouched; CAD/USD never mixed; seed
workbook read-only (mtime unchanged); zero paid APIs; pure SVG/CSS UI.