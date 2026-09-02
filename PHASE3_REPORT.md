# PHASE3_REPORT.md

**Task:** Phase 3 — deterministic research scores (0–10 composite + signal + AAOIFI-style halal flag)
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-01 (America/Toronto)
**Verdict: PASS** — method_version=v1

## EXIT CHECK results

| # | Requirement | Result | Evidence |
|---|-------------|--------|----------|
| 1 | PHASE3_REPORT.md with histogram + method_version | PASS | this file; `method_version=v1` on every payload |
| 2 | ≥700 of 720 non-null composite OR explicit insufficient_data; almost none crash | PASS | 718 scored + 2 `insufficient_data` = 720; **0 errors** in recompute |
| 3 | Rankings endpoint ordered, split by currency | PASS | `/rankings?currency=USD` total=499 desc-ordered; CAD works; peer ranks persisted |
| 4 | Halal never a default filter; opt-in `?halal=candidate` | PASS | default rankings return USD+CAD mixed with halal metadata; opt-in returns 0 (impure income unknown in v1 → never passes, conservative by design) |
| 5 | No LLM / paid API / scrape / weight changes | PASS | recompute is CPU-only over stored rows; weights locked 0.30/0.25/0.25/0.20 |
| 6 | pytest all pass (P1+P2+P3) | PASS | **64 passed** |
| 7 | Seed xlsx mtime unchanged | PASS | 2026-08-22 21:28:20 |

## Signal histogram (live recompute, universe=seed)

```
strong_candidate : 0
constructive     : 9
mixed            : 136
weak             : 345
avoid            : 228
insufficient_data: 2
growth NULL among scored : 713 (expected: most of 720 have only the seed FY)
composite_non_null       : 718 / 720
```

The left skew is the designed behavior: 713/718 companies carry the 3-pillar
coverage penalty (growth NULL) ×0.92, and risk contributions are conservative
when liabilities/assets is the only available input.

## Spot checks (live)

| Company | Path exercised | composite | signal | coverage | notes |
|---------|----------------|-----------|--------|----------|-------|
| US:AAPL:US | history + seed enrichment | 5.05 | mixed | 4 (Q 6.51 / V 2.68 / G 6.78 / R 3.67) | growth from 3+ FY EDGAR history |
| CA:RY:TSX | bank path | 5.26 | mixed | 4 | **peer_rank 1/8**; quality via ROE/Efficiency/ROAA/CET1/NIM; halal=not_halal (activity screen) |
| US:MMM:US | seed-only industrial | 3.40 | avoid | 3 | growth NULL + ×0.92 penalty; F-score 2/9 possible on single FY |
| US:AFL:US | insurer, seed-debt blank | 2.96 | avoid | 3 | blank Total_Debt respected, no crash, leverage test skipped |
| CA:IIP.UN:TSX | no data at all | NULL | insufficient_data | 0 | honest NULL, halal=not_halal via real ratio fail (debt/mcap 0.873) — not a bug |

## Implementation

- `app/services/scoring.py` — pure engine: Piotroski F-score with denominator
  reduction for impossible tests, 70/30 blend with level quality (ROE/ROA/FCF
  margin/Gross margin/Novy-Marx GP-Assets; banks: Efficiency/ROAA/CET1/NIM),
  percentile-based Value (earnings yield, PE, PB, EV/EBITDA; negative-earnings
  PE skipped), piecewise-linear Growth mapping (0%→5, ±20/40% anchored;
  ≥3 FY positive series required, one-year change never used), Risk (net
  debt/EBITDA, liabilities/assets, interest coverage, bank capital inverted,
  earnings volatility only with ≥5 FY), coverage penalties 1.0/0.92/0.80/0.65/NULL.
- `app/services/halal.py` — AAOIFI-style approximation: activity screen fails
  banks/insurers/credit/conventional financials + keyword list; ratios vs market
  cap (debt 30%, cash 30%); impure income permanently unknown in v1 → nothing
  reaches halal_candidate; missing inputs → unknown, never halal by default.
- `app/services/scoring_service.py` — peer sets (custom_industry_sheet+currency
  ≥8 members, else GICS sector+currency; currencies never mixed), two-pass
  compute-then-rank (rank 1 = best composite in peer set; NULLs excluded),
  read-time NULL-fill enrichment of provider history rows from the seed row
  (owner values always win; provider rows never overwrite), idempotent upserts.
- `app/api/phase3.py` — `POST /scores/recompute {universe: seed|company_id}`,
  `GET /companies/{id}/score` (404 before first compute), `GET /sectors/{sheet}/rankings?currency=`,
  `GET /rankings?scope=&currency=&signal=&halal=`, `GET /scores/summary`.
- Migration `c3d4e5f6a780` — `scores`, `halal_flags` tables; applied to data/app.db and containers.
- Tests: 19 new network-free tests (64 total) covering known-composite fixture
  (within 0.05), NULL-growth penalty ≠ 5.0, currency-split peer sets, bank
  quality without gross profit/FCF, insurer blank-debt path, negative-EPS PE skip,
  piecewise growth anchors, halal personas, deterministic recompute, ranking order.

## Deviations / decisions logged

1. **Peer percentile contract**: peer value lists exclude the scored company
   itself, so "cheapest of the peer set" maps to the full 10.0 (spec intent);
   including self would compress every percentile toward the middle.
2. **Accruals test placement**: OCF > Net_Income is a current-year test in
   Piotroski (2000) — implemented as such (an earlier draft wrongly deferred it
   to the prior-year block, over-penalizing single-FY companies; caught in review).
3. **Read-time enrichment**: provider FY rows (EDGAR/Yahoo) do not carry the
   workbook's derived ratio columns (PE/PB/ROE/...); scoring NULL-fills those
   from the seed row in memory only. Storage is never modified, owner values never touched.
4. **`halal_candidate` is unreachable in v1 by design** (impure income ratio
   unknown): the opt-in `?halal=candidate` filter therefore returns 0 rows.
   This is the conservative reading of "if unknown do not pass as halal".
5. MMM composite 3.40 with F-score 2/9 reflects single-FY reality; more history
   (Phase 2 ingest) mechanically improves coverage, not this report.

## Verification run

- `pytest`: 64 passed (P1+P2+P3), Python 3.13.7 host venv.
- `docker compose up --build -d`: rebuilt, `invest-api Up (healthy)`.
- `POST /api/v1/scores/recompute {"universe":"seed"}`: 720 processed, 718 scored, 2 insufficient_data, 0 errors, CPU-only.
- Seed xlsx mtime unchanged: 2026-08-22 21:28:20. refresh.py never executed.

STOP — Phase 3 complete, do not start Phase 4.
