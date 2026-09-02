# SPRINT_REPORT.md

**Task:** Layout + data-trust sprint (Sections A–E)
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-02
**Verdict: ALL SECTIONS PASS**

## Before → after: the MSFT revenue bug

**Observed before:** MSFT dossier showed FY2026–2020 revenue in the right ballpark
($331B…$143B) then FY2019–2017 at ~$23–31B (impossible vs FY2020 $143B); FY2022 blank.
Compare showed ROE as `0.3` while the dossier showed `30.2%`.

**Root cause (confirmed by code inspection + fixture test):** the EDGAR companyfacts
parser accepted any `frame: "CY####…"` — including **quarterly frames** like
`CY2017Q1` — so 90-day revenue facts stole FY years. No duration check existed, and
duplicate facts for the same year were won by whichever arrived first.

**Fix (A):**
1. Duration gate: income-statement facts must span ~300–400 days; explicit `Q` frames
   rejected; annual-duration facts without a frame still require `fp=FY` + December end.
2. Duplicate facts for the same year now prefer the one closest to 365 days.
3. `sanitize_history()` (read path, `app/services/history_sanity.py`): years with
   revenue < 0.25× or > 4× the strong-year median (median of values ≥ 40th percentile)
   get `quality_flag=SCALE_OR_TAG_SUSPECT`, are **excluded from growth CAGR and bars**,
   but remain visible in the table with a chip. Stored rows are never deleted.
4. MSFT rescored on the sanitized read path: growth 6.93 → **6.31**, composite
   6.06 → **5.78** (weights untouched).

**After:** suspect years still visible (italic + chip, in the live API + UI), bars
use sanitized years only, real holes (FY2022 NULL) stay holes, growth ignores the
$23–31B years.

## Sections delivered

| Section | What shipped |
|---|---|
| A — History sanity | parser duration gate + duplicate preference; `sanitize_history` wired into scoring growth + dossier API (`quality_flag`, `warning`, `used_for_growth` per row); 6 new tests incl. the exact MSFT-like fixture `[331B, 281B, 245B, 212B, 143B, 30B, 26B, 23B]` → 30/26/23 excluded |
| B — Formatting | `format.ts`: `percentish` (0.302 → 30.2%, 30.2 → 30.2%), multiples one decimal, money with currency, YoY; compare now shows ROE 30.2% (never 0.3) |
| C — Dossier grid | 12-column CSS grid (~1280px): hero(8)+verdict(4), 4 pillar bars in one row, why+gaps(7) with similar-table(5), snapshot as 18 tiles in a 4-wide grid with YoY deltas (incl. Total debt, Cash, Net debt, Shares, Book equity), history table (YoY + suspect chips) beside sanitized bars, watch toggle, 10-K/SEDAR+ links, narration below; 1-column <900px |
| D — Compare board | sticky company column, percent/multiple formats, SVG pillar bars primary, best-value highlight row (Best PE/ROE/composite by name), Halal column only with `?halal=1`, mixed-currency warning intact |
| E — Watchlist | localStorage `watchIds` (max 50), ☆/★ toggle on dossier, Desk watchlist grid with signal/composite/peer rank; **also fixed**: compare basket now really persists under `compareIds` (was a placeholder key — found by the Playwright localStorage assertion) |

## Test counts

| Suite | Result |
|---|---|
| backend pytest | **107 passed** (6 new sprint-A tests: fixture series, real-hole, healthy series, duration gate, 365d preference, live-DB read-path check) |
| frontend vitest | **39 passed** (10 new: format percentish/multiple/money/yoy, watchlist/compare caps, bars) |
| npm run build | ✓ |
| Playwright | full suite: **12 passed + 2 flaky-recovered** (Banks All from Phase 9 and MSFT-suspect-chip pass on retry; both pass individually — documented timing flakes under 3-worker load) |

## Live verification

- `docker compose --profile frontend up --build -d` rebuilt both images; containers healthy.
- MSFT dossier: snapshot tiles include Total debt / Cash / Net debt / Shares; provenance
  line visible; watch toggle persists to `localStorage.watchIds`; suspect years chipped;
  bars sanitized; EPS column renders diluted values.
- Compare MSFT+ACN: ROE 30.2% (not 0.3), best-value legend row present, no Halal column
  by default.
- Junk id → friendly 404. Seed xlsx mtime unchanged: 2026-08-22 21:28:20.

## Leftover (explicitly not done here)

- Full re-ingest of all 720 to rewrite stored history with clean tags (read-path filter
  already protects the UI; a re-ingest would also fix stored rows).
- Watchlist sync across devices (local-only by design).
- News, LLM feature work, and the 720 backfill: out of scope per master prompt.

STOP — sprint complete.
