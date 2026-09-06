/** Shared API types - mirror the backend payloads (Phases 1-4). */

export interface SearchItem {
  company_id: string;
  name: string | null;
  ticker: string | null;
  currency: string | null;
  sector: string | null;
  composite: number | null;
  signal: string | null;
  peer_rank: number | null;
  peer_n: number | null;
}

export interface SearchOut {
  q: string;
  count: number;
  items: SearchItem[];
  method_version: string;
  disclaimer: string;
}

export interface SuggestionItem {
  company_id: string;
  ticker: string;
  name: string | null;
  exchange: string;
  country: string;
  sector: string | null;
  in_database: boolean;
  tradingview_symbol: string;
  composite?: number | null;
  signal?: string | null;
  universe_tags?: string[];
}

export interface SuggestionsOut {
  q: string;
  count: number;
  items: SuggestionItem[];
}

export interface Snapshot {
  revenue?: number | null;
  net_income?: number | null;
  diluted_eps?: number | null;
  gross_profit?: number | null;
  operating_cash_flow?: number | null;
  capex?: number | null;
  fcf_calc?: number | null;
  netdebt_calc?: number | null;
  total_debt?: number | null;
  book_equity?: number | null;
  cash_st_investments?: number | null;
  total_assets?: number | null;
  total_liabilities?: number | null;
  ebit?: number | null;
  ebitda?: number | null;
  interest_expense?: number | null;
  roe_calc?: number | null;
  roa_calc?: number | null;
  fcfmargin_calc?: number | null;
  grossmargin_calc?: number | null;
  pe_calc?: number | null;
  pb_calc?: number | null;
  ev_to_ebitda_calc?: number | null;
  price?: number | null;
  market_cap?: number | null;
  cet1_ratio?: number | null;
  leverage_ratio?: number | null;
  nim_fy2025?: number | null;
  efficiency_ratio?: number | null;
  roaa?: number | null;
  as_of_date?: string | null;
  source?: string | null;
  price_asof?: string | null;
  price_currency?: string | null;
  [k: string]: unknown;
}

export interface HistoryRow {
  fiscal_year: number;
  revenue?: number | null;
  net_income?: number | null;
  fcf_calc?: number | null;
  diluted_eps?: number | null;
  source?: string | null;
  quality_flag?: string | null;
  warning?: string | null;
  used_for_growth?: boolean;
}

export interface ScorePillars {
  quality: number | null;
  value: number | null;
  growth: number | null;
  risk: number | null;
}

export interface ScorePayload {
  composite: number | null;
  pillars: ScorePillars;
  coverage: number | null;
  penalty: number | null;
  signal: string | null;
  peer_set_type: string | null;
  peer_rank: number | null;
  peer_n: number | null;
  as_of_fy: number | null;
  computed_at: string | null;
  method_version: string;
  percentiles?: Record<string, number | null> | null;
}

export interface HalalPayload {
  status: string;
  method: string;
  failed_tests: { test: string; basis?: unknown; ratio?: unknown }[];
}

export interface CompanyProfile {
  summary?: string | null;
  dividend_yield?: number | null;
  dividend_rate?: number | null;
  next_earnings_date?: string | null;
}

export interface QuarterlyRow {
  date: string;
  revenue?: number | null;
  net_income?: number | null;
  diluted_eps?: number | null;
}

export interface SwotOut {
  company_id: string;
  swot: string;
  model: string;
  cached: boolean;
  label: string;
  disclaimer: string;
  elapsed_ms?: number;
}

export interface WhyMatchedSummary {
  median_composite: number | null;
  median_pe: number | null;
  median_roe: number | null;
  top_sectors: Array<{ sector: string; count: number }>;
  count: number;
}

export interface NullWarning {
  has_null_data_warning: boolean;
  null_reasons: string[];
  explanation?: string | null;
}

export interface ScreenItem {
  company_id: string;
  name: string | null;
  ticker: string | null;
  currency: string | null;
  gics_sector: string | null;
  custom_industry_sheet: string | null;
  composite: number | null;
  signal: string | null;
  pe_calc: number | null;
  roe_calc: number | null;
  fcfmargin_calc: number | null;
  peer_rank: number | null;
  peer_n: number | null;
  coverage: number | null;
  has_growth_history: boolean;
  is_bank: boolean;
  halal_status: string | null;
  money?: Record<string, number | null> | null;

  // Wave 2 rich metrics (Epic 7):
  market_cap?: number | null;
  market_cap_band?: string | null;
  roic_calc?: number | null;
  ev_to_ebitda_calc?: number | null;
  debt_to_ebitda_calc?: number | null;
  interest_coverage_calc?: number | null;
  gross_profitability?: number | null;
  sbc_ratio?: number | null;
  cagr_rev_3y?: number | null;
  altman_z?: number | null;
  altman_zone?: string | null;
  is_turnaround?: boolean;
  revenue_sparkline?: number[];
  checklists?: {
    graham?: boolean;
    lynch?: boolean;
    greenblatt?: boolean;
    piotroski?: boolean;
  };
}

export interface ScreenOut {
  total: number;
  count: number;
  currency_view: string;
  items: ScreenItem[];
  method_version: string;
  disclaimer: string;
  why_matched_summary?: WhyMatchedSummary | null;
  null_warning?: NullWarning | null;
}

export interface ScreenerPresetItem {
  id: string;
  name: string;
  description?: string | null;
  criteria: Record<string, any>;
  auto_run?: boolean;
  created_at?: string;
}

export interface WatchlistAlertRouting {
  primary_channel: string;
  fallback_channel: string;
  urgency: string;
}

export interface WatchlistDigestAlert {
  id: string;
  company_id: string;
  ticker: string;
  name: string;
  alert_type: string;
  title: string;
  detail: string;
  severity: "high" | "medium" | "low";
  routing: WatchlistAlertRouting;
  metrics?: Record<string, any>;
  sedar_url?: string | null;
  edgar_url?: string | null;
  timestamp: string;
}

export interface WatchlistDigestStats {
  total_watched: number;
  high_severity_count: number;
  medium_severity_count: number;
  low_severity_count: number;
  rerated_count: number;
  earnings_count: number;
}

export interface WatchlistDigestResponse {
  brief_date: string;
  market_session: string;
  stats: WatchlistDigestStats;
  alerts: WatchlistDigestAlert[];
  cad_companies_count: number;
  usd_companies_count: number;
  currency_segregation_note: string;
  disclaimer: string;
}

export interface WatchlistDeltaItem {
  company_id: string;
  ticker: string;
  name: string;
  currency: string;
  current_composite: number | null;
  prior_composite: number | null;
  delta_composite: number | null;
  current_signal: string | null;
  prior_signal: string | null;
  is_rerated: boolean;
  pillar_deltas: {
    quality?: number | null;
    value?: number | null;
    growth?: number | null;
    risk?: number | null;
  };
  earnings_post_actual?: {
    fiscal_year?: number;
    revenue_actual?: number | null;
    prior_year_revenue?: number | null;
    revenue_growth_pct?: number | null;
    net_income_actual?: number | null;
    prior_year_net_income?: number | null;
  } | null;
  filing_links: {
    edgar?: string | null;
    sedar_plus?: string | null;
  };
  as_of: string;
}

export interface WatchlistDeltasResponse {
  count: number;
  deltas: WatchlistDeltaItem[];
  timestamp: string;
}

export interface DossierOut {
  identity: {
    company_id: string;
    name: string | null;
    currency: string | null;
    country: string | null;
    gics_sector: string | null;
    gics_industry: string | null;
    custom_industry_sheet: string | null;
    indexes: string[] | null;
    in_sp500: boolean;
    in_tsx_composite: boolean;
    cik?: number | null;
    ticker?: string | null;
    reporting_currency?: string | null;
    filing_type?: string | null;
    exchange?: string | null;
    tradingview_symbol?: string | null;
  };
  latest_snapshot: Snapshot | null;
  history_annual: HistoryRow[];
  history_warnings?: string[];
  score: ScorePayload | null;
  halal: HalalPayload | null;
  data_gaps: string[];
  profile?: CompanyProfile | null;
  quarterly?: QuarterlyRow[] | null;
  decision_verdict?: {
    verdict_badge?: string | null;
    traffic_lights?: Record<string, string> | null;
    reverse_dcf_rule?: string | null;
    decision_bullets?: string[] | null;
    expectations_gap?: number | null;
    moat_rating?: string | null;
    archetype?: string | null;
  } | null;
  archetype?: {
    archetype?: string | null;
    peg_ratio?: number | null;
    eps_cagr_5y?: number | null;
  } | null;
  moat_rating?: {
    moat_rating?: string | null;
    score?: number | null;
  } | null;
  expectations_gap?: number | null;
  level1?: {
    identity?: Record<string, any> | null;
    verdict_badge?: string | null;
    traffic_lights?: Record<string, string> | null;
    reverse_dcf_rule?: string | null;
    decision_bullets?: string[] | null;
    implied_10y_cagr?: number | null;
    historical_5y_cagr?: number | null;
    expectations_gap?: number | null;
  } | null;
  level2?: {
    four_pillar_radar?: Record<string, any> | null;
    lynch_archetype?: Record<string, any> | null;
    true_shareholder_yield?: Record<string, any> | null;
    cash_flow_waterfall?: Record<string, any> | null;
  } | null;
  level3?: {
    beneish_matrix?: Record<string, any> | null;
    penman_table?: {
      noa?: number | null;
      nfo?: number | null;
      rnoa?: number | null;
      flev?: number | null;
      nbc?: number | null;
      roe_operational_spread?: number | null;
      exclusion?: string | null;
    } | null;
    altman_breakdown?: Record<string, any> | null;
    statement_history_10y?: HistoryRow[] | null;
  } | null;
  pillar_drilldown?: PillarDrilldownOut | null;
  tensions?: PillarTension[] | null;
  bear_case?: BearCaseOut | null;
  vintage?: {
    filing_vintage?: string;
    price_vintage?: string;
    composite_vintage?: string;
  } | null;
  sector_medians?: Record<string, number | null> | null;
  method_version: string;
  disclaimer: string;
}

export interface CompareRow {
  company_id: string;
  name: string | null;
  currency: string | null;
  found: boolean;
  composite: number | null;
  quality: number | null;
  value: number | null;
  growth: number | null;
  risk: number | null;
  signal: string | null;
  pe_calc: number | null;
  pb_calc: number | null;
  roe_calc: number | null;
  roa_calc: number | null;
  fcfmargin_calc: number | null;
  ev_to_ebitda_calc: number | null;
  peer_rank: number | null;
  halal_status: string | null;
  money: ({ currency: string | null } & Record<string, number | null>) | null;
}

export interface CompareOut {
  ids: string[];
  currency_warning: boolean;
  currencies: string[];
  comparable: string[];
  rows: CompareRow[];
  method_version: string;
  disclaimer: string;
}

export interface SimilarItem {
  company_id: string;
  name: string | null;
  composite: number | null;
  signal: string | null;
  better: boolean;
  currency: string | null;
}

export interface SimilarOut {
  company_id: string;
  peer_set_type: string | null;
  peer_n: number | null;
  items: SimilarItem[];
  method_version: string;
  disclaimer: string;
}

export interface SectorSnapshotOut {
  sheet: string;
  currency: string;
  companies: number;
  scored: number;
  signal_histogram: Record<string, number>;
  median_composite: number | null;
  median_pe: number | null;
  median_pb: number | null;
  median_roe: number | null;
  top: { company_id: string; name: string | null; composite: number | null; signal: string | null }[];
  bottom: { company_id: string; name: string | null; composite: number | null; signal: string | null }[];
  method_version: string;
  disclaimer: string;
}

export interface ResearchMetaOut {
  companies: number;
  scored: number;
  insufficient_data: number;
  growth_null: number;
  signal_histogram: Record<string, number>;
  method_version: string;
  last_recompute: string | null;
  disclaimer: string;
}

export interface IngestOut {
  job_id: string;
  status: string;
  kind?: string;
  step?: string | null;
  message?: string | null;
  company_id?: string | null;
  error_code?: string | null;
}

export interface RankingsItem {
  rank: number;
  company_id: string;
  name: string | null;
  country: string | null;
  currency: string | null;
  gics_sector: string | null;
  custom_industry_sheet: string | null;
  composite: number | null;
  signal: string | null;
  method_version: string;
}

export interface RankingsOut {
  scope: string;
  total: number;
  limit: number;
  offset: number;
  items: RankingsItem[];
  disclaimer: string;
}

export interface SectorCount {
  name: string;
  count: number;
  usd: number;
  cad: number;
  median_composite_usd?: number | null;
  median_composite_cad?: number | null;
  median_composite_all?: number | null;
}

export interface SectorsOut {
  custom_industries: SectorCount[];
  gics_sectors: SectorCount[];
}

export interface SectorRankingItem {
  rank: number;
  company_id: string;
  name: string | null;
  ticker?: string | null;
  currency?: string | null;
  composite: number | null;
  signal: string | null;
  peer_set_type: string | null;
  peer_rank: number | null;
  halal_status: string | null;
  pe_calc?: number | null;
  pb_calc?: number | null;
  roe_calc?: number | null;
  method_version: string;
}

export interface SectorRankingsOut {
  sheet: string;
  currency: string;
  count: number;
  items: SectorRankingItem[];
  disclaimer: string;
  note?: string;
}

export interface JobOut {
  id: string;
  kind: string;
  status: string;
  step?: string | null;
  message?: string | null;
  company_id?: string | null;
  error_code?: string | null;
  payload: Record<string, unknown>;
  progress_done: number;
  progress_total: number;
  error: string | null;
  provider_stats: Record<string, unknown>;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface NarrationResult {
  narration?: string;
  model?: string;
  cached?: boolean;
  narration_unavailable?: boolean;
  reason?: string;
  facts?: unknown;
  banner?: string;
  disclaimer?: string;
}

export interface JobsListOut {
  count: number;
  items: JobOut[];
  method_version: string;
  disclaimer: string;
}

export type CurrencyView = "ALL" | "USD" | "CAD";

export interface FcfVsNiYear {
  fiscal_year: number;
  net_income: number | null;
  fcf: number | null;
}

export interface ForensicsOut {
  company_id: string;
  currency: string;
  sloan_accrual_ratio: number | null;
  sloan_signal: "green" | "red" | "neutral" | "insufficient_data";
  cash_conversion_ratio: number | null;
  cash_conversion_signal: "weak" | "healthy" | "insufficient_data";
  roic: number | null;
  roic_interpretation?: "normal" | "distorted_low_denominator" | "negative_capital" | "not_meaningful" | null;
  roic_confidence?: "high" | "medium" | "low" | null;
  roic_warning_reason?: string | null;
  invested_capital_to_assets?: number | null;
  fcf_yield: number | null;
  nopat: number | null;
  invested_capital: number | null;
  fcf_vs_ni_history: FcfVsNiYear[];
}

export interface SensitivityCell {
  wacc: number;
  terminal_g: number;
  implied_growth: number | null;
}

export interface SensitivityMatrix {
  wacc_headers: number[];
  terminal_g_headers: number[];
  grid: SensitivityCell[][];
}

export interface ValuationOut {
  company_id: string;
  status: string;
  current_share_price: number | null;
  diluted_shares: number | null;
  net_debt: number | null;
  baseline_fcf: number | null;
  wacc: number;
  terminal_growth_rate: number;
  market_implied_growth_10y: number | null;
  historical_5y_cagr: number | null;
  expectations_gap: number | null;
  sensitivity_matrix: SensitivityMatrix | null;
  price_as_of?: string | null;
  price_freshness?: "green" | "amber" | "red" | "unknown" | null;
  baseline_fcf_period_end?: string | null;
  baseline_fcf_basis?: "TTM" | "FY" | "MRQ" | null;
  fcf_freshness?: "green" | "amber" | "red" | "unknown" | null;
  valuation_computed_at?: string | null;
}

export interface ScreenerPreset {
  id: string;
  name: string;
  criteria: Record<string, unknown>;
  is_system: boolean;
}

export interface ScreenerRow {
  company_id: string;
  ticker: string | null;
  name: string | null;
  currency: string | null;
  gics_sector: string | null;
  custom_industry: string | null;
  composite: number | null;
  signal: string | null;
  roic: number | null;
  roic_interpretation?: string | null;
  roic_confidence?: string | null;
  eqr?: number | null;
  fcf_yield: number | null;
  ev_ebitda: number | null;
  pe_ratio: number | null;
  sloan_accrual_ratio: number | null;
  cash_conversion_ratio: number | null;
  market_implied_growth_10y: number | null;
  historical_5y_cagr: number | null;
  expectations_gap: number | null;
  dcf_status: string;
  rnoa?: number | null;
  flev?: number | null;
  altman_z?: number | null;
  altman_zone?: string | null;
  total_shareholder_yield?: number | null;
  value_percentile?: number | null;
  quality_percentile?: number | null;
}

export interface ScreenerResult {
  items: ScreenerRow[];
  count: number;
  limit: number;
  offset: number;
}

export interface DeleteCompanyOut {
  ok: boolean;
  company_id: string;
  message: string;
}

export interface DistressAnalysis {
  company_id: string;
  fiscal_year?: number | null;
  status: "computed" | "financial_institution_excluded" | "insufficient_data";
  model_used: "manufacturing" | "non_manufacturing" | "excluded" | null;
  z_score: number | null;
  z_double_prime: number | null;
  active_z: number | null;
  zone: "Safe" | "Grey" | "Distress" | "Excluded" | "Unknown";
  message?: string;
  factors?: {
    x1_working_capital_to_ta: number;
    x2_retained_earnings_to_ta: number;
    x3_ebit_to_ta: number;
    x4_market_equity_to_tl: number;
    x5_sales_to_ta: number;
  } | null;
}

export interface ShareholderYield {
  company_id: string;
  currency: string;
  share_count_history: { fiscal_year: number; diluted_shares: number }[];
  share_count_delta_1y_pct: number | null;
  share_count_cagr_3y_pct: number | null;
  net_repurchase_rate_pct?: number | null;
  gross_buyback_yield_pct?: number | null;
  sbc_drag_pct?: number | null;
  sbc_dilution_offset_pct?: number | null;
  net_buyback_yield_pct: number | null;
  dividend_yield_pct: number | null;
  total_shareholder_yield_pct: number | null;
  true_shareholder_yield_pct?: number | null;
  flags: string[];
}

export interface BeneishAnalysis {
  company_id: string;
  fiscal_year?: number | null;
  status: string;
  m_score: number | null;
  is_manipulator: boolean;
  zone: string;
  threshold: number;
  variables?: {
    dsri: number | null;
    gmi: number | null;
    aqi: number | null;
    sgi: number | null;
    depi: number | null;
    sgai: number | null;
    lvgi: number | null;
    tata: number | null;
  } | null;
  interpretation: string;
  message?: string;
}

export interface ETFCohortItem {
  company_id: string;
  ticker: string;
  name: string;
  currency: string;
  composite: number | null;
  signal: string | null;
  sector: string | null;
  universe_tags?: string[] | null;
}

export type ETFCohortsOut = Record<string, ETFCohortItem[]>;

export interface PractitionerOut {
  company_id: string;
  penman?: {
    rnoa: number | null;
    flev: number | null;
    nbc: number | null;
    noa: number | null;
    nfo: number | null;
    guardrail?: {
      triggered: boolean;
      reported_roic: number | null;
      penman_rnoa: number | null;
      flev: number | null;
      flag: string | null;
      note: string | null;
    };
  };
  fridson?: {
    reality_spread: number | null;
    cfo: number | null;
    ebitda: number | null;
    flag: string | null;
    interpretation: string | null;
    fixed_charge_coverage: number | null;
  };
  graham?: {
    graham_number: number | null;
    ncav_per_share: number | null;
    nnwc_per_share: number | null;
    margin_of_safety_pct: number | null;
    current_price: number | null;
  };
  malkiel?: {
    index_hurdle_rate?: number;
    index_nominal_hurdle_pct?: number;
    fcf_yield_pct: number | null;
    required_fcf_growth_10y?: number | null;
    required_fcf_growth_pct?: number | null;
    opportunity_cost_benchmark?: string;
    interpretation?: string;
  };
  behavioral?: {
    fomo_risk: boolean;
    valuation_stretch_sigmas: number | null;
    executive_safety_verdict: {
      moat_durability: "Pass" | "Caution";
      solvency_runway: "Pass" | "Caution";
      valuation_safety: "Pass" | "Caution";
      overall: "Pass" | "Caution";
    };
  };
  distress_analysis?: DistressAnalysis;
  shareholder_yield?: ShareholderYield;
  beneish_analysis?: BeneishAnalysis;
}

export interface CommonSizeLineItem {
  raw: number | null;
  pct: number | null;
}

export interface MarginDriftFlag {
  code: string;
  severity: "info" | "warning" | "danger";
  metric: string;
  from_year: number;
  to_year: number;
  change_bps: number;
  message: string;
}

export interface CommonSizeOut {
  company_id: string;
  currency: string;
  years_delivered: number;
  income_statement_common_size: Record<string, any>[];
  balance_sheet_common_size: Record<string, any>[];
  margin_drift_flags: MarginDriftFlag[];
}

export interface PiotroskiTest {
  name: string;
  category: string;
  passed: boolean | null;
  current_value: number | null;
  prior_value: number | null;
  description: string;
}

export interface PiotroskiOut {
  company_id: string;
  fiscal_year: number | null;
  prior_fiscal_year: number | null;
  f_score: number;
  f_possible: number;
  signal: string;
  interpretation: string;
  is_bank: boolean;
  tests: Record<string, PiotroskiTest>;
  categories: {
    profitability: PiotroskiTest[];
    leverage_liquidity: PiotroskiTest[];
    efficiency: PiotroskiTest[];
  };
}

export interface DuPontYear {
  fiscal_year: number;
  roe_direct: number | null;
  net_profit_margin: number | null;
  asset_turnover: number | null;
  equity_multiplier: number | null;
  roe_3stage: number | null;
  tax_burden: number | null;
  interest_burden: number | null;
  operating_margin: number | null;
  roe_5stage: number | null;
  revenue: number | null;
  net_income: number | null;
  ebit: number | null;
  total_assets: number | null;
  book_equity: number | null;
}

export interface DuPontOut {
  company_id: string;
  is_bank: boolean;
  primary_driver: string;
  driver_explanation: string;
  latest: DuPontYear | null;
  history: DuPontYear[];
}

export interface PeerMatrixMetric {
  value: number | null;
  percentile: number | null;
}

export interface PeerMatrixOut {
  company_id: string;
  peer_group: string;
  peer_count: number;
  pillars: {
    valuation: Record<string, PeerMatrixMetric>;
    quality: Record<string, PeerMatrixMetric>;
    financial_health: Record<string, PeerMatrixMetric>;
    capital_allocation: Record<string, PeerMatrixMetric>;
  };
}

// =========================================================================
// WAVE 1 TYPES (EPICS 1 - 4)
// =========================================================================

export interface StatementLineItem {
  name: string;
  raw_value: number | null;
  formatted: string;
  currency: string;
  period: string;
  provenance: string;
  sec_edgar_url?: string | null;
}

export interface SubMetric {
  metric_id: string;
  name: string;
  raw_value: number | null;
  formatted_value: string;
  weight: number;
  normalized_score?: number | null;
  line_items: StatementLineItem[];
  formula_definition: string;
}

export interface RiskSubBar {
  name: string;
  score: number;
  max: number;
  interpretation: string;
  metrics: { label: string; value: string }[];
}

export interface PillarDetail {
  score: number | null;
  formula: string;
  interpretation: string;
  missing_faq: string;
  sector_median?: number | null;
  sub_bars?: Record<string, RiskSubBar>;
  sub_metrics: SubMetric[];
}

export interface PillarTension {
  tension_id: string;
  title: string;
  chip: string;
  summary: string;
  pillars_involved: string[];
  tone: "warn" | "neg" | "info" | "pos";
}

export interface CoveragePenaltyTier {
  pillars: number;
  multiplier: number;
  label: string;
}

export interface CoveragePenaltyDetails {
  unadjusted_weighted_score: number | null;
  coverage_count: number;
  multiplier: number;
  deduction: number;
  formula_string: string;
  published_score: number | null;
  penalty_table: CoveragePenaltyTier[];
}

export interface PillarDrilldownOut {
  company_id: string;
  name: string;
  currency: string;
  sector_peer_medians: Record<string, number | null>;
  tensions: PillarTension[];
  coverage_penalty: CoveragePenaltyDetails;
  method_version: string;
  disclaimer: string;
  pillars: {
    quality: PillarDetail;
    value: PillarDetail;
    growth: PillarDetail;
    risk: PillarDetail;
  };
}

export interface RatioComponent {
  label: string;
  raw_value: number | null;
  formatted: string;
  units: string;
  currency: string;
  as_of_date: string;
  statement_location: string;
  source: string;
  sec_edgar_url?: string | null;
}

export interface RatioInspectOut {
  company_id: string;
  ratio_id: string;
  label: string;
  formula_string: string;
  result: number | null;
  result_formatted: string;
  vintage: string;
  numerator: RatioComponent;
  denominator: RatioComponent;
  arithmetic_resolution: string[];
}

export interface SectorHealthBreakdown {
  sector: string;
  company_count: number;
  quality_pct: number;
  value_pct: number;
  growth_pct: number;
  risk_pct: number;
  average_pillars: number;
}

export interface NullFieldMissing {
  field: string;
  missing_count: number;
  pct: number;
}

export interface CoverageHealthOut {
  universe_summary: {
    total_companies: number;
    us_names: number;
    canadian_names: number;
    seed_target: number;
    coverage_verified: boolean;
  };
  provenance_summary: {
    total_snapshot_rows: number;
    seed_workbook_rows: number;
    provider_backfill_rows: number;
    seed_completeness_pct: number;
  };
  pillar_completeness: {
    quality: { count: number; pct: number };
    value: { count: number; pct: number };
    growth: { count: number; pct: number };
    risk: { count: number; pct: number };
    composite: { count: number; pct: number };
  };
  sector_breakdown: SectorHealthBreakdown[];
  null_data_audit: {
    total_cells_audited: number;
    total_null_cells: number;
    null_percentage: number;
    honest_null_policy: string;
    top_missing_fields: NullFieldMissing[];
  };
}

export interface LowestPercentileItem {
  metric_id: string;
  label: string;
  percentile: number;
  rank_descriptor: string;
}

export interface ForensicConcern {
  model: string;
  flag: string;
  detail: string;
  false_positive_rate: string;
  severity: "high" | "medium" | "low";
}

export interface BearCaseOut {
  company_id: string;
  company_name: string;
  bear_thesis_narrative: string;
  core_vulnerabilities: string[];
  lowest_3_percentiles: LowestPercentileItem[];
  forensic_flags: ForensicConcern[];
  pre_mortem_challenge: string;
  equal_billing_mandate: string;
}

export interface CanonicalFactor {
  factor_id: string;
  name: string;
  academic_source: string;
  historical_annualized_premium: string;
  sharpe_ratio: number;
  max_drawdown: string;
  sample_window: string;
  regime_sensitivity: string;
  decay_date: string;
}

export interface ForensicModelEvidence {
  model_id: string;
  name: string;
  author: string;
  publication_year: number;
  sample_period: string;
  date_badge: string;
  out_of_sample_behavior: string;
  false_positive_rate: string;
  limitations: string;
}

export interface FactorEvidenceOut {
  bessembinder_base_rate: {
    title: string;
    stat: string;
    statement: string;
    citations: string[];
    probabilistic_lesson: string;
  };
  canonical_factors: CanonicalFactor[];
  forensic_models: ForensicModelEvidence[];
}

// =========================================================================
// WAVE 3 TYPES (EPICS 8 & 9 - Forensics Red Flags & Restatements)
// =========================================================================

export interface BenfordOut {
  company_id: string;
  status: string;
  data_available: boolean;
  observations: number;
  min_required: number;
  observed_freq: Record<string, number> | null;
  expected_freq: Record<string, number> | null;
  observed_counts?: Record<string, number> | null;
  chi2: number | null;
  degrees_of_freedom: number;
  verdict: "conforms" | "deviation_noted" | "strong_deviation" | "insufficient_data";
  interpretation: string;
  disclaimer: string;
}

export interface ForensicsSummaryFlag {
  code: string;
  severity: "critical" | "elevated" | "informational";
  detail: string;
  threshold: unknown;
  value: unknown;
}

export interface ForensicsSummaryOut {
  company_id: string;
  currency: string | null;
  forensic_health_score: number;
  forensic_risk_tier: string;
  flag_count: number;
  flags: ForensicsSummaryFlag[];
  triggered_codes: string[];
  cross_model_divergence: string | null;
  plain_language_summary: string;
  beneish: BeneishAnalysis;
  distress: DistressAnalysis;
  sloan: Record<string, unknown>;
  shenanigans: Record<string, unknown>;
  benford: { verdict: string; chi2: number | null; observations: number };
  disclaimer: string;
  method_version: string;
}

export interface ForensicsTimelineItem {
  fiscal_year: number;
  beneish_m: number | null;
  beneish_zone: string | null;
  altman_z: number | null;
  altman_zone: string | null;
  sloan_ratio: number | null;
  sloan_flag: string | null;
}

export interface ForensicsTimelineOut {
  company_id: string;
  count: number;
  timeline: ForensicsTimelineItem[];
  disclaimer: string;
}

export interface ForensicsRankItem {
  company_id: string;
  ticker: string | null;
  name: string | null;
  currency: string | null;
  severity_score: number;
  worst_flag: string | null;
  flag_count: number;
  altman_zone: string | null;
  beneish_zone: string | null;
  sloan_flag: string | null;
}

export interface ForensicsRankOut {
  count: number;
  ranked: ForensicsRankItem[];
}

export interface RestatementItem {
  fiscal_year: number;
  as_filed: Record<string, number | string | null>;
  as_restated: Record<string, number | string | null> | null;
  delta_pct: Record<string, number | null>;
  has_restatement: boolean;
  provenance: { filed_source: string | null; restated_source: string | null };
}

export interface RestatementsOut {
  company_id: string;
  count: number;
  items: RestatementItem[];
  disclaimer: string;
}

export interface TrajectoryPoint {
  fiscal_year: number;
  revenue: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  fcf: number | null;
  inflections: string[];
  currency: string | null;
}

export interface TrajectoryOut {
  company_id: string;
  count: number;
  points: TrajectoryPoint[];
  currency: string | null;
}

export interface WorkingCapitalPoint {
  fiscal_year: number;
  dso: number | null;
  dio: number | null;
  dpo: number | null;
  ccc: number | null;
  dso_yoy?: number | null;
  dio_yoy?: number | null;
  dpo_yoy?: number | null;
  ccc_yoy?: number | null;
}

export interface WorkingCapitalOut {
  company_id: string;
  data_available: boolean;
  reason?: string | null;
  series: WorkingCapitalPoint[];
  disclaimer: string;
}

export interface GoodwillRiskOut {
  company_id: string;
  goodwill: Record<string, unknown>;
  serial_acquirer: Record<string, unknown>;
  strip: Array<{ fiscal_year: number | null; proxy_intangible_ratio: number | null; total_assets: number | null }>;
  disclaimer: string;
}

export interface DilutionPoint {
  fiscal_year: number | null;
  shares: number | null;
  sbc: number | null;
  annotation?: string | null;
  delta?: number | null;
  delta_pct?: number | null;
  sbc_dilution_note?: string | null;
}

export interface DilutionOut {
  company_id: string;
  count: number;
  series: DilutionPoint[];
  disclaimer: string;
}


