# Wave 6 Epic Specification: Grounded Voice, Export Suite & Valuation Visual Polish

> **Phase 1 Wave 6 Specification**
> **Objective**: Deliver 87 user stories across Epics 13 (Institutional Export Suite, 48 stories) and 14 (Grounded AI Narration & Balanced Dialogue Expansion, 39 stories) plus a visual refactoring of the Valuation & Expectations tab. Grounded narration over local facts with minimax/minimax-m3:free default, cached, 50/50 bull/bear, citation chips, 100-word verdicts, deterministic fallback, export suite with research memo, PDF print, batch CSV/JSON, and polished pure-SVG valuation visuals (Reverse DCF, EPV, sensitivity heatmap) using tokens.css.

---

## Epic 13: Institutional Export Suite (48 Stories)

### US-0266: Export Center Modal Entry Point
- **Given** a user on any dossier or portfolio view
- **When** clicking Export
- **Then** a modal lists available exports (memo, factsheet PDF, CSV, JSON, journal) with format and currency notes.

### US-0267: Export Format Selection
- **Given** the export center is open
- **When** selecting a format (Markdown, PDF, CSV, JSON)
- **Then** the corresponding generator is invoked and the download starts.

### US-0293: Export Currency Tagging
- **Given** any export containing money
- **When** generating the file
- **Then** each row retains native ISO currency code and disclaimer never averages across currencies.

### US-0300: Portfolio Holdings CSV Export
- **Given** a portfolio with holdings
- **When** exporting holdings
- **Then** a CSV with currency-tagged market value and disclaimers is produced.

### US-0402: Full Research Memo Draft (Markdown)
- **Given** a company with metrics, valuation floors, and forensic flags
- **When** generating a research memo
- **Then** a structured Markdown memo is filled with current metrics and provenance.

### US-0403: Dossier PDF & Clean Print Export
- **Given** a dossier view
- **When** printing or exporting PDF
- **Then** CSS @media print guarantees no clipped tables, clean page breaks, and provenance headers.

### US-0405: Batch Export Engine
- **Given** a list of 2–8 company IDs
- **When** requesting batch export
- **Then** a multi-company packet (CSV + JSON) is generated.

### US-0406: Research Memo Editable Workspace
- **Given** a generated memo
- **When** editing the memo
- **Then** the workspace allows Markdown editing and re-export.

### US-0407: Memo Provenance Section
- **Given** a research memo
- **When** viewing the memo
- **Then** a provenance section lists source, as-of date, and currency per metric.

### US-0408: Annual Decision Journal & Portfolio Review Doc
- **Given** journal entries for the year
- **When** generating the annual review doc
- **Then** a 1-click audit with confidence calibration statistics is produced.

### US-0409: Export Includes Valuation Floors
- **Given** a memo for a company
- **When** generating
- **Then** valuation floors (EPV, Graham) are included.

### US-0410: Export Includes Forensic Flags
- **Given** a company with forensic flags
- **When** generating memo
- **Then** flags are listed with thresholds.

### US-0411: Export Disclaimer
- **Given** any export
- **When** viewing the export
- **Then** disclaimer Personal research software, not investment advice is displayed.

### US-0412: Decision Journal Audit in Export
- **Given** annual journal entries
- **When** exporting the review doc
- **Then** calibration stats are included.

### US-0413: Batch Comparison Packet
- **Given** a comparison of 2–8 companies
- **When** exporting batch
- **Then** a comparison packet with metrics is generated.

### US-0414: Screen CSV Formula-Transparent Export
- **Given** a screen result
- **When** exporting CSV
- **Then** column definitions with formulas are included.

### US-0416: Export File Naming
- **Given** any export
- **When** downloading
- **Then** the filename contains company ticker, date, and format.

### US-0417: Export Currency Isolation Note
- **Given** an export with CAD and USD rows
- **When** viewing the file
- **Then** a note states CAD and USD are segregated.

### US-0418: Raw JSON Dump
- **Given** a company
- **When** requesting raw JSON dump
- **Then** a JSON with dossier, scores, and provenance is returned.

### US-0419: JSON Dump Currency Tagging
- **Given** a JSON dump
- **When** viewing
- **Then** each money field has currency tag.

### US-0420: Export Includes Sector Medians
- **Given** a company with sector medians
- **When** generating memo
- **Then** sector medians are included.

### US-0421: Export Includes Peer Comparison
- **Given** a company with peers
- **When** generating memo
- **Then** peer metrics are included.

### US-0422: Export Includes Dividend Schedule
- **Given** a portfolio
- **When** exporting review doc
- **Then** dividend schedule is included.

### US-0423: Export Includes Holdings Summary
- **Given** a portfolio
- **When** exporting
- **Then** holdings summary is included.

### US-0425: Export Center Keyboard Navigation
- **Given** the export modal
- **When** pressing Tab and Escape
- **Then** focus is trapped and Escape closes the modal.

### US-0426: Export SVG Charts as Data
- **Given** a memo with charts
- **When** viewing the memo
- **Then** chart data is included as tables, not images.

### US-0427: Export Includes Risk Metrics
- **Given** a company with risk metrics
- **When** generating memo
- **Then** risk metrics are included.

### US-0428: Research Memo Draft Editable
- **Given** a draft memo
- **When** editing
- **Then** the draft is editable and re-exportable.

### US-0429: Export Includes Valuation Sensitivity
- **Given** a valuation with sensitivity matrix
- **When** generating memo
- **Then** sensitivity heatmap data is included.

### US-0431: Presentation Mode High-Contrast
- **Given** a company review
- **When** toggling presentation mode
- **Then** a distraction-free high-contrast view is shown.

### US-0433: Export Includes Halal Flag
- **Given** a company with halal flag
- **When** generating memo
- **Then** halal status is included.

### US-0434: Export Includes Pillar Drilldown
- **Given** a dossier with pillar drilldown
- **When** generating memo
- **Then** pillar formulas are included.

### US-0435: Export Includes Bear Case
- **Given** a company with bear case
- **When** generating memo
- **Then** bear case bullets are included.

### US-0436: Export Includes Coverage Health
- **Given** a universe health matrix
- **When** exporting
- **Then** coverage health is included.

### US-0437: Export Includes Watchlist
- **Given** a watchlist
- **When** exporting
- **Then** watchlist holdings are included.

### US-0438: Batch CSV with Formula-Transparent Columns
- **Given** a batch export
- **When** viewing CSV
- **Then** columns have formula definitions.

### US-0439: Presentation Mode Distraction-Free
- **Given** presentation mode is active
- **When** viewing
- **Then** nav and sidebars are hidden.

### US-0440: Export Includes Alerts Calendar
- **Given** a calendar with events
- **When** exporting
- **Then** calendar events are included.

### US-0441: Raw JSON Dump for Research Archive
- **Given** a company
- **When** requesting raw dump
- **Then** a JSON archive is returned.

### US-0442: Export Includes EPV
- **Given** a valuation with EPV
- **When** generating memo
- **Then** EPV and reproduction cost are included.

### US-0443: Export Includes DDM
- **Given** a bank with DDM
- **When** generating memo
- **Then** DDM fair value is included.

### US-0444: Export Includes Sensitivity Heatmap Data
- **Given** a valuation
- **When** exporting
- **Then** heatmap data is included.

### US-0445: Export Includes Thesis & Kill Conditions
- **Given** a journal entry
- **When** exporting review doc
- **Then** thesis and kill conditions are included.

### US-0446: Export Includes Tax Lots
- **Given** portfolio with tax lots
- **When** exporting
- **Then** tax lot details are included.

### US-0447: Export Includes Forensic Heatmap
- **Given** a portfolio heatmap
- **When** exporting
- **Then** heatmap is included.

### US-0448: Export Generation Time
- **Given** any export
- **When** generating
- **Then** generation timestamp and method_version are included.

### US-0449: Export File Size
- **Given** an export
- **When** viewing
- **Then** file size is reasonable (<1MB).

### US-0450: Export Center Modal ARIA
- **Given** the export modal
- **When** opening
- **Then** it has role dialog, aria-modal, and aria-labelledby.

---

## Epic 14: Grounded AI Narration & Balanced Dialogue Expansion (39 Stories)

### US-0701: OpenRouter Engine Default minimax/minimax-m3:free
- **Given** the backend config and chat router
- **When** an AI narration is requested
- **Then** the default model is minimax/minimax-m3:free with fallback mistralai/mistral-small-24b-instruct-2501:free, 45s timeout, token tracking.

### US-0702: Plain-English 100-Word Verdict
- **Given** a company with scores and forensics
- **When** requesting a 100-word verdict
- **Then** a concise 100-word executive summary is returned, labeled AI Narration (not the score).

### US-0703: Grounded Prompts — Local DB Snapshots Only
- **Given** a company
- **When** building the system prompt
- **Then** only local DB snapshots (financials, 4-pillars, Altman/Beneish, EPV, Graham floors) are assembled; no external facts.

### US-0704: Clickable Verification Links — Citation Chips
- **Given** a narration with assertions
- **When** viewing the narration
- **Then** each assertion has a hoverable citation chip linking to the exact metric row.

### US-0706: Structural Bull/Bear Equal Billing in Prompts
- **Given** the system prompt
- **When** generating narration
- **Then** the prompt enforces 50/50 bull/bear balance with equal-length sections.

### US-0707: Narration Disclaimer
- **Given** any AI narration view
- **When** viewing
- **Then** disclaimer AI Narration (not the score) and Personal research software, not investment advice are displayed.

### US-0711: Citation Mapping — Metric Keys
- **Given** a narration claim
- **When** hovering the citation chip
- **Then** the chip shows metric key, value, and source table.

### US-0712: Narration Token Tracking
- **Given** an AI request
- **When** the request completes
- **Then** token count and model used are tracked.

### US-0713: Narration Timeout Handling (45s)
- **Given** an AI request
- **When** the model times out after 45s
- **Then** a graceful fallback to local deterministic copy is returned.

### US-0714: Narration Caching (llm_cache)
- **Given** an AI request for the same company and facts version
- **When** requesting again
- **Then** the cached narration is returned without re-calling OpenRouter.

### US-0715: Narration 50/50 Bull/Bear Balance Enforcement
- **Given** a generated narration
- **When** viewing
- **Then** bull and bear points are equal in length and count.

### US-0716: Multi-Format Toggles — 100-Word, Bullets, Board Memo
- **Given** a narration
- **When** toggling format
- **Then** the narration re-renders as 100-word, bullet points, or formal board memo.

### US-0717: Narration Model Telemetry
- **Given** a narration response
- **When** viewing telemetry
- **Then** model name, fallback status, and token count are shown.

### US-0719: Narration Earnings Walkthrough
- **Given** a company with earnings history
- **When** requesting an earnings walkthrough
- **Then** a step-by-step earnings narrative is returned.

### US-0720: Narration Financials Provenance
- **Given** a narration
- **When** viewing citations
- **Then** each financial value shows provenance (source, as-of).

### US-0722: Narration Forensic Context
- **Given** a company with forensic flags
- **When** generating narration
- **Then** forensic context is included in the prompt.

### US-0723: 100-Word Verdict Toggle
- **Given** a narration
- **When** toggling to 100-word mode
- **Then** the verdict is truncated to 100 words.

### US-0724: Narration Bullet Points Toggle
- **Given** a narration
- **When** toggling to bullets
- **Then** the narration is shown as bullet points.

### US-0726: Narration Strictly Qualitative Commentary
- **Given** the AI guardrail
- **When** generating narration
- **Then** the AI cannot modify, invent, or overwrite fundamental figures.

### US-0727: Narration Citation Chips Linking to Table Rows
- **Given** a narration assertion
- **When** clicking the citation chip
- **Then** the view scrolls to the exact metric row.

### US-0728: Narration Offline Fallback — Deterministic Copy
- **Given** OpenRouter is offline or unconfigured
- **When** requesting narration
- **Then** a local deterministic grade-10 copy template is returned without error banner.

### US-0729: Narration Bear Points Citing Weakest Inputs
- **Given** a narration
- **When** viewing bear points
- **Then** the weakest inputs and forensic red flags are cited.

### US-0730: Narration Board Memo Format
- **Given** a narration
- **When** toggling to board memo
- **Then** a formal memo format is shown.

### US-0731: Narration Prompt Schema
- **Given** the prompt builder
- **When** building the prompt
- **Then** the schema is versioned and deterministic.

### US-0733: Narration Citation Hover
- **Given** a citation chip
- **When** hovering
- **Then** the chip shows metric details on hover.

### US-0734: Narration Model Default Telemetry
- **Given** the default model
- **When** viewing telemetry
- **Then** the default is shown as minimax/minimax-m3:free.

### US-0735: Narration Deterministic Fallback Grade-10 Copy
- **Given** offline mode
- **When** requesting narration
- **Then** the fallback copy is grade-10 and deterministic.

### US-0736: Clickable Verification Links
- **Given** a narration with citations
- **When** clicking a citation
- **Then** the link navigates to the metric.

### US-0737: Narration Equal Billing Enforcement
- **Given** a narration
- **When** viewing
- **Then** bull and bear sections are equal length.

### US-0739: Narration Local Facts Only
- **Given** the prompt
- **When** building
- **Then** only local DB facts are used.

### US-0740: Narration Token Limit Handling
- **Given** a long prompt
- **When** sending to OpenRouter
- **Then** the prompt is truncated gracefully to fit token limits.

### US-0741: Narration Earnings Walkthrough Trigger
- **Given** an earnings walkthrough request
- **When** handling
- **Then** the walkthrough is generated from earnings history.

### US-0742: Narration Forensic Red Flags in Prompt
- **Given** forensic flags
- **When** building prompt
- **Then** flags are included in the prompt.

### US-0744: Narration 100-Word Limit Enforcement
- **Given** a 100-word verdict
- **When** viewing
- **Then** the verdict is ≤100 words.

### US-0745: Narration Fallback Without Error Banner
- **Given** offline mode
- **When** requesting
- **Then** the fallback is seamless without error banner.

### US-0746: Narration Model Fallback Chain
- **Given** primary model failure
- **When** handling
- **Then** fallback to mistralai/mistral-small-24b-instruct-2501:free is attempted.

### US-0747: Narration Citation Mapping Table
- **Given** a narration
- **When** viewing citation map
- **Then** a table of claims to metric keys is shown.

### US-0748: Narration Plain-English
- **Given** a narration
- **When** viewing
- **Then** the language is plain-English grade-10.

### US-0750: Narration Requires No Overwrite of Fundamentals
- **Given** the AI guardrail
- **When** generating narration
- **Then** the AI cannot overwrite fundamentals.

---

## Valuation & Expectations Tab Visual & Layout Polish (User Feedback Mandate)

- **Given** the Valuation & Expectations tab with 4 cards (Guided DCF, EPV, Bank DDM/Residual, Reverse DCF)
- **When** viewing on desktop (≥1280px) and mobile (<900px)
- **Then** the layout uses a structured 12-column responsive grid (lg:grid-cols-12) with clear visual hierarchy, consistent margins (var(--space-4), var(--space-6)) via tokens.css, and balanced card heights.

- **Given** the pure-SVG charts in the tab (Reverse DCF Implied Growth vs Historical CAGR, EPV Range Meter, Sensitivity Heatmap 5×5)
- **When** viewing
- **Then** the charts have proper viewBox scaling, clean needle/gauge styling, crisp monospace coordinate labels, high-contrast borders, consistent padding via design tokens, and respect prefers-reduced-motion.

---

## Cross-Cutting Acceptance Notes

- Default LLM model minimax/minimax-m3:free is configured in app/config.py, app/api/chat.py, and fallback minimax/minimax-m3:free → mistralai/mistral-small-24b-instruct-2501:free.
- AI narration is strictly qualitative commentary over verified database facts; every block is labeled AI Narration (not the score) with 50/50 bull/bear balance.
- Zero chart npm libraries: pure SVG primitives and tokens.css only.
- Currency segregation: CAD/USD strictly segregated; exports retain native ISO codes per row.
- Seed immutability: git diff must be empty.
- Local Docker: no cloud, no Postgres, no paid APIs; free :free tier only with llm_cache.
- a11y: export menus, narration prompts, SVG charts have ARIA roles/labels and Tab/Escape.
- Disclaimers: Personal research software, not investment advice. AI narration is an interpretation of local facts, not a financial endorsement.
