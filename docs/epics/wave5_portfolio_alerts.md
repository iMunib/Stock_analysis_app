# Wave 5 Epic Specification: Portfolio, Holdings Tracking & Local Alerts Engine — Judgment Infrastructure

> **Phase 1 Wave 5 Specification**
> **Objective**: Deliver 93 user stories across Epics 6 (Local Alerts Engine, 44 stories), 11 (Local Portfolio Ledger, 44), and 12 (Decision Journaling, 5)

---

## Epic 11: Local Portfolio Ledger (44 Stories)

### US-0302: Portfolio Pillar Averages
- **Given** a portfolio with holdings that have composite scores
- **When** requesting portfolio summary
- **Then** weighted pillar averages are computed as sum(score×market_value)/sum(market_value)

### US-0303: Sector Concentration
- **Given** holdings with sector tags
- **When** viewing portfolio summary
- **Then** sector concentration is aggregated by market value with weight %

### US-0304: Account Segmentation
- **Given** a user creating an account of type TFSA, RRSP, FHSA, Taxable, or Paper
- **When** creating the account
- **Then** it appears in the account filter with correct currency isolation.

### US-0305: Dividend Income Trailing
- **Given** holdings with dividend history
- **When** requesting dividend schedule
- **Then** trailing 12M dividends are summed by currency.

### US-0306: Position Sizing Bands
- **Given** holdings with market values
- **When** viewing rebalance analysis
- **Then** each holding shows weight %, target %, drift %, and warning if drift >5pp.

### US-0307: Transaction Ledger — Buy
- **Given** an account and a company
- **When** posting a buy transaction
- **Then** holdings quantity and cost basis increase.

### US-0309: Forensic Heatmap
- **Given** holdings
- **When** requesting forensic heatmap
- **Then** each holding shows Beneish/Altman/Sloan severity sorted descending.

### US-0310: Max Position Warning
- **Given** a holding >25% weight
- **When** viewing rebalance
- **Then** warning max_position_exceeded_25pct is shown.

### US-0311: Capital Gain Type
- **Given** a buy lot and current price
- **When** viewing tax lots
- **Then** gain type and holding period are shown.

### US-0312: Journal Thesis Tag
- **Given** a journal entry with strategy tag
- **When** saving the journal
- **Then** the tag is persisted.

### US-0313: Holdings Table
- **Given** holdings
- **When** viewing holdings table
- **Then** quantity, avg cost, market value, currency chip are displayed.

### US-0314: Currency-Segregated Totals
- **Given** holdings in CAD and USD
- **When** viewing summary
- **Then** totals by currency are shown separately with note never blended.

### US-0315: Account Filter
- **Given** multiple accounts
- **When** selecting an account filter
- **Then** holdings are filtered to that account.

### US-0316: Tax-Loss Harvest Candidate
- **Given** a buy lot at unrealized loss held short-term
- **When** viewing tax lots
- **Then** harvest_candidate is true.

### US-0317: Forward Dividend Projection
- **Given** holdings with yield
- **When** viewing dividend schedule
- **Then** forward 12M projection is shown by currency.

### US-0318: Realized P&L on Sell
- **Given** a buy then sell
- **When** selling
- **Then** realized PnL is computed via average cost.

### US-0319: Holdings Search
- **Given** holdings
- **When** searching by ticker
- **Then** filtered holdings are returned.

### US-0320: Portfolio Export
- **Given** holdings
- **When** exporting
- **Then** CSV with currency tags is downloadable.

### US-0322: Dividend Yield on Cost
- **Given** buy price vs dividend
- **When** viewing holding
- **Then** yield on cost is displayed.

### US-0323: Account Currency Isolation
- **Given** TFSA CAD and RRSP USD
- **When** viewing summary
- **Then** no FX conversion is performed.

### US-0324: Holdings Count
- **Given** portfolio with holdings
- **When** viewing summary
- **Then** holdings count is shown.

### US-0325: Portfolio Distress Exposure
- **Given** holdings with Altman Distress
- **When** viewing heatmap
- **Then** distress flags are highlighted.

### US-0326: Sector Drift Alert
- **Given** sector >40% weight
- **When** viewing concentration
- **Then** concentration warning is shown.

### US-0327: Rebalancing Suggestion
- **Given** drift >5pp
- **When** viewing rebalance
- **Then** suggested trades are implied.

### US-0329: Cash Balance by Currency
- **Given** accounts with cash
- **When** viewing summary
- **Then** cash by currency is shown.

### US-0330: Transaction Fees
- **Given** a buy with fees
- **When** posting transaction
- **Then** cost basis includes fees.

### US-0331: Dividend Reinvestment
- **Given** a dividend transaction
- **When** posting dividend
- **Then** holdings quantity is not affected.

### US-0332: Holdings Sort by Value
- **Given** holdings
- **When** viewing holdings
- **Then** sorted by market value descending.

### US-0333: Account Creation
- **Given** a new account request
- **When** creating account
- **Then** account appears in list.

### US-0334: Transaction Notes
- **Given** a transaction with notes
- **When** posting
- **Then** notes are persisted.

### US-0335: Portfolio Disclaimer
- **Given** portfolio view
- **When** viewing
- **Then** disclaimer is displayed.

### US-0336: Holdings Currency Badge
- **Given** a holding row
- **When** viewing holdings
- **Then** currency chip is shown.

### US-0338: Journal Kill Conditions
- **Given** a journal with kill conditions
- **When** saving
- **Then** kill conditions are persisted.

### US-0339: Journal Confidence 1-5
- **Given** a journal with confidence
- **When** saving
- **Then** confidence is validated to 1-5.

### US-0340: Journal Strategy Tag
- **Given** a journal with strategy tag
- **When** saving
- **Then** tag is persisted.

### US-0341: Journal List by Company
- **Given** journal entries
- **When** filtering by company
- **Then** filtered journals are returned.

### US-0342: Journal Thesis Length
- **Given** a long thesis
- **When** saving
- **Then** thesis is stored up to 2000 chars.

### US-0343: Holdings Avg Cost
- **Given** buy transactions
- **When** viewing holding
- **Then** avg cost per share is shown.

### US-0344: Unrealized P&L
- **Given** a holding with market price
- **When** viewing holding
- **Then** unrealized PnL is computed.

### US-0345: Dividend Schedule by Account
- **Given** an account filter for dividends
- **When** requesting dividends with account_id
- **Then** dividends are filtered by account.

### US-0347: Tax Lots FIFO
- **Given** buy lots
- **When** viewing tax lots
- **Then** FIFO lots with gain are shown.

### US-0348: Target Allocation Bands
- **Given** rebalance with equal-weight target
- **When** viewing rebalance
- **Then** drift vs target is shown.

### US-0349: Holdings Weight Percent
- **Given** holdings with market value
- **When** viewing holdings
- **Then** weight percent is shown.

### US-0350: Portfolio Analytics Weighted Composite
- **Given** holdings with scores
- **When** viewing summary
- **Then** weighted composite is shown.

---

## Epic 12: Decision Journaling (5 Stories)

### US-0301: Buy Decision Journal
- **Given** a company and purchase details
- **When** creating a journal entry with date, confidence, thesis
- **Then** the entry is created and appears in journal list.

### US-0308: Pre-Commitment Kill Conditions
- **Given** a journal with kill conditions
- **When** saving the journal
- **Then** kill conditions are required and persisted.

### US-0321: Strategy Tag on Buy
- **Given** a buy journal with strategy tag
- **When** saving
- **Then** the tag is persisted.

### US-0337: Pre-Sell Checklist Modal
- **Given** a holding to be sold
- **When** initiating sell
- **Then** a modal prompts review of thesis, kill conditions, and tax implications.

### US-0950: Annual Reflection & Calibration
- **Given** journal entries
- **When** viewing calibration
- **Then** avg confidence and current composite per entry are shown.

---

## Epic 6: Local Alerts Engine (44 Stories)

### US-0352: Upcoming Earnings Calendar
- **Given** earnings dates within 30 days
- **When** requesting calendar
- **Then** earnings events are returned sorted by date.

### US-0353: Alert Rule Creation
- **Given** a company and rule type
- **When** creating an alert rule
- **Then** the rule is stored and appears in rule list.

### US-0354: Alert Rule List
- **Given** existing rules
- **When** listing rules
- **Then** rules are returned with params.

### US-0355: Local Monitoring Daemon
- **Given** enabled rules
- **When** evaluating
- **Then** events are generated locally without external calls.

### US-0356: Ex-Dividend Calendar
- **Given** ex-div dates within 30 days
- **When** requesting calendar
- **Then** ex-dividend events are returned.

### US-0357: Distress Alarm Immediate
- **Given** Altman Z distress
- **When** evaluating distress rule
- **Then** a critical alert is generated.

### US-0358: Intrinsic Value Trigger
- **Given** price below fair value
- **When** evaluating price_below_fair_value rule
- **Then** an alert is generated when discount >= min_change_pct.

### US-0359: Alert Events List
- **Given** evaluated alerts
- **When** requesting events
- **Then** events are returned.

### US-0360: Alert Rule Enable/Disable
- **Given** a rule
- **When** toggling enabled
- **Then** the enabled flag is updated.

### US-0361: Alert Severity
- **Given** distress vs forensic triggers
- **When** evaluating
- **Then** severity is critical for distress, elevated for forensic.

### US-0362: Alert Detail Message
- **Given** a triggered alert
- **When** viewing the event
- **Then** a detail message is present.

### US-0363: Calendar Sorting
- **Given** calendar items
- **When** viewing calendar
- **Then** items are sorted by event date.

### US-0364: Heartbeat Operational
- **Given** the daemon
- **When** requesting heartbeat
- **Then** status operational with daemon name is returned.

### US-0365: De-noising Minimum Change
- **Given** a rule with high min_change_pct
- **When** evaluating
- **Then** no trigger if below threshold.

### US-0366: Quiet Hours Batching
- **Given** a rule with quiet hours
- **When** evaluating
- **Then** evaluation is batched.

### US-0369: Alert Company Filter
- **Given** rules for multiple companies
- **When** filtering by company
- **Then** only matching rules are returned.

### US-0370: Minimum Change Filter
- **Given** a price trigger with min pct
- **When** evaluating
- **Then** the discount must exceed min pct.

### US-0371: Unified Calendar
- **Given** earnings and ex-div events
- **When** viewing calendar
- **Then** both types appear in a unified list.

### US-0372: Alert Timestamp
- **Given** a triggered event
- **When** viewing the event
- **Then** triggered_at timestamp is present.

### US-0373: Alert Ticker
- **Given** an event with company
- **When** viewing the event
- **Then** ticker is displayed.

### US-0375: Alert Rule Params JSON
- **Given** a rule with params_json
- **When** saving
- **Then** params are persisted.

### US-0376: Alert Evaluate by Company
- **Given** a company filter for evaluation
- **When** evaluating for one company
- **Then** only that company rules are evaluated.

### US-0378: Filing Milestone Calendar
- **Given** filing dates
- **When** viewing calendar
- **Then** filing milestones are shown.

### US-0379: Alert Disclaimer
- **Given** alerts view
- **When** viewing
- **Then** disclaimer is displayed.

### US-0380: Graham Fair Value Alert
- **Given** price below Graham fair value
- **When** evaluating
- **Then** a trigger is generated.

### US-0381: Alert Count Badge
- **Given** active alerts
- **When** viewing AppShell
- **Then** badge count is shown.

### US-0382: Alert Drawer
- **Given** alert notification
- **When** opening drawer
- **Then** drawer shows recent events.

### US-0383: Calendar Days Ahead
- **Given** calendar
- **When** viewing
- **Then** days_ahead field is present.

### US-0384: Alert Channel
- **Given** a triggered alert
- **When** viewing
- **Then** channel information is present.

### US-0386: Alert Rule Creation Validation
- **Given** an invalid company ID
- **When** creating a rule
- **Then** a 404 is returned.

### US-0387: Alert Evaluate No Rules
- **Given** no rules
- **When** evaluating
- **Then** empty events are returned.

### US-0388: Alert Rule Delete
- **Given** an existing rule
- **When** deleting
- **Then** the rule is removed.

### US-0389: Alert History
- **Given** evaluated history
- **When** viewing events
- **Then** audit log is available.

### US-0390: Distress vs Forensic Severity Mapping
- **Given** distress vs forensic
- **When** evaluating
- **Then** severity mapping is correct.

### US-0391: Alert Filtering
- **Given** events
- **When** filtering
- **Then** filtered events are returned.

### US-0392: Calendar Empty State
- **Given** no calendar events
- **When** viewing calendar
- **Then** empty message is shown.

### US-0393: Heartbeat Disclaimer
- **Given** heartbeat
- **When** viewing
- **Then** disclaimer is present.

### US-0394: Alert Audit Log
- **Given** alert events
- **When** viewing
- **Then** audit log is available.

### US-0395: Alert Local-Only
- **Given** an alert rule
- **When** storing
- **Then** it is stored locally with no external send.

### US-0396: Alert Enable Toggle
- **Given** a rule
- **When** toggling enabled
- **Then** enabled flag is updated.

### US-0397: Alert Rule Params JSON Persistence
- **Given** params JSON
- **When** saving
- **Then** params are persisted.

### US-0398: Alert Evaluate Local — No Network
- **Given** local evaluation
- **When** evaluating
- **Then** no network calls are made.

### US-0399: Alert Calendar Unified
- **Given** a unified calendar
- **When** viewing
- **Then** earnings + dividends are shown.

### US-0400: System Heartbeat Weekly
- **Given** the heartbeat endpoint
- **When** requesting heartbeat
- **Then** status operational is returned weekly.

---

## Cross-Cutting Acceptance Notes

- Holdings and cash totals are segregated by native currency (CAD vs USD); portfolio summary shows separate totals per currency with explicit note never blended.
- Portfolio weighted pillar averages use unitless scores weighted by market value.
- Missing price → market_value NULL + flag; missing dividend history → trailing/forward 0 with reason.
- Journal confidence 1-5 validated; kill_conditions and thesis stored locally (SQLite decision_journal).
- Alerts evaluate locally against snapshots/scores/filings; no external push; de-noising via min_change_pct and quiet-hours batching; heartbeat GET /alerts/heartbeat returns operational.
- Pure SVG allocation/sector charts use <svg>, <rect>, <text> with tokens.css.
- a11y: transaction/journal forms, alert drawer, and SVG charts have ARIA roles/labels and Tab/Escape support; prefers-reduced-motion respected.
- Disclaimer on every portfolio/alert surface: Personal research software, not investment advice. Portfolio tracking and alerts run locally.
