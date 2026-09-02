import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { SectorSnapshotOut } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { SIGNAL_ORDER, signalTone } from "../api/visuals";
import { signalLabel } from "../api/copy";

export default function Sector() {
  const { sheet = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const currency = (params.get("currency") as "USD" | "CAD") ?? null;
  const [data, setData] = useState<SectorSnapshotOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currency !== "USD" && currency !== "CAD") {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    api
      .sectorSnapshot(sheet, currency)
      .then(setData)
      .catch((e: ApiError) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sheet, currency]);

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <nav className="text-xs text-dim" aria-label="Breadcrumb">
          <span className="font-mono">{sheet}</span>
        </nav>
        <h1 className="font-display text-3xl tracking-tight">{sheet.replace(/_/g, " ")} snapshot</h1>
        <div className="flex items-center gap-3" role="group" aria-label="Currency toggle (required)">
          <span className="font-mono text-[10px] uppercase tracking-widest text-dim">Currency</span>
          {(["USD", "CAD"] as const).map((c) => (
            <button
              key={c}
              onClick={() => setParams({ currency: c })}
              aria-pressed={currency === c}
              className={`rounded border px-3 py-1 font-mono text-xs ${
                currency === c ? "border-gold bg-gold/15 text-gold" : "border-line text-fog hover:border-line2 hover:text-paper"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
        {!currency && (
          <p className="rounded-md border border-line bg-panel px-4 py-3 text-sm text-fog">
            Choose a currency to load the snapshot. Same-industry comparisons never mix USD and CAD.
          </p>
        )}
      </header>

      {loading && <Spinner label="Loading sector snapshot…" />}
      {error && <ErrorBanner message={error} />}

      {data && !loading && (
        <div className="space-y-8">
          <section aria-label="Sector stats" className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            <Stat label="Companies" value={data.companies} />
            <Stat label="Scored" value={data.scored} />
            <Stat label="Median score" value={data.median_composite?.toFixed(1) ?? "—"} />
            <Stat label="Median PE" value={data.median_pe?.toFixed(1) ?? "—"} />
            <Stat label="Median ROE" value={data.median_roe != null ? `${(data.median_roe * 100).toFixed(1)}%` : "—"} />
          </section>

          <section aria-label="Signal histogram" className="space-y-2">
            <p className="font-mono text-xs uppercase tracking-widest text-dim">Signal histogram</p>
            <ul className="space-y-1.5 text-sm">
              {SIGNAL_ORDER.map((sig) => {
                const n = data.signal_histogram[sig] ?? 0;
                if (!n) return null;
                const tone = signalTone(sig === "score_missing" ? null : sig);
                const color = tone === "good" ? "bg-good" : tone === "mid" ? "bg-mid" : tone === "bad" ? "bg-bad" : "bg-info";
                return (
                  <li key={sig} className="flex items-center gap-3">
                    <span className="w-36 shrink-0 text-fog">{signalLabel(sig === "score_missing" ? null : sig)}</span>
                    <span className="h-3 rounded-sm" style={{ width: `${Math.max(4, (n / data.companies) * 380)}px` }}>
                      <span className={`block h-3 rounded-sm ${color}`} />
                    </span>
                    <span className="font-mono tabular-nums">{n}</span>
                  </li>
                );
              })}
            </ul>
          </section>

          <div className="grid gap-8 lg:grid-cols-2">
            <RankTable title="Top 10" rows={data.top} emptyText="No scored companies yet." />
            <RankTable title="Bottom 10" rows={data.bottom} emptyText="No scored companies yet." />
          </div>
        </div>
      )}
    </div>
  );
}

function RankTable({ title, rows, emptyText }: { title: string; rows: SectorSnapshotOut["top"]; emptyText: string }) {
  return (
    <section aria-label={title} className="space-y-3">
      <h2 className="font-display text-xl">{title}</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-fog">{emptyText}</p>
      ) : (
        <ul className="divide-y divide-line rounded-md border border-line bg-panel">
          {rows.map((r) => (
            <li key={r.company_id} className="flex items-center justify-between gap-4 px-4 py-2.5">
              <div>
                <CompanyLink companyId={r.company_id}>{r.name ?? r.company_id}</CompanyLink>
                <span className="ml-2 font-mono text-[10px] text-dim">{r.company_id}</span>
              </div>
              <div className="flex items-center gap-3">
                <Score value={r.composite} />
                <SignalBadge signal={r.signal} small />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border border-line bg-panel px-4 py-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-dim">{label}</p>
      <p className="mt-1 font-mono text-2xl tabular-nums text-paper">{value}</p>
    </div>
  );
}
