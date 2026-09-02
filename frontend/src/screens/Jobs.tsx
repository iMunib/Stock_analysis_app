import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { JobsListOut } from "../api/types";
import { ErrorBanner, Spinner } from "../components/ui";

const STATUS_COLOR: Record<string, string> = {
  queued: "text-info border-info/40",
  running: "text-mid border-mid/40",
  succeeded: "text-good border-good/40",
  failed: "text-bad border-bad/40",
  cancelled: "text-dim border-line2",
};

export default function Jobs() {
  const [jobs, setJobs] = useState<JobsListOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    api.jobs().then(setJobs).catch((e: ApiError) => setError(e.message));
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  if (error) return <ErrorBanner message={error} onRetry={load} />;
  if (!jobs) return <Spinner label="Loading jobs…" />;

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl tracking-tight">Jobs</h1>
      {jobs.items.length === 0 ? (
        <p className="text-sm text-fog">No jobs yet. Backfills are enqueued from the API (POST /api/v1/jobs/backfill).</p>
      ) : (
        <ul className="divide-y divide-line rounded-md border border-line bg-panel">
          {jobs.items.map((j) => (
            <li key={j.id} className="px-4 py-3 space-y-1">
              <div className="flex items-center justify-between gap-4">
                <span className="font-mono text-xs text-paper">{j.id.slice(0, 12)}…</span>
                <span className={`rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${STATUS_COLOR[j.status] ?? "text-dim border-line2"}`}>
                  {j.status}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-fog">
                <span className="font-mono">{j.kind}</span>
                <span>
                  progress {j.progress_done}/{j.progress_total}
                </span>
                {j.error && <span className="text-bad">· {j.error}</span>}
              </div>
              {j.progress_total > 0 && (
                <div className="h-1.5 w-full rounded bg-ink">
                  <div
                    className="h-1.5 rounded bg-gold"
                    style={{ width: `${Math.round((j.progress_done / Math.max(1, j.progress_total)) * 100)}%` }}
                  />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
