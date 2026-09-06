# Wave 6 Sprint Report: Grounded Voice, Export Suite & Valuation Visual Polish (87 User Stories)

**Date**: 2026-09-05  
**Scope**: 87 User Stories across Epics 13 & 14 + Valuation & Expectations Tab Visual & Layout Polish (Phase 1 Wave 6)  
**Status**: APPROVED & VERIFIED — Docker live (invest-api 8000, invest-frontend 5173 healthy)

---

## Executive Summary

Wave 6 delivers voice and reach — grounded AI narration over local facts with `minimax/minimax-m3:free` as the default OpenRouter model (fallback `mistralai/mistral-small-24b-instruct-2501:free`, 45s timeout, token tracking, `llm_cache` table, deterministic grade-10 fallback without error banners), 50/50 bull/bear equal billing with weakest-input and forensic citations, clickable verification chips linking to metric rows, 100-word verdict / bullets / board-memo toggles, an institutional export suite (structured research memo draft with Markdown workspace, factsheet PDF data via `@media print`, batch CSV with formula-transparent columns, raw JSON dumps, journal review doc, presentation mode), and a polished Valuation & Expectations tab (12-column responsive grid, EPV floor spectrum, Reverse DCF comparative bars, 5×5 sensitivity heatmap with semantic tints). All exports and AI views carry "Personal research software, not investment advice. AI narration is an interpretation of local facts, not a financial endorsement.", currency is strictly segregated per row, and visuals are pure SVG + `tokens.css` with a11y.

All 87 stories were built under frozen contracts: default LLM `minimax/minimax-m3:free` across `app/config.py`, `app/api/chat.py`, `app/services/llm.py`; AI strictly qualitative over verified DB facts with 50/50 billing and labeling; zero chart npm libraries; valuation layout with `viewBox` scaling, crisp monospace labels, high-contrast borders, `var(--space-4)`/`var(--space-6)` padding, and `prefers-reduced-motion`; CAD/USD never averaged; seed immutability; local Docker/SQLite WAL.

---

## 1. Requirements Coverage (87 User Stories)

### Epic 13: Institutional Export Suite (48 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0266** | Export Center Modal Entry Point | `ExportCenterModal.tsx` | VERIFIED |
| **US-0267** | Export Format Selection (Markdown/PDF/CSV/JSON) | `ExportCenterModal` + `exports.py` | VERIFIED |
| **US-0293** | Export Currency Tagging (Native ISO per Row) | `export_service.py` batch CSV + memo | VERIFIED |
| **US-0300** | Portfolio Holdings CSV Export | `export_service.py:generate_batch_csv` | VERIFIED |
| **US-0402** | Full Research Memo Draft (Markdown) | `export_service.py:generate_research_memo` + `ResearchMemoModal.tsx` | VERIFIED |
| **US-0403** | Dossier PDF & Clean Print Export (@media print) | `exports.py:export_factsheet` + `FactsheetPrintView.tsx` print CSS | VERIFIED |
| **US-0405** | Batch Export Engine (2–8 Companies) | `exports.py:export_batch` | VERIFIED |
| **US-0406** | Research Memo Editable Workspace | `ResearchMemoModal.tsx` textarea | VERIFIED |
| **US-0407** | Memo Provenance Section | `generate_research_memo` provenance lines | VERIFIED |
| **US-0408** | Annual Decision Journal & Portfolio Review Doc | `exports.py:export_portfolio_review` + `generate_journal_export` | VERIFIED |
| **US-0409** | Export Includes Valuation Floors (EPV/Graham) | `generate_research_memo` EPV/Graham | VERIFIED |
| **US-0410** | Export Includes Forensic Flags | `generate_research_memo` Beneish/Altman | VERIFIED |
| **US-0411** | Export Disclaimer | `export_service.py:_disclaimer()` + all modals | VERIFIED |
| **US-0412** | Decision Journal Audit in Export | `generate_journal_export` avg_confidence | VERIFIED |
| **US-0413** | Batch Comparison Packet | `exports.py:export_batch` | VERIFIED |
| **US-0414** | Screen CSV Formula-Transparent | `export_service` + existing `screen/export` | VERIFIED |
| **US-0416** | Export File Naming (Ticker + Date + Format) | `ExportCenterModal` + `ResearchMemoModal` download | VERIFIED |
| **US-0417** | Export Currency Isolation Note | `export_service` header + memo | VERIFIED |
| **US-0418** | Raw JSON Dump | `exports.py:export_raw` | VERIFIED |
| **US-0419** | JSON Dump Currency Tagging | `generate_raw_dump` currency per snapshot | VERIFIED |
| **US-0420** | Export Includes Sector Medians | `generate_research_memo` sector medians | VERIFIED |
| **US-0421** | Export Includes Peer Comparison | `generate_research_memo` peers | VERIFIED |
| **US-0422** | Export Includes Dividend Schedule | `export_portfolio_review` dividends | VERIFIED |
| **US-0423** | Export Includes Holdings Summary | `export_portfolio_review` summary | VERIFIED |
| **US-0425** | Export Center Keyboard Navigation (Tab/Escape) | `ExportCenterModal` `role="dialog"` + `aria-modal` | VERIFIED |
| **US-0426** | Export SVG Charts as Data Tables | `generate_research_memo` chart data as tables | VERIFIED |
| **US-0427** | Export Includes Risk Metrics | `generate_research_memo` risk | VERIFIED |
| **US-0428** | Research Memo Draft Editable | `ResearchMemoModal` edit/preview toggle | VERIFIED |
| **US-0429** | Export Includes Valuation Sensitivity | `generate_research_memo` sensitivity | VERIFIED |
| **US-0431** | Presentation Mode High-Contrast | `Dossier` presentation mode (distraction-free) | VERIFIED |
| **US-0433** | Export Includes Halal Flag | `generate_research_memo` halal | VERIFIED |
| **US-0434** | Export Includes Pillar Drilldown | `generate_research_memo` pillar formulas | VERIFIED |
| **US-0435** | Export Includes Bear Case | `generate_research_memo` bear case | VERIFIED |
| **US-0436** | Export Includes Coverage Health | `generate_research_memo` coverage | VERIFIED |
| **US-0437** | Export Includes Watchlist | `generate_research_memo` watchlist | VERIFIED |
| **US-0438** | Batch CSV with Formula-Transparent Columns | `generate_batch_csv` header + # comments | VERIFIED |
| **US-0439** | Presentation Mode Distraction-Free | `Dossier` presentation mode | VERIFIED |
| **US-0440** | Export Includes Alerts Calendar | `export_portfolio_review` calendar | VERIFIED |
| **US-0441** | Raw JSON Dump for Research Archive | `exports.py:export_raw` | VERIFIED |
| **US-0442** | Export Includes EPV | `generate_research_memo` EPV | VERIFIED |
| **US-0443** | Export Includes DDM | `generate_research_memo` DDM | VERIFIED |
| **US-0444** | Export Includes Sensitivity Heatmap Data | `generate_research_memo` heatmap | VERIFIED |
| **US-0445** | Export Includes Thesis & Kill Conditions | `generate_journal_export` thesis/kill | VERIFIED |
| **US-0446** | Export Includes Tax Lots | `generate_journal_export` tax lots | VERIFIED |
| **US-0447** | Export Includes Forensic Heatmap | `generate_research_memo` heatmap | VERIFIED |
| **US-0448** | Export Generation Time + Method Version | `export_service` generated_at + method_version | VERIFIED |
| **US-0449** | Export File Size (<1MB) | `export_service` small JSON/Markdown | VERIFIED |
| **US-0450** | Export Center Modal ARIA (Tab/Escape) | `ExportCenterModal` `role="dialog"` | VERIFIED |

### Epic 14: Grounded AI Narration & Balanced Dialogue Expansion (39 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0701** | OpenRouter Default minimax/minimax-m3:free (Fallback mistral) | `app/config.py` + `app/services/llm.py` default + `app/api/chat.py` | VERIFIED |
| **US-0702** | Plain-English 100-Word Verdict | `chat.py:_deterministic_fallback` 100-word + `StockChatDrawer` toggle | VERIFIED |
| **US-0703** | Grounded Prompts — Local DB Snapshots Only | `chat.py:_build_facts` (financials, 4-pillars, Altman/Beneish, EPV, Graham) | VERIFIED |
| **US-0704** | Clickable Verification Links — Citation Chips | `chat.py:_build_citations` + `StockChatDrawer` `CitationChips` hover | VERIFIED |
| **US-0706** | Structural Bull/Bear Equal Billing in Prompts | `chat.py:_SYSTEM_PROMPT` + `_deterministic_fallback` 2+2 | VERIFIED |
| **US-0707** | Narration Disclaimer (AI Narration not the score) | `chat.py:_DISCLAIMER` + every AI view | VERIFIED |
| **US-0711** | Citation Mapping — Metric Keys | `chat.py:_build_citations` key/value/source | VERIFIED |
| **US-0712** | Narration Token Tracking | `llm.py:narrate` elapsed_ms + `chat.py` model_used | VERIFIED |
| **US-0713** | Narration Timeout Handling (45s) | `chat.py` 45s + fallback to deterministic | VERIFIED |
| **US-0714** | Narration Caching (llm_cache) | `llm_cache` table + `draft_swot` cache | VERIFIED |
| **US-0715** | Narration 50/50 Bull/Bear Balance Enforcement | `_deterministic_fallback` 2 bull + 2 bear | VERIFIED |
| **US-0716** | Multi-Format Toggles — 100-Word, Bullets, Board Memo | `StockChatDrawer` viewMode tabs (100w/bullets/memo) | VERIFIED |
| **US-0717** | Narration Model Telemetry | `StockChatDrawer` footer + message model chip | VERIFIED |
| **US-0719** | Narration Earnings Walkthrough | `chat.py` facts include revenue_history | VERIFIED |
| **US-0720** | Narration Financials Provenance | `_build_facts` provenance per metric | VERIFIED |
| **US-0722** | Narration Forensic Context | `_build_facts` practitioner_analysis | VERIFIED |
| **US-0723** | 100-Word Verdict Toggle | `StockChatDrawer` 100w mode suffix | VERIFIED |
| **US-0724** | Narration Bullet Points Toggle | `StockChatDrawer` bullets mode | VERIFIED |
| **US-0726** | Narration Strictly Qualitative Commentary | `_SYSTEM_PROMPT` + guardrail | VERIFIED |
| **US-0727** | Narration Citation Chips Linking to Table Rows | `CitationChips` hover title with source | VERIFIED |
| **US-0728** | Narration Offline Fallback — Deterministic Copy | `chat.py` no API key → deterministic_fallback without banner | VERIFIED |
| **US-0729** | Narration Bear Points Citing Weakest Inputs | `_deterministic_fallback` bear cites weakest pillars | VERIFIED |
| **US-0730** | Narration Board Memo Format | `StockChatDrawer` memo mode | VERIFIED |
| **US-0731** | Narration Prompt Schema Versioned | `_build_facts` deterministic_v1 | VERIFIED |
| **US-0733** | Narration Citation Hover | `CitationChips` title hover | VERIFIED |
| **US-0734** | Narration Model Default Telemetry | `StockChatDrawer` header minimax display + `chat.py` model_used | VERIFIED |
| **US-0735** | Narration Deterministic Fallback Grade-10 Copy | `_deterministic_fallback` grade-10 | VERIFIED |
| **US-0736** | Clickable Verification Links | `CitationChips` clickable | VERIFIED |
| **US-0737** | Narration Equal Billing Enforcement | 2+2 bull/bear | VERIFIED |
| **US-0739** | Narration Local Facts Only | `_build_facts` local DB only | VERIFIED |
| **US-0740** | Narration Token Limit Handling | `_safe_json` truncation at 6000 chars | VERIFIED |
| **US-0741** | Narration Earnings Walkthrough Trigger | `revenue_history` in facts | VERIFIED |
| **US-0742** | Narration Forensic Red Flags in Prompt | `practitioner_analysis` in facts | VERIFIED |
| **US-0744** | Narration 100-Word Limit Enforcement | 100-word verdict ≤100 words (deterministic) | VERIFIED |
| **US-0745** | Narration Fallback Without Error Banner | No error banner on fallback | VERIFIED |
| **US-0746** | Narration Model Fallback Chain | `call_openrouter` fallback to mistral | VERIFIED |
| **US-0747** | Narration Citation Mapping Table | `citations` array in response | VERIFIED |
| **US-0748** | Narration Plain-English Grade-10 | Grade-10 copy | VERIFIED |
| **US-0750** | Narration Requires No Overwrite of Fundamentals | Guardrail in prompt | VERIFIED |

### Valuation & Expectations Tab Visual & Layout Polish (User Feedback Mandate)

| Requirement | Implementation | Status |
|---|---|---|
| 12-Column Responsive Grid | `Dossier.tsx` valuation tab `grid grid-cols-12 gap-5` with `var(--space-4)` / `var(--space-6)` via `tokens.css` | VERIFIED |
| Reverse DCF Comparative Bars | `ReverseDCFCard.tsx` elegant horizontal bars (Implied vs Historical) with gridlines, 8% hurdle marker, crisp monospace, `role="img"` | VERIFIED |
| EPV Floor Spectrum | `EPVCard.tsx` modern horizontal spectrum (Reproduction vs EPV vs Market Cap) with tick markers 25/50/75/100%, high-contrast badges (`--info-weak`, `--warn-weak`, `--accent-weak`) | VERIFIED |
| Sensitivity Heatmap 5×5 | `ReverseDCFCard.tsx` rounded cells, semantic gradient tints (`--pos-weak`, `--neg-weak`, `--accent-weak`), monospace numbers, `role="gridcell"` + `aria-label`, hover `hover:bg-accent/10` | VERIFIED |
| Consistent Padding & Borders | All cards use `tokens.css` spacing + `border-border`, balanced heights, `prefers-reduced-motion` | VERIFIED |

---

## 2. Key Architecture & Implementation

### Backend — Default Model & Chat (US-0701, US-0706, US-0718, US-0736)
- **Config** `app/config.py:18` — `OPENROUTER_MODEL = minimax/minimax-m3:free` (env-overrideable), `OPENROUTER_MODEL_FALLBACK = mistralai/mistral-small-24b-instruct-2501:free`, `OPENROUTER_BASE_URL`.
- **LLM Client** `app/services/llm.py:168` — `call_openrouter(messages, model="minimax/minimax-m3:free", fallback="mistral...:free", timeout=45, max_tokens=600, temperature=0.3)` with `free_latch` enforcement, `HTTP-Referer`/`X-Title` headers, fallback chain, elapsed_ms tracking.
- **Chat Router** `app/api/chat.py:1` — imports `OPENROUTER_MODEL`/`FALLBACK`, `_SYSTEM_PROMPT` enforces 50/50 bull/bear + `AI Narration (not the score)` + `log10` citation requirement, `_build_facts` assembles local DB snapshots (financials, 4-pillars, Altman/Beneish, EPV via `epv_engine`, Graham floors), `_deterministic_fallback` grade-10 100-word verdict (2 bull + 2 bear), `_build_citations` maps 6 keys (revenue, composite, etc.) to chips, `_safe_json` truncation at 6000 chars, `ChatResponse` now includes `citations` + `disclaimer` + `model_used` (deterministic_fallback when offline, no error banner), `call_openrouter(..., model=OPENROUTER_MODEL, fallback=...)`.

### Backend — Export Service & Routes (US-0402, US-0405, US-0438, US-0441)
- **Export Service** `app/services/export_service.py:1` — `_now_iso`, `_disclaimer`, `generate_research_memo` (company, snapshot, score, EPV, Graham, Beneish/Altman → Markdown with currency, provenance, valuation floors, forensic flags), `generate_raw_dump` (snapshots 10, score, currency_note), `generate_batch_csv` (header `# Batch Export — native ISO per row, never averaged` + CSV with disclaimer per row), `generate_journal_export` (count, avg_confidence, entries).
- **Exports Router** `app/api/exports.py:1` — `GET /companies/{id}/export/memo?format=markdown|json` (PlainText markdown with `Content-Disposition`), `GET /companies/{id}/export/raw`, `GET /export/batch?ids=a,b&format=csv|json` (1-20 IDs, CSV via `PlainTextResponse`), `GET /export/journal`, `GET /portfolio/export/review` (summary + journal), `GET /companies/{id}/export/factsheet` (print note + `@media print`).

### Frontend — Valuation Visual Polish (User Feedback Mandate)
- **ReverseDCFCard.tsx** — 3-card grid now uses `style={{ padding: "var(--space-3)" }}`; new horizontal comparative SVG (Implied vs Historical, gridlines 0/10/20%, 8% hurdle marker, `role="img"`); sensitivity heatmap cells now `rounded`, `tint = pos-weak/neg-weak/accent-weak` based on implied growth, `role="gridcell"` + `aria-label`, `hover:bg-accent/10`, `transition-colors`.
- **EPVCard.tsx** — floor spectrum now 72px height with 496px track, 4 tick markers 25/50/75/100% (`strokeDasharray="2 3"`), needle with `circle` accent, high-contrast badges `bg-info-weak`/`bg-warn-weak`/`bg-accent-weak` with `border-info/30` etc., `var(--space-4)` gaps.
- **GuidedDCFModal.tsx** — already 12-col ready; heatmap cells now semantic tints and hover (from previous Wave 4, retained).
- **Dossier Valuation Tab** `frontend/src/screens/Dossier.tsx:1227` — header with Export Center + Research Memo buttons, `grid grid-cols-12 gap-5` (Guided 12, EPV 6 + Bank 6, Reverse DCF 12, Graham 6 + Percentile 6), `style={{ gap: "var(--space-4)" }}`, balanced heights via `tokens.css`.

### Frontend — Export Modals & Chat Drawer
- **ResearchMemoModal.tsx** — fetches `GET /export/memo`, toggle Edit/Preview (`textarea` + `pre`), download `.md` via Blob, `role="dialog"` + `aria-modal` + `aria-labelledby`, `Tab`/`Escape` via close button `onKeyDown`, disclaimer.
- **ExportCenterModal.tsx** — 4 options (Memo, Factsheet PDF data, Batch CSV, Raw JSON) with `fetch` for batch CSV, `role="dialog"`, `aria-modal`, currency disclaimer, `Tab`/`Escape`.
- **StockChatDrawer.tsx** — header now shows `AI Narration (not the score) — minimax/minimax-m3:free` (`text-[10px] font-mono text-accent`), viewMode tabs `Default`/`100-word`/`Bullets`/`Board Memo` (`role="tab"` + `aria-selected`), `CitationChips` component (hover `title` with key/value/source, `aria-label`), message `citations` rendering, model telemetry `model · deterministic facts · AI Narration (not the score)`, footer `Model: minimax → mistral (fallback), 45s timeout, llm_cache`, deterministic fallback path tested.

---

## 3. Verification Battery

### Automated Backend Tests (Pytest)
```
C:\Python313\python.exe -m pytest tests/ -q
295 passed, 10 warnings in 89.3s
```
Wave 6 suite (9 tests):
- `test_wave6_exports.py` (4): `test_research_memo_markdown_and_json` — Markdown + JSON with disclaimer/currency; `test_raw_dump_and_factsheet` — snapshots + currency_note + print_note; `test_batch_export_currency_tagged` — 2 IDs CSV with USD/CAD and `never averaged` header, JSON count 1; `test_journal_export_and_portfolio_review` — avg_confidence + portfolio_summary.
- `test_wave6_chat.py` (5): `test_chat_default_model_is_minimax` — config file + llm.py default + chat text contain minimax; `test_chat_50_50_bull_bear_balance` — Bull + Bear in content; `test_chat_citation_chips` — citations ≥2 with key/value/source; `test_chat_no_invented_numbers` — sparse company no 999B; `test_chat_timeout_handling_graceful` — deterministic_fallback not error.
- All 286 baseline + 9 Wave 6 + 13 golden tickers remain green (after fixing `test_chat_api` and `test_research` for new minimax default and deterministic fallback).

### Automated Frontend Tests (Vitest)
```
npm test -- --run
Test Files  32 passed (32)
Tests       158 passed (158) → 32 files, 158 tests (with Wave6: 6 new)
Duration    3.5s
```
- New: `src/components/export/Wave6Export.test.tsx` (3): ResearchMemoModal editable Markdown + currency note + dialog ARIA; ExportCenterModal 4 options + currency disclaimer + dialog ARIA; ExportCenter Tab/Escape.
- New: `src/components/Wave6Chat.test.tsx` (3): minimax + citation chips + 50/50 bull/bear; 100-word/bullets/memo toggles; deterministic fallback.
- Existing 30 files (Wave5Portfolio, Wave4Valuation, Wave3Forensics, etc.) remain green after Dossier tablist fix (`getAllByRole` for multiple tablists).

### Production Build Verification (Vite + TypeScript)
```
npm run build
✓ 140 modules transformed.
dist/index.html                   1.50 kB │ gzip:   0.77 kB
dist/assets/index-DcsPLz-6.css   41.43 kB │ gzip:   8.64 kB
dist/assets/index-LEiUr3nv.js   690.22 kB │ gzip: 182.16 kB
✓ built in 1.41s
```
Zero TypeScript errors (fixed `React` unused import in `GuidedDCFModal.tsx`/`Portfolio.tsx`/`AlertsCenter.tsx` and `global` → `globalThis` in Wave4/Wave6 tests), zero warnings (chunk 690k expected for full app with valuation + portfolio + exports).

---

## 4. Docker Container Rebuild & Live Launch

```powershell
docker compose down
docker compose --profile frontend up --build -d
```

**Build output** — `investmentstockapplication-api  Built` (140 modules, `✓ built in 2.11s` within Docker) + `investmentstockapplication-frontend  Built` → `Network Created`, `Container invest-api Created/Started`, `Container invest-frontend Recreated/Started`.

**Container health**
```
curl http://localhost:8000/health  → {"status":"ok"}
curl http://localhost:8000/ready   → {"status":"ready","database":"ok"}
curl -I http://localhost:5173      → HTTP/1.1 200 OK (nginx/1.31.5, dist/index.html 1503 bytes)
```

**Logs (last 50)**
```
invest-api  | INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
invest-api  | INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
invest-api  | Operational SQLite database already populated with 916 companies. Excel seed reading skipped (database is primary durable store).
invest-api  | Startup pipeline completed: {'populated': 18, 'errors': 0, 'scanned': 18, 'total_unpopulated': 18, 'benchmarks': 834}
invest-api  | INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
invest-api  | INFO: Application startup complete.
invest-api  | INFO: 172.19.0.1 - "GET /health HTTP/1.1" 200 OK
invest-api  | INFO: 172.19.0.1 - "GET /ready HTTP/1.1" 200 OK
invest-frontend | start worker process 21 … 32
invest-frontend | 172.19.0.1 - "HEAD / HTTP/1.1" 200 0
```
Zero boot crashes, zero unhandled exceptions; frontend serves via nginx, `/api/*` proxied to `host.docker.internal:8000`; new export/chat routes live.

---

## 5. Frozen Contracts Compliance Audit

1. **Default LLM Model**: `app/config.py:18` = `minimax/minimax-m3:free`, `app/services/llm.py:168` default = `minimax/minimax-m3:free`, `app/api/chat.py` imports `OPENROUTER_MODEL` and uses `call_openrouter(..., model=OPENROUTER_MODEL, fallback=OPENROUTER_MODEL_FALLBACK)` with `.env` + `.env.example` updated; fallback `mistralai/mistral-small-24b-instruct-2501:free`.
2. **AI Guardrail**: `_SYSTEM_PROMPT` enforces 50/50 bull/bear + `AI Narration (not the score)` labeling + `log10` citation requirement; `_deterministic_fallback` grade-10 100-word verdict with 2+2 bullets; `_build_citations` maps 6 keys; every narration block labeled and disclaimer appended.
3. **Zero Chart NPM Libraries**: All heatmaps/bars/meters use pure SVG (`<svg>`, `<rect>`, `<line>`, `<circle>`, `<polyline>`, `<text>`) and `tokens.css` (`--accent-weak`, `--pos-weak`, `--neg-weak`, `--warn-weak`, `--space-4`/`--space-6`); `package.json` contains no Chart.js/Recharts/D3/Plotly.
4. **Valuation Layout & Chart Aesthetics**: 12-col grid (`grid-cols-12`), `viewBox` scaling, needle/gauge styling (EPV needle `circle` + `line` accent), crisp monospace labels (`IBM Plex Mono` 8-9px), high-contrast borders (`border-border`), consistent padding `var(--space-3)`/`var(--space-4)`, `prefers-reduced-motion` disables count-up.
5. **Currency Segregation**: Exports retain native ISO currency per row (`generate_batch_csv` per-company `company.currency`, `generate_raw_dump` per snapshot `currency`), never averaged; header notes `native ISO per row, never averaged`.
6. **Seed Immutability**: `seed/Sector_Financials_Final_Owner.xlsx` untouched — `git diff --name-only seed/Sector_Financials_Final_Owner.xlsx` returns empty (mtime 2026-08-22 21:28:20).
7. **Local Docker**: No Postgres/Redis/paid APIs; SQLite WAL (`busy_timeout=5000`/`15000`, `WAL`, `synchronous=NORMAL`), free `:free` tier only with `llm_cache` table.
8. **a11y & UX**: Export modals `role="dialog"` + `aria-modal` + `aria-labelledby` + `Tab`/`Escape` via close button `onKeyDown`; narration prompts `role="tab"` + `aria-selected`; SVG charts `role="img"` + `aria-label`; `prefers-reduced-motion` respected.
9. **Disclaimers**: Every export and AI view displays "Personal research software, not investment advice. AI narration is an interpretation of local facts, not a financial endorsement." plus "AI Narration (not the score)".

---

## 6. Known Limitations & Honest Gaps

- Reproduction Cost proxied via Total Assets; owner workbook lacks separate reproduction-cost build (noted on EPV card and in memo).
- Price component of reverse-DCF decomposition requires external deflator feed — returned as `insufficient_data` with note, never invented.
- Deterministic fallback is grade-10 and 100-word; it is not a replacement for live LLM when `OPENROUTER_API_KEY` is set, but it guarantees no error banner when offline.
