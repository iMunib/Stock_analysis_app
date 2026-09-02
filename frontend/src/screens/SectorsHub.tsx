import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { SectorsOut } from "../api/types";
import { ErrorBanner, Spinner } from "../components/ui";
import { gicsSheetParam, sectorCardKey } from "../lib/nav";
import type { CurrencyView } from "../api/types";

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

  // Batch-load medians for all cards after the sector list arrives.
  useEffect(() => {
    if (!data) return;
    setLoadingMedians(true);
    const all: { key: string; sheet: string }[] = [
      ...data.custom_industries.map((s) => ({ key: sectorCardKey("custom", s.name), sheet: s.name })),
      ...data.gics_sectors.map((s) => ({ key: sectorCardKey("gics", s.name), sheet: gicsSheetParam(s.name) })),
    ];
    let cancelled = false;
    if (view === "ALL") {
      Promise.allSettled(
        all.map((c) =>
          Promise.all([
            api.sectorSnapshot(c.sheet, "USD"),
            api.sectorSnapshot(c.sheet, "CAD"),
          ]).then(([usd, cad]) => {
            // unitless median composite across both currencies (no money blending)
            const comps = [usd.median_composite, cad.median_composite].filter((x): x is number => x != null);
            const avg = comps.length ? comps.reduce((a, b) => a + b, 0) / comps.length : null;
            return { key: c.key, median: avg };
          }),
        ),
      ).then((results) => {
        if (cancelled) return;
        const m: Record<string, number | null> = {};
        for (const r of results) if (r.status === "fulfilled") m[r.value.key] = r.value.median;
        setMedians(m);
        setLoadingMedians(false);
      });
    } else {
      Promise.allSettled(
        all.map((c) => api.sectorSnapshot(c.sheet, view).then((snap) => ({ key: c.key, median: snap.median_composite }))),
      ).then((results) => {
        if (cancelled) return;
        const m: Record<string, number | null> = {};
        for (const r of results) if (r.status === "fulfilled") m[r.value.key] = r.value.median;
        setMedians(m);
        setLoadingMedians(false);
      });
    }
    return () => {
      cancelled = true;
    };
  }, [data, view]);

  return (
    <div className="space-y-8 animate-fade-in">
      <header className="space-y-3">
        <h1 className="font-display text-3xl tracking-tight">Sectors</h1>
        <div className="flex items-center gap-2" role="group" aria-label="Currency view">
          <span className="font-mono text-[10px] uppercase tracking-widest text-dim">View</span>
          {VIEWS.map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              aria-pressed={view === v}
              className={`rounded border px-3 py-1 font-mono text-xs transition-colors ${
                view === v ? "border-gold bg-gold/15 text-gold" : "border-line text-fog hover:border-line2 hover:text-paper"
              }`}
            >
              {v}
            </button>
          ))}
          {view === "ALL" && (
            <span className="ml-2 text-xs text-dim">
              score-only view — money medians stay split per currency
            </span>
          )}
        </div>
      </header>

      {error && <ErrorBanner message={error} onRetry={load} />}
      {!data && !error && <Spinner label="Loading sectors…" />}

      {data && (
        <>
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
        </>
      )}
    </div>
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
      <h2 className="font-display text-xl">{title}</h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map((g) => (
          <Link
            key={g.key}
            to={`/sectors/${enc(g.sheet)}?currency=${currency}`}
            className="group animate-rise rounded-md border border-line bg-panel px-4 py-4 transition-colors hover:border-gold/60"
          >
            <div className="flex items-baseline justify-between gap-3">
              <span className="font-medium text-paper group-hover:text-gold transition-colors">{g.name}</span>
              <span className="font-mono text-xs text-dim">{g.countLabel}</span>
            </div>
            <div className="mt-2 font-mono text-xs text-fog">
              median score{" "}
              {g.median === undefined && loadingMedians ? (
                <span className="text-dim">…</span>
              ) : g.median == null ? (
                <span className="text-dim">—</span>
              ) : (
                <span className="text-gold">{g.median.toFixed(1)}</span>
              )}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
