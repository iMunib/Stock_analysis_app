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
  };
  latest_snapshot: Snapshot | null;
  history_annual: HistoryRow[];
  score: ScorePayload | null;
  halal: HalalPayload | null;
  data_gaps: string[];
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
  company_id: string;
  in_universe: boolean;
  year_count: number;
  fiscal_years: number[];
  counts: Record<string, number>;
  price_filled: boolean;
}
