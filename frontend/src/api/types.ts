/** Shared API types — mirror the backend payloads (Phases 1-4). */

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
}

export interface ScreenOut {
  total: number;
  count: number;
  currency_view: string;
  items: ScreenItem[];
  method_version: string;
  disclaimer: string;
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
  };
  latest_snapshot: Snapshot | null;
  history_annual: HistoryRow[];
  history_warnings?: string[];
  score: ScorePayload | null;
  halal: HalalPayload | null;
  data_gaps: string[];
  profile?: CompanyProfile | null;
  quarterly?: QuarterlyRow[] | null;
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
  fcf_yield: number | null;
  ev_ebitda: number | null;
  pe_ratio: number | null;
  sloan_accrual_ratio: number | null;
  cash_conversion_ratio: number | null;
  market_implied_growth_10y: number | null;
  historical_5y_cagr: number | null;
  expectations_gap: number | null;
  dcf_status: string;
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

