# Wave 3 Epic Specification: The Uncontested Class — Forensic Red Flags & Statement Integrity

> **Phase 1 Wave 3 Specification**
> **Objective**: Deliver 42 user stories across Epics 8 (Forensic Red Flags Workspace, 42 stories) and 9 (As-Filed vs As-Restated Reporting, 38 stories subset) — institutional forensic depth with zero retail peer: consolidated Red Flags tab, Benford's Law screening, Schilit shenanigans engine, auditor/going-concern tracking, cross-model divergence, fraud learning gallery, portfolio severity ranker, restatement preservation, 10-year trajectories, and working-capital CCC analysis.
> **Frozen Contracts Maintained**: Locked composite weights (0.30/0.25/0.25/0.20) — forensics remain a separate lens, never blended into composite; CAD/USD never mixed (money carries native currency tag; cross-border ratios only); owner seed immutability; honest NULL + flag (no invented numbers); Company_ID `US:TICKER:US` | `CA:TICKER:TSX`; banks/insurers carve-out `financial_institution_excluded`; pure SVG+CSS (tokens.css) only; local Docker/SQLite WAL only; a11y (prefers-reduced-motion, ARIA, Tab/Escape); disclaimer on every forensic surface.

---

## Epic 8: Consolidated Forensic Red Flags Workspace & Shenanigans Engine (42 Stories)

### US-0018: Receivables vs Revenue Divergence (Channel Stuffing) Screener
- **Given** a forensic screener with receivables growth vs revenue growth
- **When** screening for receivables growing faster than revenue for 2 consecutive years
- **Then** the shenanigans engine flags `RED_FLAG_DSO_SURGE` when DSO or AR/revenue divergence exceeds +15% YoY vs prior period, with affected fiscal years listed.

### US-0027: Goodwill Bloat / Serial Overpayer Screen
- **Given** a balance sheet with goodwill and total assets
- **When** screening for goodwill > 40% of total assets in any FY
- **Then** the engine flags `GOODWILL_BLOAT` (goodwill/assets ≥ 0.40) and surfaces goodwill trend + impairment risk note; banks excluded remain `financial_institution_excluded` for debt models only, but goodwill check still runs.

### US-0045: Auditor Changes & Going-Concern Language Filter
- **Given** a company with filing provenance or quality flags indicating audit opinion
- **When** applying the "exclude auditor change / going-concern" filter or viewing the audit card
- **Then** the workspace shows auditor name/tenure/change flag and going-concern language presence with fiscal year and source provenance.

### US-0202: Hindenburg-Style First-Pass Checklist
- **Given** any company dossier
- **When** opening the Red Flags tab → First-Pass Checklist section
- **Then** a 5-item professional skepticism checklist renders (related-party, revenue recognition, auditor changes, Beneish flag, distress flag) with PASS/FAIL per item derived from live forensic signals.

### US-0209: Historical Fraud Learning Gallery — Model Calibration
- **Given** a user browsing the Learn → Forensic Gallery or Red Flags → Learn link
- **When** viewing the gallery entry for a documented collapse (Enron, WorldCom, etc.)
- **Then** the UI maps which flags (Beneish M > -1.78, Altman Distress, Sloan High Accruals, Schilit decoupling) would have triggered pre-collapse with threshold citations and date badges.

### US-0210: Auditor Name, Tenure & Opinion Notes per Year
- **Given** a company with multi-year filing history
- **When** expanding the Auditor Timeline card
- **Then** each FY row displays auditor name (or `Unknown` + `unknown_auditor` flag when missing), tenure length, change indicator vs prior FY, and opinion notes; `NULL` is rendered as explicit "—" with `unknown` reason.

### US-0211: Benford's Law First-Digit Test on Statement Figures
- **Given** a company with ≥ 15 positive statement figures across 10-year FY rows (revenue, assets, cash, etc.)
- **When** requesting `/api/v1/companies/{id}/forensics/benford`
- **Then** the service returns observed first-digit distribution (1–9) vs Benford expected `log10(1+1/d)` curve, χ² statistic, degrees of freedom = 8, and verdict (`conforms` | `deviation_noted` | `insufficient_data`); frontend renders it in a pure SVG BenfordChart with ARIA labels.

### US-0212: Insider Selling Cluster Flag (Behavioral)
- **Given** a forensic workspace
- **When** insider data is unavailable (local-only, no paid APIs)
- **Then** the service returns `data_available: false` + explanatory note `insider_data_requires_premium_feed` rather than inventing a flag; UI shows informational placeholder, not a FAIL.

### US-0213: Consolidated Red-Flag Count & Severity per Company
- **Given** any company with computed forensics
- **When** calling `GET /api/v1/companies/{id}/forensics/summary`
- **Then** the response aggregates all triggered flags (Beneish, Altman, Sloan, Schilit, goodwill, auditor) into a count, severity list (`critical` | `elevated` | `informational`), and a 0–100 forensic health score.

### US-0214: Forensic Due-Diligence Export (Structured)
- **Given** a company with forensics computed
- **When** requesting `GET /api/v1/companies/{id}/forensics/export`
- **Then** the API returns a JSON with every flag, value, threshold, and provenance URL suitable for board/family-office documentation; CSV alternative via `?format=csv`.

### US-0215: Related-Party Transaction Summary per Year
- **Given** filings are the sole truth source and no vendor enrichment exists locally
- **When** viewing the Related-Party card
- **Then** the service scans `data_quality_flags` for related-party codes and filing notes; if none, returns `data_available: false` with `related_party_disclosure_not_in_local_statements` note — never guessed.

### US-0216: DSO Trend + Channel-Stuffing Indicators
- **Given** a company with AR and revenue across ≥ 2 FY
- **When** computing shenanigans
- **Then** DSO = AR / Revenue × 365 is trended YoY; a surge > +15% divergence vs revenue growth triggers `RED_FLAG_DSO_SURGE` with affected FY listed.

### US-0217: Margin Anomaly vs Peer Median
- **Given** a company's gross/operating margin and its sector-currency peer median
- **When** margin diverges > 2× inter-quartile spread or > 15pp from median without disclosure
- **Then** the cross-model comparison notes `MARGIN_OUTLIER` with peer median value and company margin displayed — as an informational callout, not an accusation.

### US-0218: Going-Concern Language Immediate Flag
- **Given** filing text or quality flag contains `going_concern` code
- **When** forensics are summarized
- **Then** a `critical` severity flag `GOING_CONCERN_LANGUAGE` appears immediately with fiscal year and filing link (EDGAR/SEDAR+); absent data shows `not_detected` rather than `clear`.

### US-0220: Pension Underfunding Warning (Informational Placeholder)
- **Given** no pension liability line is stored in `financial_snapshots`
- **When** rendering the pension card
- **Then** the service returns `data_available: false` with `pension_fields_not_in_owner_workbook`; UI shows placeholder explaining the limitation.

### US-0221: Threshold-Crossing Explainer (Why Grey → Distress)
- **Given** a company whose Altman zone crossed from Grey to Distress year-over-year
- **When** expanding the Distress Detail drawer
- **Then** the response decomposes ΔX1–X5 contributions and highlights the variable with largest negative Δ as `primary_driver` with delta values.

### US-0222: Cross-Model Distress Comparison (Beneish vs Altman vs Sloan) with Divergence Callout
- **Given** a company with Beneish, Altman Z/Z'', and Sloan results
- **When** viewing the Cross-Model Comparison card
- **Then** the UI shows all three verdicts side-by-side and a divergence banner when models disagree (e.g., `Beneish=Clean but Sloan=High Accruals`) with short interpretation.

### US-0223: Annotate Forensic Flags with Notes & Evidence Links (Local)
- **Given** an investigator using the Red Flags workspace
- **When** adding a note to a flag
- **Then** the frontend persists it in `localStorage` key `forensic_notes:{company_id}` (max 2000 chars, client-only) and re-displays it; no backend write is required.

### US-0224: Re-Alert on Forensic Deterioration for Watched Names
- **Given** a watchlist containing the company
- **When** a new flag appears or severity escalates on recompute
- **Then** the watchlist digest includes a `forensic_escalation` alert with severity routing (mirrors Wave 2 digest channel model; local evaluation via `watchlist.ts` re-check on dossier load).

### US-0226: Pump-and-Dump Style Promotion Spike Placeholder
- **Given** no promotion/listing-change feed exists locally
- **When** viewing the Meme/Promotion card
- **Then** the service returns `data_available: false` with `promotion_feed_not_in_local_scope` — never a false PASS.

### US-0227: Fraud Learning Gallery Browsing (Second Entry)
- **Given** the gallery index
- **When** selecting any documented case
- **Then** the gallery detail shows case summary, year, flags that would have triggered, and explicit "screen, not proof — false-positive 15–20%" disclaimer.

### US-0228: Cash Conversion Cycle Trend with Forensic Interpretation
- **Given** AR, inventory, payables (proxied via `current_liabilities - total_debt` when `accounts_payable` absent) and revenue/COGS (approx via `revenue - gross_profit`) and `365` day factor
- **When** viewing the CCC card
- **Then** DSO/DIO/DPO and CCC = DSO + DIO − DPO are trended over available FY rows with YoY deltas and a short forensic note on cash reality.

### US-0229: Model Applicability Disclosure (US vs CAD)
- **Given** any forensic model result
- **When** rendering the model header
- **Then** a badge states applicability: `validated_globally` (Beneish/Sloan) vs `US_edgar_history_dependent` where FY depth matters; CAD names carry `SEDAR+ filing provenance` link.

### US-0230: Full Forensic Timeline Structured Export
- **Given** a company with ≥ 2 FY rows
- **When** requesting `GET /api/v1/companies/{id}/forensics/timeline`
- **Then** the response returns year-by-year Beneish M, Altman Z, Sloan ratio, DSO, inventory delta, and flags for each FY as an array.

### US-0231: User-Configurable Forensic Thresholds (Local)
- **Given** a paranoid-but-systematic user
- **When** adjusting thresholds in Settings (localStorage `forensic_thresholds`)
- **Then** the frontend re-evaluates flags client-side against the stored thresholds and shows `custom_threshold_active` badge; backend thresholds remain canonical.

### US-0232: Complexity Flag for Multi-Layer Holding Structures
- **Given** no holding-structure graph is stored
- **When** viewing the Complexity card
- **Then** service returns `data_available: false` with `holding_structure_not_in_local_statements`; UI shows explanatory placeholder.

### US-0233: Inventory Growth vs Sales Growth Divergence
- **Given** inventory and revenue across ≥ 2 FY
- **When** inventory growth exceeds revenue growth by > +15%
- **Then** `RED_FLAG_INVENTORY_BUILDUP` triggers with affected FY.

### US-0234: Capitalized Expenses / Cost Capitalization Shift Flag
- **Given** current assets, PP&E, and total assets across ≥ 2 FY
- **When** non-current non-PPE asset ratio expands > 25% YoY (AQI proxy)
- **Then** `RED_FLAG_CAPITALIZED_EXPENSES` triggers.

### US-0235: Debt-Covenant Pressure Indicators
- **Given** debt, interest, and coverage are available
- **When** net debt/EBITDA > 4.0 and interest coverage < 3.0 simultaneously
- **Then** an `COVENANT_PRESSURE` informational flag appears; otherwise `data_available` note when inputs missing.

### US-0236: Regulatory Investigations / Settlements Summary
- **Given** only local flags/filings are available
- **When** viewing the Regulatory card
- **Then** service scans quality flags for regulatory codes; if none, returns `data_available: false` with `regulatory_actions_not_in_local_statements`.

### US-0238: Zero Red Flags + High F-Score "Clean Compounders" Screener
- **Given** the screener engine
- **When** filtering `clean_compounders=true` (zero forensic flags + Piotroski-style health via `eqr >= 80` and Sloan `neutral`)
- **Then** only companies with no critical/elevated flags pass.

### US-0239: Plain-Language "What Could Go Wrong" Summary
- **Given** any company's triggered flags
- **When** rendering the Red Flags header
- **Then** a 1-sentence plain-language summary concatenates top 2 flag interpretations (e.g., "Cash lags earnings and inventory is building faster than sales.").

### US-0240: Forensic Due-Diligence Documentation per Holding (Family Office)
- **Given** the export endpoint
- **When** exporting
- **Then** the payload includes disclaimer, methodology version, and per-flag provenance suitable for governance archiving.

### US-0241: Earnings-Call Narrative vs Flag Trajectory Cross-Check
- **Given** premium transcript feed is not locally available
- **When** viewing the cross-check card
- **Then** service returns `data_available: false` with `transcript_feed_not_in_local_scope` and suggests manual comparison against flag timeline.

### US-0242: Delisted-Case Calibration (True-Positive Teaching)
- **Given** gallery or timeline
- **When** viewing a delisted/acquired case (synthetic example built from local seed anomalies)
- **Then** flags are shown historically with teaching note on calibration.

### US-0243: High-Yield Trap Check Before Chasing Yield
- **Given** a company with dividend yield > 6%
- **When** forensics are summarized
- **Then** a `YIELD_TRAP_REVIEW` banner advises checking Sloan, distress, and coverage before chasing yield.

### US-0244: Serial-Acquirer & Goodwill Accumulation Flag
- **Given** goodwill accumulation across FY (goodwill_tangible proxy via `total_assets - book_equity` trend or goodwill field when present)
- **When** goodwill rises > 20% YoY in ≥ 2 of last 3 FY
- **Then** `SERIAL_ACQUIRER_GOODWILL_BUILD` triggers.

### US-0245: Restatement History — Before/After Values (As-Filed vs As-Restated)
- **Given** a company with duplicate fiscal_year rows from different sources (seed vs provider) or corrected filings
- **When** requesting `GET /api/v1/companies/{id}/restatements`
- **Then** the response returns per-FY `as_filed` (owner-workbook immutable row or earliest fetched) and `as_restated` (latest provider row) with delta and `source` provenance; toggle UI preserves both.

### US-0246: Forensic Suite as University Teaching Tool
- **Given** any company
- **When** Learn → Forensics lesson is opened
- **Then** the lesson deep-links to live Red Flags tabs with real numbers and methodology citations.

### US-0247: Turnaround Verification via Falling Flags
- **Given** a turnaround screen (negative NI but positive FCF) and ≥ 3 FY of flag history
- **When** viewing the turnaround card
- **Then** the UI shows whether triggered flag count fell year-over-year alongside improving FCF, as verification.

### US-0249: Portfolio-Level Forensic Severity Ranker
- **Given** a list of 2–8 company IDs via `GET /api/v1/forensics/rank?ids=a,b,c`
- **When** requesting ranking
- **Then** the service returns companies ordered by forensic severity (critical → elevated → informational → clean), with per-company flag count and worst flag.

### US-0555: Short-Interest % Float & Days-to-Cover with Staleness
- **Given** no short-interest feed exists locally (requires exchange premium feed)
- **When** viewing the short-interest card
- **Then** service returns `data_available: false` with `short_interest_requires_premium_feed` and staleness note `twice_monthly_lag`; UI shows placeholder.

---

## Epic 9: As-Filed vs As-Restated Reporting & Statement Trajectory Deep-Dive (Wave 3 Subset — 5 Additional GWT)

### US-0152: Synchronized Multi-Year Trajectory Charts (Revenue/Margins/FCF)
- **Given** a company with ≥ 3 FY rows
- **When** viewing the Trajectory card (Red Flags → Statements or Financials tab)
- **Then** pure SVG synchronized charts show Revenue (bars scaled in native currency), Gross/Operating Margins (%), and FCF (native currency) across 10 years with inflection markers where YoY Δ > 15%.

### US-0156: Margin Trajectory with Inflection Markers
- **Given** ≥ 3 FY of gross and operating margins
- **When** margins inflection Δ > 5pp YoY
- **Then** markers appear on the margin chart with ARIA label and tooltip.

### US-0157: Working-Capital Days Plotted Over Time (DSO/DIO/DPO)
- **Given** AR, inventory, and payables proxy available
- **When** DSO/DIO/DPO are computable
- **Then** CCC = DSO + DIO − DPO and its components are plotted as a stacked/trended SVG with per-year values.

### US-0161: As-Originally-Reported vs As-Restated Toggle When Restatements Exist
- **Given** per-FY as_filed and as_restated values from `/restatements`
- **When** toggling the switch
- **Then** the history table swaps values and shows delta badges (Δ revenue, Δ net income) with source tags `seed` vs `provider`.

### US-0168: Goodwill vs Tangible Assets Trend with Impairment History
- **Given** goodwill or proxy (assets − equity) and total assets
- **When** goodwill/assets ≥ 0.40 or YoY jump > 20%
- **Then** a goodwill/tangible strip shows trend and an impairment risk banner.

### US-0158: Share Count History with Buybacks & Issuance Annotated
- **Given** shares_snapshot across FY rows and price history
- **When** share count falls YoY
- **Then** the card annotates "net buyback" vs "issuance" via YoY Δ and delta %; dilution tracker separates SBC dilution from organic buybacks where SBC field exists.

---

## Cross-Cutting Acceptance Notes

- Every forensic model card displays: formula, threshold, provenance link (SEC EDGAR or SEDAR+), `method_version`, and disclaimer: "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings."
- Financial institution carve-out: any debt-based model returns `{status: "financial_institution_excluded", financial_institution_excluded: true}` and UI shows informational chip, never a score.
- NULL honesty: insufficient-data model returns `{status: "insufficient_data", data_available: false}` and FAQ explains which inputs were missing; no fake CCC or goodwill is invented.
- Pure SVG: BenfordChart, trajectory charts, CCC chart, and goodwill strip use `<svg>`, `<line>`, `<rect>`, `<circle>`, `<polyline>`, `<path>` with `tokens.css` only.
- a11y: RedFlagsWorkspace tabs, BenfordChart, trajectory charts, and AsFiledToggle are keyboard navigable (Tab/Escape) and carry `role="img"`/`aria-label` where visual.
- Currency: all money values in trajectories and CCC carry native currency badge; never blended.
