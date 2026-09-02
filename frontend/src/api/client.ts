/** API fetch wrappers with typed errors. Base: /api (proxied). */
import type {
  CompareOut,
  DossierOut,
  IngestOut,
  ResearchMetaOut,
  SearchOut,
  SectorSnapshotOut,
  SimilarOut,
} from "./types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function get<T>(path: string): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(path, { headers: { Accept: "application/json" } });
  } catch {
    throw new ApiError(0, "Cannot reach the research API. Is the api container running on port 8000?");
  }
  if (!resp.ok) {
    let detail = `${resp.status}`;
    try {
      const body = await resp.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* keep status text */
    }
    throw new ApiError(resp.status, detail);
  }
  return resp.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Cannot reach the research API. Is the api container running on port 8000?");
  }
  if (!resp.ok) {
    let detail = `${resp.status}`;
    try {
      const j = await resp.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? j);
    } catch {
      /* keep */
    }
    throw new ApiError(resp.status, detail);
  }
  return resp.json() as Promise<T>;
}

export const enc = encodeURIComponent;

export const api = {
  search: (q: string, limit = 20) => get<SearchOut>(`/api/v1/search?q=${enc(q)}&limit=${limit}`),
  dossier: (companyId: string) => get<DossierOut>(`/api/v1/companies/${enc(companyId)}/dossier`),
  compare: (ids: string[]) => get<CompareOut>(`/api/v1/compare?ids=${ids.map(enc).join(",")}`),
  similar: (companyId: string, n = 5) => get<SimilarOut>(`/api/v1/companies/${enc(companyId)}/similar?n=${n}`),
  sectorSnapshot: (sheet: string, currency: "USD" | "CAD") =>
    get<SectorSnapshotOut>(`/api/v1/sectors/${enc(sheet)}/snapshot?currency=${currency}`),
  researchMeta: () => get<ResearchMetaOut>(`/api/v1/research/meta`),
  ingest: (ticker: string) => post<IngestOut>("/api/v1/tickers/ingest", { ticker }),
  recomputeCompany: (companyId: string) => post<{ scored: number }>("/api/v1/scores/recompute", { universe: "company_id", company_id: companyId }),
};
