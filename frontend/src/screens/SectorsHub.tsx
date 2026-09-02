import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { SectorsOut } from "../api/types";
import { ErrorBanner, Spinner } from "../components/ui";
import { gicsSheetParam, sectorCardKey } from "../lib/nav";

export default function SectorsHub() {
  const [currency, setCurrency] = useState<"USD" | "CAD">("USD");
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
    Promise.allSettled(
      all.map((c) => api.sectorSnapshot(c.sheet, currency).then((snap) => ({ key: c.key, median: snap.median_composite }))),
    ).then((results) => {
      if (cancelled) return;
      const m: Record<string, number | null> = {};
      for (const r of results) {
        if (r.status === "fulfilled") m[r.value.key] = r.value.median;
      }
      setMedians(m);
      setLoadingMedians(false);
    });
    return () => {
      cancelled = true;
    };
  }, [data, currency]);

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="font-display text-3xl tracking-tight">Sectors</h1>
        <div className="flex items-center gap-3" role="group" aria-label="Currency toggle">
          <span className="font-mono text-[10px] uppercase tracking-widest text-dim">Currency</span>
          {(["USD", "CAD"] as const).map((c) => (
            <button
              key={c}
              onClick={() => setCurrency(c)}
              aria-pressed={currency === c}
              className={`rounded border px-3 py-1 font-mono text-xs ${
                currency === c ? "border-gold bg-gold/15 text-gold" : "border-line text-fog hover:border-line2 hover:text-paper"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </header>

      {error && <ErrorBanner message={error} onRetry={load} />}
      {!data && !error && <Spinner label="Loading sectors…" />}

      {data && (
        <>
          <SectorGroup
            title="Custom industries"
            groups={data.custom_industries.map((s) => ({ key: sectorCardKey("custom", s.name), name: s.name, count: currency === "USD" ? s.usd : s.cad, sheet: s.name, median: medians[sectorCardKey("custom", s.name)] }))}
            currency={currency}
            loadingMedians={loadingMedians}
          />
          <SectorGroup
            title="GICS sectors"
            groups={data.gics_sectors.map((s) => ({ key: sectorCardKey("gics", s.name), name: s.name, count: currency === "USD" ? s.usd : s.cad, sheet: gicsSheetParam(s.name), median: medians[sectorCardKey("gics", s.name)] }))}
            currency={currency}
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
  groups: { key: string; name: string; count: number; sheet: string; median: number | null | undefined }[];
  currency: "USD" | "CAD";
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
            className="group rounded-md border border-line bg-panel px-4 py-4 transition-colors hover:border-gold/60"
          >
            <div className="flex items-baseline justify-between gap-3">
              <span className="font-medium text-paper group-hover:text-gold transition-colors">{g.name}</span>
              <span className="font-mono text-xs text-dim">{g.count} names</span>
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
