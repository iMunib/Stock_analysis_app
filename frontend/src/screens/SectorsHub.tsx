import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { CurrencyView, SectorsOut } from "../api/types";
import { ErrorBanner, Spinner } from "../components/ui";
import { gicsSheetParam, sectorCardKey } from "../lib/nav";
import { Page } from "../components/layout";
import { CompositeGauge } from "../components/viz";

const VIEWS: CurrencyView[] = ["ALL", "USD", "CAD"];

export default function SectorsHub() {
  const [view, setView] = useState<CurrencyView>("ALL");
  const [data, setData] = useState<SectorsOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [medians, setMedians] = useState<Record<string, number | null>>({});
  const [loadingMedians, setLoadingMedians] = useState(false);

  const load = () => {
    setError(null);
    api.sectors().then(setData).catch((e: ApiError) => setError(e.message));
  };

  useEffect(load, []);

  // Populate medians immediately from precomputed sector metrics (instant zero-lag barometer display)
  useEffect(() => {
    if (!data) return;

    const m: Record<string, number | null> = {};
    for (const s of data.custom_industries) {
      const k = sectorCardKey("custom", s.name);
      m[k] =
        view === "ALL"
          ? (s.median_composite_all ?? s.median_composite_usd ?? s.median_composite_cad ?? null)
          : view === "USD"
          ? (s.median_composite_usd ?? null)
          : (s.median_composite_cad ?? null);
    }
    for (const s of data.gics_sectors) {
      const k = sectorCardKey("gics", s.name);
      m[k] =
        view === "ALL"
          ? (s.median_composite_all ?? s.median_composite_usd ?? s.median_composite_cad ?? null)
          : view === "USD"
          ? (s.median_composite_usd ?? null)
          : (s.median_composite_cad ?? null);
    }
    setMedians(m);
    setLoadingMedians(false);
  }, [data, view]);

  const viewControls = (
    <div className="flex items-center gap-2" role="group" aria-label="Currency view">
      <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2">View</span>
      <div className="flex rounded-chip border border-border bg-bg-0 p-0.5">
        {VIEWS.map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            aria-pressed={view === v}
            className={`rounded-chip px-3 py-1 font-mono text-xs transition-colors ${
              view === v ? "bg-bg-1 text-accent font-medium shadow-sm" : "text-ink-1 hover:text-ink-0"
            }`}
          >
            {v}
          </button>
        ))}
      </div>
      {view === "ALL" && (
        <span className="ml-2 text-xs text-ink-2 font-mono">
          score-only view - money medians stay split per currency
        </span>
      )}
    </div>
  );

  return (
    <Page
      title="Sectors"
      description="Compare sector benchmarks, median composites, and valuation distributions."
      actions={viewControls}
    >
      {error && <ErrorBanner message={error} onRetry={load} />}
      {!data && !error && <Spinner label="Loading sectors…" />}

      {data && (
        <div className="space-y-8">
          <SectorGroup
            title="Custom industries"
            groups={data.custom_industries.map((s) => ({
              key: sectorCardKey("custom", s.name),
              name: s.name,
              count: view === "CAD" ? s.cad : view === "USD" ? s.usd : s.usd + s.cad,
              countLabel: view === "ALL" ? `${s.usd} USD / ${s.cad} CAD` : `${s.count} names`,
              sheet: s.name,
              median: medians[sectorCardKey("custom", s.name)],
            }))}
            currency={view}
            loadingMedians={loadingMedians}
          />
          <SectorGroup
            title="GICS sectors"
            groups={data.gics_sectors.map((s) => ({
              key: sectorCardKey("gics", s.name),
              name: s.name,
              count: view === "CAD" ? s.cad : view === "USD" ? s.usd : s.usd + s.cad,
              countLabel: view === "ALL" ? `${s.usd} USD / ${s.cad} CAD` : `${s.count} names`,
              sheet: gicsSheetParam(s.name),
              median: medians[sectorCardKey("gics", s.name)],
            }))}
            currency={view}
            loadingMedians={loadingMedians}
          />
        </div>
      )}
    </Page>
  );
}

function SectorGroup({
  title,
  groups,
  currency,
  loadingMedians,
}: {
  title: string;
  groups: { key: string; name: string; count: number; countLabel: string; sheet: string; median: number | null | undefined }[];
  currency: CurrencyView;
  loadingMedians: boolean;
}) {
  return (
    <section aria-label={title} className="space-y-3">
      <div className="flex items-center justify-between border-b border-border pb-2">
        <h2 className="font-heading text-lg font-semibold text-ink-0">{title}</h2>
        <span className="font-mono text-xs text-ink-2">{groups.length} peer groups</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map((g) => (
          <Link
            key={g.key}
            to={`/sectors/${enc(g.sheet)}?currency=${currency}`}
            className="group rounded-card border border-border bg-bg-1 p-4 transition-all shadow-card hover:border-accent/60 hover:bg-bg-2 flex items-center justify-between gap-3"
            aria-label={`${g.name} sector with ${g.count} companies`}
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-semibold text-ink-0 group-hover:text-accent transition-colors truncate">
                  {g.name} <span className="font-mono text-[11px] font-normal text-ink-2">({g.count} companies)</span>
                </span>
              </div>
              <p className="mt-1 font-mono text-[11px] text-ink-2">{g.countLabel} · {g.count} total constituents</p>
              <div className="mt-2 font-mono text-xs text-ink-1 flex items-center gap-1.5">
                <span className="text-ink-2">Median score:</span>
                {g.median === undefined && loadingMedians ? (
                  <span className="text-ink-2 animate-pulse">Not reported in filing</span>
                ) : g.median == null ? (
                  <span className="text-ink-2">Under review</span>
                ) : (
                  <span className="text-accent font-semibold">{g.median.toFixed(1)}</span>
                )}
              </div>
            </div>
            <div className="shrink-0">
              <CompositeGauge value={g.median} size="sm" showLabel={false} />
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}