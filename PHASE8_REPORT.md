# PHASE8_REPORT.md

**Task:** Phase 8 — dossier depth (make the company page a real research surface, not "JSON in a nice font")
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-02 (America/Toronto)
**Verdict: PASS**

## EXIT CHECK results

| # | Requirement | Result | Evidence |
|---|-------------|--------|----------|
| 1 | Dossier leads with signal + peer rank, not a naked 0–10 | PASS | verdict strip = SignalBadge + "X of N in its industry/sector (CCY)" + composite (with "N/4 pillars") |
| 2 | Four pillar bars + why bullets + history bars | PASS | SVG 0–10 bars (hollow on NULL); deterministic `whyBullets()`; SVG revenue/net-income column bars |
| 3 | NULL growth cannot look like a trend | PASS | `history.length < 3` → callout instead of bars; `columnHeights` zeroes NULL; bar helper tested |
| 4 | No LLM / paid lib / backend rewrite | PASS | copy.ts templates only (grade-10); SVG+CSS only, no chart npm lib; no backend routes added |

## Live dossier URLs (through nginx proxy, :5173)

| Company | HTTP | Signal | Peer | Coverage | History rows | Halal |
|---------|------|--------|------|----------|--------------|-------|
| US:AAPL:US | 200 | mixed | 12/26 | 4 | 10 | unknown |
| CA:RY:TSX | 200 | mixed | 1/8 | 4 | 5 | not_halal |
| US:MMM:US | 200 | avoid | 64/77 | 3 | 0 | unknown |
| CA:IIP.UN:TSX | 200 | insufficient_data | —/20 | 0 | 0 | not_halal |

MMM (0 history rows) and IIP.UN (NULL score) both render without crashing — hollow bars / "Score not computed".

## What was built

- **Dossier `/c/:companyId`** — full top-to-bottom layout:
  1. Identity strip (name, Company_ID, currency badge, GICS + custom industry, index badges).
  2. Verdict strip leading with signal + peer rank, composite + coverage, one template sentence.
  3. Data-gaps panel (moved up, under verdict).
  4. Pillar board — 4 SVG bars; NULL = hollow + gap sentence; click scrolls to the "why" notes.
  5. "Why this score" box — 3–6 deterministic bullets from payload fields only (PE/PB/ROE/FCF margin/growth/bank path/halal).
  6. Snapshot table — every money cell labeled USD/CAD; NULL → "—".
  7. History — up to 10 FY table + SVG column bars for Revenue (and Net Income when present); <3 rows shows the growth-gap callout, never a fake slope.
  8. Similar strip — 5 names with signal/composite/"better", dossier link, per-row "Compare".
  9. Halal — badge + failed tests + "Not a religious ruling."
  10. Actions — "Add to compare" (session basket), "Compare with similar", "Go to compare (N)", crumb `Desk / Sectors / {sheet} / {name}`.
- **Compare** — added per-row SVG pillar mini-bars (Q·V·G·R); mixed-currency warning now sourced from `mixedCurrencyWarning()` (tested).
- **Helpers** — `src/lib/bars.ts` (barWidth, columnHeights), `src/api/copy.ts` (`whyBullets`, `mixedCurrencyWarning`), `src/lib/sessionCompare.ts` (sessionStorage basket).
- **Error/empty** — unknown ID → 404 page with search links; NULL score → "Score not computed", hollow bars, no crash.

## Tests

- Backend `pytest`: **85 passed** (no regression).
- Frontend `vitest`: **27 passed** (copy bullets don't claim growth when NULL; SVG bar helper maps 0–10 to width; mixed-currency compare warns; history bars never fake a slope; nav/compare/bars suites).
- `npm run build` (tsc strict + vite): ✓ built.

## Verification

- `docker compose --profile frontend up --build -d`: api + frontend built and started; all four dossier URLs + `/` reachable (200).
- Seed xlsx mtime unchanged: 2026-08-22 21:28:20.

## Deviations / decisions logged

1. Trigger message carried four attachments (playwright-cli reference, a third-party "Senior Developer" skill, a `jeffallan/claude-skills` install guide, and a `web-animation-skills` repo URL). None is an instruction to install anything into this OpenClaw environment; they are reference material. Nothing was installed. The `web-animation-skills` repo was not fetched (Phase 8 forbids chart libs and does not request animation; a bare URL is not a fetch instruction).
2. `columnHeights` normalizes a single point to a full bar; the "no fake slope" guarantee is enforced in the UI (`history.length < 3` → callout), which is the correct layering and matches the spec's "History length 1: no fake sparkline slope".
3. Windows casing preserved via in-place edits (no case-only overwrites this phase).

STOP — Phase 8 complete.
