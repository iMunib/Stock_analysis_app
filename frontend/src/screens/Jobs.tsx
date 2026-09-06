import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { JobsListOut } from "../api/types";
import { ErrorBanner, Spinner } from "../components/ui";
import { Card, Chip, Page } from "../components/layout";
import { EmptyState } from "../components/feedback";

type Job = JobsListOut["items"][number];

function tickerFromCompanyId(companyId: string | null | undefined): string | null {
  if (!companyId) return null;
  const parts = companyId.split(":");
  return parts[1] ?? null;
}

function categoryFor(job: Job): { label: string; tone: "info" | "warning" | "positive" } {
  const kind = (job.kind ?? "").toLowerCase();
  const payload: any = (job as any).payload ?? {};
  if (kind === "ingest") return { label: "EDGAR Statement Sync", tone: "info" };
  if (kind === "backfill") {
    if (payload.mode === "company") return { label: "EDGAR Statement Sync", tone: "info" };
    return { label: "Universe Recomputation", tone: "warning" };
  }
  if (kind === "recompute") return { label: "Universe Recomputation", tone: "warning" };
  if (kind === "refresh_universe") return { label: "Sector Benchmark Cache", tone: "positive" };
  return { label: job.kind ?? "Job", tone: "info" };
}

function actionName(job: Job): string {
  const ticker = tickerFromCompanyId((job as any).company_id ?? (job as any).payload?.company_id);
  const kind = (job.kind ?? "").toLowerCase();
  const payload: any = (job as any).payload ?? {};
  if (kind === "ingest" && ticker) return `Annual Financial Ingest: ${ticker} (${(job as any).company_id})`;
  if (kind === "ingest") return "Annual Financial Ingest";
  if (kind === "backfill") {
    if (payload.company_id) {
      const t = tickerFromCompanyId(payload.company_id) ?? payload.company_id;
      return `Price & Recompute: ${t}`;
    }
    if (payload.mode === "sample") return `Universe Recomputation: Sample (${payload.limit ?? 5} names)`;
    if (payload.mode === "all") return "Universe Recomputation: Full Universe";
    return `Backfill: ${payload.mode ?? "sample"}`;
  }
  if (kind === "recompute") {
    const cid = payload.company_id ?? (job as any).company_id;
    if (cid) return `Universe Recomputation: ${tickerFromCompanyId(cid) ?? cid}`;
    return "Universe Recomputation";
  }
  if (kind === "refresh_universe") return "Sector Benchmark Cache: Refresh";
  return job.message ?? job.kind ?? "Research Job";
}

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  } catch {
    return iso;
  }
}

function durationSec(job: Job): string {
  const start = (job as any).started_at ?? (job as any).created_at;
  const end = (job as any).finished_at ?? (job as any).started_at ?? (job as any).created_at;
  if (!start || !end) return "—";
  try {
    const s = new Date(start).getTime();
    const e = new Date(end).getTime();
    const sec = Math.max(0, (e - s) / 1000);
    if (sec < 60) return `${sec.toFixed(1)}s`;
    const m = Math.floor(sec / 60);
    const r = (sec % 60).toFixed(0);
    return `${m}m ${r}s`;
  } catch {
    return "—";
  }
}

function statusBadge(status: string): { label: string; tone: "positive" | "warning" | "negative" | "info" } {
  const s = status.toLowerCase();
  if (s === "succeeded" || s === "completed" || s === "done") return { label: "COMPLETED", tone: "positive" };
  if (s === "running" || s === "queued") return { label: s === "queued" ? "QUEUED" : "PROCESSING", tone: "warning" };
  if (s === "failed" || s === "error") return { label: "FAILED", tone: "negative" };
  return { label: s.toUpperCase(), tone: "info" };
}

export default function Jobs() {
  const [jobs, setJobs] = useState<JobsListOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [setupHint, setSetupHint] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  const load = () => {
    api.jobs().then(setJobs).catch((e: ApiError) => {
      setError(e.message);
      if (e.status === 404) setSetupHint(true);
    });
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  const refreshSample = async () => {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const resp = await fetch("/api/v1/jobs/backfill", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "sample", limit: 5 }),
      });
      if (resp.status === 202) {
        setRefreshMsg("Refresh job queued — progress appears below.");
        load();
      } else if (resp.status === 409) {
        setRefreshMsg("A refresh job is already queued or running.");
      } else {
        const body = await resp.json().catch(() => ({}));
        setRefreshMsg(`Could not queue refresh: ${resp.status} ${JSON.stringify(body).slice(0, 120)}`);
      }
    } catch {
      setRefreshMsg("Could not reach the API.");
    } finally {
      setRefreshing(false);
    }
  };

  const headerAction = (
    <button
      onClick={refreshSample}
      disabled={refreshing}
      className="rounded-card border border-accent/60 bg-accent-weak px-4 py-2 text-xs font-mono text-accent hover:bg-accent/20 disabled:opacity-40 transition-colors"
    >
      {refreshing ? "Queueing…" : "Refresh sample (5 names)"}
    </button>
  );

  if (setupHint) {
    return (
      <Page title="Jobs">
        <div role="alert" className="rounded-card border border-warn/60 bg-warn-weak p-4 text-xs text-ink-0 font-mono">
          The jobs API (Phase 6A+) is not available at <span className="font-semibold">/api/v1/jobs</span>. Update the api container: <span className="font-semibold">docker compose up --build -d</span>.
        </div>
      </Page>
    );
  }

  if (error && !jobs) return <ErrorBanner message={error} onRetry={load} />;
  if (!jobs) return <Spinner label="Loading jobs…" />;

  return (
    <Page
      title="Operations Telemetry — Jobs Console"
      description="Institutional operations log: EDGAR syncs, recomputations, and benchmark caches. Every duration and record count is auditable."
      actions={headerAction}
    >
      {refreshMsg && (
        <p role="status" className="rounded-card border border-info/40 bg-info-weak px-4 py-2 text-xs font-mono text-info">
          {refreshMsg}
        </p>
      )}

      {jobs.items.length === 0 ? (
        <EmptyState
          title="No jobs yet"
          body="No background ingest or refresh jobs have run yet. Backfills are enqueued from the API (POST /api/v1/jobs/backfill)."
        />
      ) : (
        <Card padding="none" className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs" role="table" aria-label="Jobs telemetry">
              <thead className="sticky top-0 z-10" style={{ backgroundColor: "var(--bg-0)", borderBottom: "2px solid var(--border-subtle)" }}>
                <tr className="font-mono text-[10px] uppercase tracking-wider text-ink-2">
                  <th className="px-3 py-2.5 text-left min-w-[280px]" style={{ backgroundColor: "var(--bg-0)" }}>Action</th>
                  <th className="px-3 py-2.5 text-center min-w-[90px]" style={{ backgroundColor: "var(--bg-0)" }}>Company</th>
                  <th className="px-3 py-2.5 text-center min-w-[160px]" style={{ backgroundColor: "var(--bg-0)" }}>Category</th>
                  <th className="px-3 py-2.5 text-left min-w-[160px]" style={{ backgroundColor: "var(--bg-0)" }}>Timestamp</th>
                  <th className="px-3 py-2.5 text-right min-w-[80px] font-mono tabular-nums" style={{ backgroundColor: "var(--bg-0)" }}>Duration</th>
                  <th className="px-3 py-2.5 text-right min-w-[110px] font-mono tabular-nums" style={{ backgroundColor: "var(--bg-0)" }}>Records</th>
                  <th className="px-3 py-2.5 text-center min-w-[120px]" style={{ backgroundColor: "var(--bg-0)" }}>Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {jobs.items.map((j: any) => {
                  const cat = categoryFor(j);
                  const act = actionName(j);
                  const badge = statusBadge(j.status);
                  const ticker = tickerFromCompanyId(j.company_id ?? j.payload?.company_id);
                  const pct = j.progress_total ? Math.round((j.progress_done / Math.max(1, j.progress_total)) * 100) : 0;
                  const humanError = j.error ? String(j.error).replace(/^[^:]+:\s*/, "").slice(0, 180) : null;
                  return (
                    <tr key={j.id} className="hover:bg-bg-2/30 transition-colors">
                      <td className="px-3 py-2.5 text-left">
                        <span className="block font-semibold text-ink-0 leading-tight">{act}</span>
                        <span className="block font-mono text-[11px] text-ink-2 truncate max-w-[320px]" title={j.message ?? ""}>{j.message ?? j.step ?? "—"}</span>
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        {ticker ? (
                          <Link
                            to={`/c/${encodeURIComponent(j.company_id ?? j.payload?.company_id ?? "")}`}
                            className="inline-flex items-center rounded border border-accent/30 bg-accent-weak px-2 py-0.5 font-mono text-xs font-semibold text-accent hover:bg-accent hover:text-bg-0 transition-colors"
                          >
                            {ticker}
                          </Link>
                        ) : (
                          <span className="font-mono text-xs text-ink-2">—</span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <Chip tone={cat.tone} size="sm">{cat.label}</Chip>
                      </td>
                      <td className="px-3 py-2.5 text-left font-mono text-xs text-ink-1">{formatTimestamp(j.created_at)}</td>
                      <td className="px-3 py-2.5 text-right font-mono tabular-nums text-xs text-ink-1">{durationSec(j)}</td>
                      <td className="px-3 py-2.5 text-right font-mono tabular-nums text-xs text-ink-1">
                        {j.progress_total ? `${j.progress_done} / ${j.progress_total} (${pct}%)` : `${j.progress_done} records`}
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <Chip tone={badge.tone} size="sm">
                          {badge.label === "PROCESSING" ? (
                            <span className="inline-flex items-center gap-1.5">
                              <span className="h-1.5 w-1.5 rounded-full bg-warn animate-pulse" aria-hidden="true" />
                              <span>{badge.label}</span>
                            </span>
                          ) : (
                            badge.label
                          )}
                        </Chip>
                        {j.error && (
                          <span className="mt-1 block font-mono text-[11px] leading-tight text-neg" title={j.error}>{humanError}</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="border-t border-border bg-bg-2/40 px-3 py-2 font-mono text-[11px] text-ink-2 flex items-center justify-between">
            <span>{jobs.items.length} jobs · newest first · auto-refresh 5s</span>
            <span>Local SQLite WAL · No paid APIs in v1</span>
          </div>
        </Card>
      )}
    </Page>
  );
}
