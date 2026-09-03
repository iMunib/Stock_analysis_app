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
const del = <T>(path: string, timeoutMs?: number) =>
  request<T>(path, { method: "DELETE" }, timeoutMs);

export const enc = encodeURIComponent;

export const api = {
  search: (q: string, limit = 20) => get<import("./types").SearchOut>(`/api/v1/search?q=${enc(q)}&limit=${limit}`),
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
};
