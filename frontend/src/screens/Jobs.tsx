import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { JobsListOut } from "../api/types";
import { ErrorBanner, Spinner } from "../components/ui";
import { Card, Chip, Page } from "../components/layout";
import { EmptyState } from "../components/feedback";

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
      const resp = await fetch("/api/v1/jobs/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "sample", limit: 5 }),
      });
      if (resp.status === 202) {
        setRefreshMsg("Refresh job queued - progress appears below.");
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

  if (setupHint) {
    return (
      <Page title="Jobs">
        <div role="alert" className="rounded-card border border-warn/60 bg-warn-weak p-4 text-xs text-ink-0 font-mono">
          The jobs API (Phase 6A+) is not available at <span className="font-semibold">/api/v1/jobs</span>. Update the
          api container: <span className="font-semibold">docker compose up --build -d</span>.
        </div>
      </Page>
    );
  }

  if (error && !jobs) return <ErrorBanner message={error} onRetry={load} />;
  if (!jobs) return <Spinner label="Loading jobs…" />;

  const headerAction = (
    <button
      onClick={refreshSample}
      disabled={refreshing}
      className="rounded-card border border-accent/60 bg-accent-weak px-4 py-2 text-xs font-mono text-accent hover:bg-accent/20 disabled:opacity-40 transition-colors"
    >
      {refreshing ? "Queueing…" : "Refresh sample (5 names)"}
    </button>
  );

  return (
    <Page
      title="Jobs"
      description="Refresh pulls new fiscal years from EDGAR/Yahoo and re-scores. The owner row is never overwritten."
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
          <ul className="divide-y divide-border">
            {jobs.items.map((j) => {
              const tone =
                j.status === "succeeded"
                  ? "positive"
                  : j.status === "failed"
                    ? "negative"
                    : j.status === "running"
                      ? "warning"
                      : "info";

              const pct = Math.round((j.progress_done / Math.max(1, j.progress_total)) * 100);

              return (
                <li key={j.id} className="p-4 space-y-2 hover:bg-bg-2/30 transition-colors">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-ink-0">{j.id.slice(0, 12)}…</span>
                      <span className="font-mono text-[11px] text-ink-2">({j.kind})</span>
                    </div>
                    <Chip tone={tone} size="sm">
                      {j.status === "running" ? (
                        <span className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-warn animate-ping" />
                          <span>running</span>
                        </span>
                      ) : (
                        j.status
                      )}
                    </Chip>
                  </div>

                  <div className="flex items-center justify-between text-xs text-ink-1 font-mono">
                    <span>
                      Progress: {j.progress_done} / {j.progress_total} ({pct}%)
                    </span>
                    {j.error && <span className="text-neg font-sans">Error: {j.error}</span>}
                  </div>

                  {j.progress_total > 0 && (
                    <div className="h-2 w-full rounded-full bg-bg-0 border border-border/50 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-accent transition-all duration-500 ease-out"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </Card>
      )}
    </Page>
  );
}