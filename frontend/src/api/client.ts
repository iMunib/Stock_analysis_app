import type {
  JobsListOut,
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  let resp: Response;
  try {
    resp = await fetch(path, { ...init, signal: ctrl.signal, headers: { Accept: "application/json", ...(init?.headers ?? {}) } });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ApiError(0, `Request timed out after ${TIMEOUT_MS / 1000}s. Is the api container running?`);
    }
    throw new ApiError(0, "Cannot reach the research API. Is the api container running on port 8000?");
  } finally {
    clearTimeout(timer);
  }
  const text = await resp.text().catch(() => "");
  if (!resp.ok) {
    let detail = `${resp.status}`;
    try {
      const body = text ? JSON.parse(text) : {};
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      detail = `HTTP ${resp.status}`;
    }
    throw new ApiError(resp.status, detail);
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError(resp.status, "Invalid response from the server.");
  }
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

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
  researchMeta: () => get<import("./types").ResearchMetaOut>(`/api/v1/research/meta`),
  ingest: (ticker: string) => post<import("./types").IngestOut>("/api/v1/tickers/ingest", { ticker }),
  recomputeCompany: (companyId: string) =>
    post<{ scored: number }>("/api/v1/scores/recompute", { universe: "company_id", company_id: companyId }),
};
