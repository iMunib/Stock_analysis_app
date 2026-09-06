import type {
  JobOut,
  JobsListOut,
  NarrationResult,
  RankingsOut,
  SectorsOut,
  SectorRankingsOut,
} from "./types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const TIMEOUT_MS = 15_000;

async function request<T>(path: string, init?: RequestInit, timeoutMs = TIMEOUT_MS): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let resp: Response;
  try {
    resp = await fetch(path, { ...init, signal: ctrl.signal, headers: { Accept: "application/json", ...(init?.headers ?? {}) } });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ApiError(0, `Request timed out after ${timeoutMs / 1000}s. Is the api container running?`);
    }
    throw new ApiError(0, "Cannot reach the research API. Is the api container running on port 8000?");
  } finally {
    clearTimeout(timer);
  }
  const text = await resp.text().catch(() => "");
  if (!resp.ok) {
    let detail = `${resp.status}`;
    if (text.trim().startsWith("<")) {
      if (resp.status === 504) {
        detail = "Request timed out on the proxy/gateway (504). Please retry.";
      } else if (resp.status === 502 || resp.status === 503) {
        detail = "Research API is temporarily unavailable (502/503).";
      } else {
        detail = `HTTP ${resp.status}`;
      }
    } else {
      try {
        const body = text ? JSON.parse(text) : {};
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
      } catch {
        detail = `HTTP ${resp.status}`;
      }
    }
    throw new ApiError(resp.status, detail);
  }
  if (text.trim().startsWith("<")) {
    throw new ApiError(resp.status, "Received HTML instead of JSON from server.");
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError(resp.status, "Invalid response from the server.");
  }
}

const get = <T>(path: string, timeoutMs?: number) => request<T>(path, undefined, timeoutMs);
const post = <T>(path: string, body?: unknown, timeoutMs?: number) =>
  request<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: body !== undefined ? JSON.stringify(body) : undefined }, timeoutMs);
const put = <T>(path: string, body?: unknown, timeoutMs?: number) =>
  request<T>(path, { method: "PUT", headers: { "Content-Type": "application/json" }, body: body !== undefined ? JSON.stringify(body) : undefined }, timeoutMs);
const del = <T>(path: string, timeoutMs?: number) =>
  request<T>(path, { method: "DELETE" }, timeoutMs);

export const enc = encodeURIComponent;

export const api = {
  search: (q: string, limit = 20) => get<import("./types").SearchOut>(`/api/v1/search?q=${enc(q)}&limit=${limit}`),
  suggestions: (q: string, limit = 10) =>
    get<import("./types").SuggestionsOut>(`/api/v1/search/suggestions?q=${enc(q)}&limit=${limit}`),
  dossier: (companyId: string) => get<import("./types").DossierOut>(`/api/v1/companies/${enc(companyId)}/dossier`),
  compare: (ids: string[]) => get<import("./types").CompareOut>(`/api/v1/compare?ids=${ids.map(enc).join(",")}`),
  similar: (companyId: string, n = 5) => get<import("./types").SimilarOut>(`/api/v1/companies/${enc(companyId)}/similar?n=${n}`),
  sectorSnapshot: (sheet: string, currency: "USD" | "CAD") =>
    get<import("./types").SectorSnapshotOut>(`/api/v1/sectors/${enc(sheet)}/snapshot?currency=${currency}`),
  rankings: (currency: "USD" | "CAD", limit = 10) =>
    get<RankingsOut>(`/api/v1/rankings?scope=seed&currency=${currency}&limit=${limit}`),
  sectors: () => get<SectorsOut>(`/api/v1/sectors`),
  sectorRankings: (sheet: string, currency: "ALL" | "USD" | "CAD", limit = 500) =>
    get<SectorRankingsOut>(`/api/v1/sectors/${enc(sheet)}/rankings?currency=${currency}&limit=${limit}`),
  jobs: () => get<JobsListOut>(`/api/v1/jobs?limit=20`),
  job: (id: string) => get<JobOut>(`/api/v1/jobs/${enc(id)}`),
  researchMeta: () => get<import("./types").ResearchMetaOut>(`/api/v1/research/meta`),
  ingest: (ticker: string, refresh = false) => post<import("./types").IngestOut>("/api/v1/tickers/ingest", { ticker, refresh }),
  recomputeCompany: (companyId: string) =>
    post<{ scored: number }>("/api/v1/scores/recompute", { universe: "company_id", company_id: companyId }),
  narrate: (endpoint: string) => post<NarrationResult>(endpoint, undefined, 180_000),
  penman: (companyId: string) => get<unknown>(`/api/v1/companies/${enc(companyId)}/penman`),
  schilit: (companyId: string) => get<unknown>(`/api/v1/companies/${enc(companyId)}/schilit`),
  graham: (companyId: string) => get<unknown>(`/api/v1/companies/${enc(companyId)}/graham`),
  practitioner: (companyId: string) =>
    get<import("./types").PractitionerOut>(`/api/v1/companies/${enc(companyId)}/practitioner`),
  commonSize: (companyId: string, years = 5) =>
    get<import("./types").CommonSizeOut>(`/api/v1/companies/${enc(companyId)}/financials/common-size?years=${years}`),
  statements: (companyId: string, limit = 10) =>
    get<{ company_id: string; count: number; items: Record<string, unknown>[] }>(`/api/v1/companies/${enc(companyId)}/statements?limit=${limit}`),
  derivedMetrics: (companyId: string, limit = 10) =>
    get<{ company_id: string; count: number; items: Record<string, unknown>[] }>(`/api/v1/companies/${enc(companyId)}/derived-metrics?limit=${limit}`),
  benchmarks: (companyId: string) =>
    get<{ company_id: string; currency: string; count: number; items: Record<string, unknown>[] }>(`/api/v1/companies/${enc(companyId)}/benchmarks`),
  dossierQuality: (companyId: string) => get<Record<string, unknown>>(`/api/v1/companies/${enc(companyId)}/quality`),
  refreshCompanyPrice: (companyId: string) =>
    post<{ job_id: string; status: string }>(`/api/v1/jobs/backfill`, {
      mode: "company",
      company_id: companyId,
      refresh: true,
    }),
  swotResearch: (companyId: string) => post<import("./types").SwotOut>(`/api/v1/companies/${enc(companyId)}/research`, undefined, 180_000),
  forensics: (companyId: string) => get<import("./types").ForensicsOut>(`/api/v1/companies/${enc(companyId)}/forensics`),
  valuation: (companyId: string) => get<import("./types").ValuationOut>(`/api/v1/companies/${enc(companyId)}/valuation`),
  deleteCompany: (companyId: string, hard = false) =>
    del<import("./types").DeleteCompanyOut>(`/api/v1/companies/${enc(companyId)}${hard ? "?hard=true" : ""}`),
  restoreCompany: (companyId: string) =>
    post<import("./types").DeleteCompanyOut>(`/api/v1/companies/${enc(companyId)}/restore`),
  screenerPresets: () => get<import("./types").ScreenerPreset[]>("/api/v1/screener/presets"),
  runScreener: (criteria: Record<string, unknown>) =>
    post<import("./types").ScreenerResult>("/api/v1/screener/run", criteria),
  screen: (params?: Record<string, string | number | boolean | null | undefined>) => {
    const q = new URLSearchParams();
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== "") {
          q.set(k, String(v));
        }
      }
    }
    return get<import("./types").ScreenOut>(`/api/v1/screen?${q.toString()}`);
  },
  etfTopCohorts: () => get<import("./types").ETFCohortsOut>("/api/v1/etfs/top-cohorts"),
  chat: (
    companyId: string,
    messages: Array<{ role: "user" | "assistant"; content: string }>
  ) =>
    post<{ role: string; content: string; model_used: string; disclaimer: string }>(
      `/api/v1/companies/${enc(companyId)}/chat`,
      { messages },
      60_000 // 60s for LLM responses
    ),
  piotroski: (companyId: string) =>
    get<import("./types").PiotroskiOut>(`/api/v1/companies/${enc(companyId)}/piotroski`),
  dupont: (companyId: string) =>
    get<import("./types").DuPontOut>(`/api/v1/companies/${enc(companyId)}/dupont`),
  peerMatrix: (companyId: string) =>
    get<import("./types").PeerMatrixOut>(`/api/v1/companies/${enc(companyId)}/peer-matrix`),
  pillarDrilldown: (companyId: string) =>
    get<import("./types").PillarDrilldownOut>(`/api/v1/companies/${enc(companyId)}/pillar-drilldown`),
  inspectRatio: (companyId: string, ratioName: string) =>
    get<import("./types").RatioInspectOut>(`/api/v1/companies/${enc(companyId)}/ratios/${enc(ratioName)}/inspect`),
  bearCase: (companyId: string) =>
    get<import("./types").BearCaseOut>(`/api/v1/companies/${enc(companyId)}/bear-case`),
  coverageHealth: () =>
    get<import("./types").CoverageHealthOut>("/api/v1/coverage/health"),
  factorEvidence: () =>
    get<import("./types").FactorEvidenceOut>("/api/v1/factors/evidence"),
  screenExportUrl: (params?: Record<string, string | number | boolean | null | undefined>) => {
    const q = new URLSearchParams();
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== "") {
          q.set(k, String(v));
        }
      }
    }
    return `/api/v1/screen/export?${q.toString()}`;
  },
  watchlistDigest: (companyIds?: string[]) =>
    post<import("./types").WatchlistDigestResponse>("/api/v1/watchlist/digest", { company_ids: companyIds }),
  watchlistDeltas: (companyIds?: string[]) => {
    const q = companyIds && companyIds.length ? `?company_ids=${companyIds.map(enc).join(",")}` : "";
    return get<import("./types").WatchlistDeltasResponse>(`/api/v1/watchlist/deltas${q}`);
  },
  savePreset: (preset: { name: string; criteria: Record<string, unknown>; auto_run?: boolean }) =>
    post<import("./types").ScreenerPresetItem>("/api/v1/screener/presets", preset),
  deletePreset: (id: string) =>
    del<{ ok: boolean; id: string }>(`/api/v1/screener/presets/${enc(id)}`),
  setPresetAutoRun: (id: string, autoRun: boolean) =>
    put<{ ok: boolean; id: string; auto_run: boolean }>(`/api/v1/screener/presets/${enc(id)}/auto-run`, { auto_run: autoRun }),
  // Wave 3 Forensics & Restatements
  forensicsSummary: (companyId: string) =>
    get<import("./types").ForensicsSummaryOut>(`/api/v1/companies/${enc(companyId)}/forensics/summary`),
  forensicsBenford: (companyId: string) =>
    get<import("./types").BenfordOut>(`/api/v1/companies/${enc(companyId)}/forensics/benford`),
  forensicsTimeline: (companyId: string) =>
    get<import("./types").ForensicsTimelineOut>(`/api/v1/companies/${enc(companyId)}/forensics/timeline`),
  forensicsRank: (ids: string[]) =>
    get<import("./types").ForensicsRankOut>(`/api/v1/forensics/rank?ids=${ids.map(enc).join(",")}`),
  restatements: (companyId: string) =>
    get<import("./types").RestatementsOut>(`/api/v1/companies/${enc(companyId)}/restatements`),
  trajectory: (companyId: string) =>
    get<import("./types").TrajectoryOut>(`/api/v1/companies/${enc(companyId)}/trajectory`),
  workingCapital: (companyId: string) =>
    get<import("./types").WorkingCapitalOut>(`/api/v1/companies/${enc(companyId)}/working-capital`),
  goodwillRisk: (companyId: string) =>
    get<import("./types").GoodwillRiskOut>(`/api/v1/companies/${enc(companyId)}/goodwill-risk`),
  dilution: (companyId: string) =>
    get<import("./types").DilutionOut>(`/api/v1/companies/${enc(companyId)}/dilution`),
  // Wave 4 Valuation Suite
  requestEPV: (companyId: string, wacc?: number) =>
    get<unknown>(`/api/v1/companies/${enc(companyId)}/valuation/epv${wacc != null ? `?wacc=${wacc}` : ""}`),
  requestDDM: (companyId: string, wacc?: number) =>
    get<unknown>(`/api/v1/companies/${enc(companyId)}/valuation/ddm${wacc != null ? `?wacc=${wacc}` : ""}`),
  requestResidual: (companyId: string, wacc?: number) =>
    get<unknown>(`/api/v1/companies/${enc(companyId)}/valuation/residual-income${wacc != null ? `?wacc=${wacc}` : ""}`),
  requestGuided: (companyId: string, params?: Record<string, number | string | null | undefined>) => {
    const q = new URLSearchParams();
    if (params) for (const [k, v] of Object.entries(params)) if (v != null) q.set(k, String(v));
    const qs = q.toString();
    return get<unknown>(`/api/v1/companies/${enc(companyId)}/valuation/guided${qs ? `?${qs}` : ""}`);
  },
  requestDecomposition: (companyId: string) =>
    get<unknown>(`/api/v1/companies/${enc(companyId)}/valuation/decomposition`),
  requestNormalized: (companyId: string) =>
    get<unknown>(`/api/v1/companies/${enc(companyId)}/valuation/normalized`),
  valuationRank: (ids: string[]) =>
    get<unknown>(`/api/v1/valuation/rank?ids=${ids.map(enc).join(",")}`),
  valuationCompare: (ids: string[]) =>
    get<unknown>(`/api/v1/valuation/compare?ids=${ids.map(enc).join(",")}`),
  // Wave 5 Portfolio & Alerts
  portfolioAccounts: () => get<unknown>("/api/v1/portfolio/accounts"),
  createPortfolioAccount: (body: { name: string; account_type: string; currency: string }) =>
    post<unknown>("/api/v1/portfolio/accounts", body),
  portfolioHoldings: (accountId?: string) =>
    get<unknown>(`/api/v1/portfolio/holdings${accountId ? `?account_id=${enc(accountId)}` : ""}`),
  portfolioSummary: (accountId?: string) =>
    get<unknown>(`/api/v1/portfolio/summary${accountId ? `?account_id=${enc(accountId)}` : ""}`),
  portfolioDividends: (accountId?: string) =>
    get<unknown>(`/api/v1/portfolio/dividends${accountId ? `?account_id=${enc(accountId)}` : ""}`),
  portfolioRebalance: (accountId?: string) =>
    get<unknown>(`/api/v1/portfolio/rebalance${accountId ? `?account_id=${enc(accountId)}` : ""}`),
  portfolioTaxLots: (accountId?: string) =>
    get<unknown>(`/api/v1/portfolio/tax-lots${accountId ? `?account_id=${enc(accountId)}` : ""}`),
  portfolioHeatmap: (accountId?: string) =>
    get<unknown>(`/api/v1/portfolio/forensic-heatmap${accountId ? `?account_id=${enc(accountId)}` : ""}`),
  createPortfolioTransaction: (body: { account_id: string; company_id: string; txn_type: string; quantity: number; price_per_share: number; txn_date: string; currency?: string; fees?: number; notes?: string }) =>
    post<unknown>("/api/v1/portfolio/transactions", body),
  journalEntries: (companyId?: string) =>
    get<unknown>(`/api/v1/portfolio/journal${companyId ? `?company_id=${enc(companyId)}` : ""}`),
  createJournalEntry: (body: { company_id: string; account_id?: string; purchase_date?: string; confidence?: number; strategy_tag?: string; thesis?: string; kill_conditions?: string }) =>
    post<unknown>("/api/v1/portfolio/journal", body),
  journalCalibration: () => get<unknown>("/api/v1/portfolio/journal/calibration"),
  alertRules: (companyId?: string) =>
    get<unknown>(`/api/v1/alerts/rules${companyId ? `?company_id=${enc(companyId)}` : ""}`),
  createAlertRule: (body: { company_id?: string; rule_type: string; params?: Record<string, unknown>; enabled?: boolean }) =>
    post<unknown>("/api/v1/alerts/rules", body),
  evaluateAlerts: (companyIds?: string[]) => {
    const qs = companyIds && companyIds.length ? `?company_ids=${companyIds.map(enc).join(",")}` : "";
    return post<unknown>(`/api/v1/alerts/evaluate${qs}`, {});
  },
  alertsCalendar: (daysAhead = 30) => get<unknown>(`/api/v1/alerts/calendar?days_ahead=${daysAhead}`),
  alertsHeartbeat: () => get<unknown>("/api/v1/alerts/heartbeat"),
  alertsEvents: () => get<unknown>("/api/v1/alerts/events"),
  requestMemo: (companyId: string) => get<unknown>(`/api/v1/companies/${enc(companyId)}/export/memo?format=json`),
  requestRawDump: (companyId: string) => get<unknown>(`/api/v1/companies/${enc(companyId)}/export/raw`),
  requestCanadianTax: (companyId: string) => get<unknown>(`/api/v1/canada/companies/${enc(companyId)}/tax-placement`),
  requestCanadianMetrics: (companyId: string) => get<unknown>(`/api/v1/canada/companies/${enc(companyId)}/canadian-metrics`),
  requestDualListed: (companyId: string) => get<unknown>(`/api/v1/canada/companies/${enc(companyId)}/dual-listed`),
  requestInsiders: (companyId: string, pureMode?: boolean) => get<unknown>(`/api/v1/companies/${enc(companyId)}/insiders${pureMode ? "?pure_mode=true" : ""}`),
  requestInsiderCluster: (ids: string[]) => get<unknown>(`/api/v1/insiders/cluster?ids=${ids.map(enc).join(",")}`),
  requestTechnicals: (companyId: string) => get<unknown>(`/api/v1/companies/${enc(companyId)}/technicals`),
  // Wave 8 Capstone
  requestCurriculumModules: () => get<unknown>("/api/v1/curriculum/modules"),
  requestCaseStudies: () => get<unknown>("/api/v1/curriculum/case-studies"),
  requestFlashcards: (moduleId?: string) => get<unknown>(`/api/v1/curriculum/flashcards${moduleId ? `?module_id=${enc(moduleId)}` : ""}`),
  requestCurriculumQuiz: (moduleId: string) => get<unknown>(`/api/v1/curriculum/quiz/${enc(moduleId)}`),
  request10KReader: (companyId: string) => get<unknown>(`/api/v1/curriculum/10k-reader/${enc(companyId)}`),
  requestSectorRotation: (currency: string = "ALL") => get<unknown>(`/api/v1/sectors/rotation?currency=${enc(currency)}`),
  requestSectorHistogram: (sheet: string, currency: string = "ALL", metric: string = "composite") => get<unknown>(`/api/v1/sectors/${enc(sheet)}/histogram?currency=${enc(currency)}&metric=${enc(metric)}`),
  requestCycleTag: (sheet: string) => get<unknown>(`/api/v1/sectors/${enc(sheet)}/cycle-tag`),
  requestBarrier: (sheet: string, currency: string = "USD") => get<unknown>(`/api/v1/sectors/${enc(sheet)}/barrier?currency=${enc(currency)}`),
  requestFactorDecay: () => get<unknown>("/api/v1/backtesting/factor-decay"),
  requestSurvivorship: () => get<unknown>("/api/v1/backtesting/survivorship"),
  requestSignalFollowThrough: () => get<unknown>("/api/v1/backtesting/signal-follow-through"),
  checkOverfitting: (criteria: Record<string, unknown>) => post<unknown>("/api/v1/backtesting/overfitting-check", criteria),
  requestBackups: () => get<unknown>("/api/v1/ops/backups"),
  createBackup: () => post<unknown>("/api/v1/ops/backup"),
  requestIntegrity: () => get<unknown>("/api/v1/ops/integrity"),
  requestSeedChecksum: () => get<unknown>("/api/v1/ops/seed-checksum"),
  requestDiagnostics: () => get<unknown>("/api/v1/ops/diagnostics"),
  vacuum: () => post<unknown>("/api/v1/ops/vacuum"),
  requestModelRisk: () => get<unknown>("/api/v1/governance/model-risk"),
  requestCanonMap: () => get<unknown>("/api/v1/governance/canon-map"),
  requestDiffMatrix: () => get<unknown>("/api/v1/governance/diff-matrix"),
};

