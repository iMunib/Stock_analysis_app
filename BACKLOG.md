# BACKLOG.md — future stories (do not implement yet)

- **Watchlist / portfolio**: persist a list of company IDs to localStorage, show a
  desk-level watchlist table with composite + signal + one-day change at a glance.
- **LLM research summaries**: one-shot LLM narrative per dossier (OpenRouter),
  cached, with a prominent disclaimer "written by a model, not investment advice".
  Never lets the model overwrite fundamentals.
- **Full 720 history backfill**: POST /api/v1/jobs/backfill mode=all (rate-limited,
  async via Phase 6A worker). UI shows progress bar. ~500 remaining names get
  history; growth-NULL count drops from 713 to near zero.
- **Telemetry / usage stats**: anonymous local counts (page loads, search queries,
  dossier opens) written to a sqlite table; a simple telemetry dashboard at /telemetry.
- **Halal data enrichment**: interest-income field from SEC/Yahoo for the impure-income
  ratio. Currently always unknown, so `halal_candidate` is unreachable. Adding this
  field would make the halal flag actionable.
- **Sector-level detail pages for GICS sub-industries**: drill below the existing
  custom-industry / GICS-sector level to the sub-industry granularity already in the
  seed (GICS_Industry column).
- **Export CSV**: download CSV for a sector, the desk top-10, or a compare table.
- **Performance**: add a materialized view or precomputed score-summary table so
  the sector snapshot endpoint doesn't call `load_universe` every time.
- **Dark/light toggle**: optional light mode (CSS custom properties).