# Investment Stock Application — Phase 1

Personal, local equity-research research tool for a single user. **This is personal
research software, not investment advice.** It is not a product, not a broker, and
every API/UI surface says so.

## What Phase 1 is

- Import the frozen owner workbook (`seed/Sector_Financials_Final_Owner.xlsx`,
  720 companies: S&P 500 + S&P/TSX Composite) into SQLite.
- Serve a read-only FastAPI over the imported data.
- No live fetching, no scoring, no LLM, no full UI. Those are later phases.

Phase map:

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Workbook import + read-only API + docs | done |
| 2 | History + on-demand ingest (SEC EDGAR + Yahoo, cache in SQLite) | done |
| 3 | Scoring 0–10 + research signal + halal flag per `docs/SCORING_SPEC.md` | not started |

## Run with Docker (Windows PowerShell)

```powershell
cd "C:\Users\RehmanPC\Downloads\Investment Stock Application"
docker compose up --build -d
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/stats
```

- API: http://localhost:8000 (docs at http://localhost:8000/docs)
- The container runs migrations, then the importer, then uvicorn. The importer is
  idempotent: it skips re-import unless the workbook changed (`--force` forces).
- SQLite lives in `./data/app.db` on the host (mounted volume).
- The seed workbook is mounted read-only at `/seed`; nothing under `seed/` is ever
  modified and `refresh.py` is never executed (copies live in `legacy/` for
  reference only).

Optional frontend placeholder (profile `frontend`):

```powershell
docker compose --profile frontend up --build -d
# then open http://localhost:5173
```

Stop:

```powershell
docker compose down
```

## Run tests (host, PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
```

Tests import the real seed workbook; if it is missing they fail honestly rather
than faking coverage.

## Hard rules (see AGENTS.md)

- Company_ID format: `US:TICKER:US` or `CA:TICKER:TSX` (dots kept, e.g. `CA:BN:TSX`).
- Never mix CAD and USD money; cross-border comparison uses unitless ratios only.
- Never invent numbers: missing data is stored as NULL plus a quality flag.
- Banks/insurers keep their intentional blanks (Total_Debt, Gross_Profit, FCF_Calc...).
- Halal is a flag (AAOIFI-style), never a filter. LLM outputs never overwrite fundamentals.
- Secrets only in `.env` (gitignored). No paid APIs in v1.
"# Stock_analysis_app" 
