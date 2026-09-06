import { useEffect, useId, useState } from "react";
import { api } from "../api/client";
import { Card, Page, Chip } from "../components/layout";

function formatPercent(value: unknown): string {
  const n = typeof value === "number" ? value : parseFloat(String(value ?? ""));
  if (Number.isNaN(n)) return "Not reported in filing";
  // raw stored as 0.0677 -> 6.77%
  const pct = Math.abs(n) <= 1 ? n * 100 : n;
  return `${pct.toFixed(2)}%`;
}

function formatDelta(delta: number | null | undefined): { text: string; tone: "pos" | "neg" | "neutral"; label: string } {
  if (delta == null || Number.isNaN(delta)) return { text: "0.00", tone: "neutral", label: "Flat" };
  if (delta > 0) return { text: `+${delta.toFixed(2)}`, tone: "pos", label: "Expansion" };
  if (delta < 0) return { text: delta.toFixed(2), tone: "neg", label: "Compression" };
  return { text: "0.00", tone: "neutral", label: "Flat" };
}

export default function SectorRotation() {
  const [currency, setCurrency] = useState<"ALL" | "USD" | "CAD">("ALL");
  const [data, setData] = useState<any>(null);
  const [hist, setHist] = useState<any>(null);
  const [cycle, setCycle] = useState<any>(null);
  const [barrier, setBarrier] = useState<any>(null);
  const [selected, setSelected] = useState<string>("Information Technology");

  const rawId = useId().replace(/:/g, "_");
  const barGradId = `histBarGrad_${rawId}`;

  useEffect(() => {
    api.requestSectorRotation(currency).then(setData).catch(() => {});
  }, [currency]);

  useEffect(() => {
    api.requestSectorHistogram(selected, currency).then(setHist).catch(() => {});
    api.requestCycleTag(selected).then(setCycle).catch(() => {});
    api.requestBarrier(selected, currency === "ALL" ? "USD" : currency).then(setBarrier).catch(() => {});
  }, [selected, currency]);

  const sectors: any[] = data?.sectors ?? [];

  return (
    <Page
      title="Sectors — Rotation & Market Structure"
      description="Quarterly multiple compression/expansion, cycle tags, barrier-to-entry proxies, and pure SVG histograms. Personal research software, not investment advice."
      actions={
        <div className="flex items-center gap-2" role="group" aria-label="Currency view">
          {(["ALL", "USD", "CAD"] as const).map((c) => (
            <button
              key={c}
              onClick={() => setCurrency(c)}
              aria-pressed={currency === c}
              className={`rounded-chip px-3 py-1 text-xs border ${currency === c ? "bg-accent text-bg-0 border-accent" : "bg-bg-1 border-border text-ink-1"}`}
            >
              {c}
            </button>
          ))}
        </div>
      }
    >
      {/* Institutional 11-Sector Matrix */}
      <Card
        title="Sector Rotation Tracker — Quarterly Delta Median Composite"
        subtitle={`${sectors.length || 11} GICS sectors · Full names, no truncation · Click to inspect detail`}
        padding="md"
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" role="list" aria-label="Sector rotation matrix">
          {sectors.map((s: any) => {
            const delta = formatDelta(s.quarterly_delta);
            const isSelected = selected === s.sector;
            const median = typeof s.median_composite === "number" ? s.median_composite.toFixed(2) : "Not scored";
            const count = s.count ?? s.companies ?? 0;
            return (
              <button
                key={s.sector}
                type="button"
                role="listitem"
                onClick={() => setSelected(s.sector)}
                aria-pressed={isSelected}
                aria-label={`${s.sector}: ${count} companies, median ${median}, delta ${delta.text} ${delta.label}`}
                className={`text-left rounded-md border p-3 transition-all focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1 ${
                  isSelected ? "bg-accent-weak border-accent shadow-sm" : "bg-bg-0 border-border-subtle hover:border-accent/40 hover:bg-bg-1"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-semibold text-sm leading-tight text-ink-0">{s.sector}</span>
                  {isSelected && <span className="shrink-0 h-2 w-2 rounded-full bg-accent mt-1" aria-hidden="true" />}
                </div>
                <p className="mt-1 font-mono text-xs text-ink-2">
                  {count} companies · Median {median}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <span
                    className={`inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-xs font-semibold ${
                      delta.tone === "pos"
                        ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30"
                        : delta.tone === "neg"
                          ? "bg-red-500/10 text-red-600 border-red-500/30"
                          : "bg-bg-2 text-ink-2 border-border"
                    }`}
                  >
                    {delta.text} · {delta.label}
                  </span>
                  <span className="font-mono text-[11px] text-ink-2">{s.direction ?? delta.label}</span>
                </div>
              </button>
            );
          })}
        </div>
        {sectors.length === 0 && <p className="mt-3 text-xs text-ink-2">Loading 11-sector matrix…</p>}
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title={`Cycle Tag — ${selected}`} padding="md">
          <Chip tone={cycle?.cycle_tag?.includes("Defensive") ? "positive" : cycle?.cycle_tag?.includes("Early") ? "info" : "warning"} size="sm">
            {cycle?.cycle_tag ?? "Not reported in filing"}
          </Chip>
          <p className="mt-2.5 text-xs leading-relaxed text-ink-1">{cycle?.explanation ?? "Not reported in filing"}</p>
          <p className="mt-3 border-t border-border pt-2 font-mono text-[11px] text-ink-2">Informational macro context, not a timing signal.</p>
        </Card>

        <Card title={`Barrier Proxy — ${selected}`} padding="md">
          <p className="text-xs text-ink-1">
            <span className="font-mono text-ink-2">Median stdev of gross margin:</span>{" "}
            <span className="font-mono font-bold text-ink-0">{formatPercent(barrier?.median_margin_stdev)}</span>
          </p>
          <p className="mt-2 text-xs">
            <Chip tone={barrier?.barrier_assessment?.includes("High") ? "positive" : barrier?.barrier_assessment?.includes("Low") ? "negative" : "info"}>
              {barrier?.barrier_assessment ?? "Not reported in filing"}
            </Chip>
          </p>
          <p className="mt-3 border-t border-border pt-2 font-mono text-[11px] text-ink-2">{barrier?.method ?? "Barrier proxy: within-sector dispersion of gross margins over trailing fiscal years."}</p>
        </Card>

        <Card title={`Histogram — ${selected} (${hist?.metric ?? "composite"})`} padding="md">
          {hist ? (
            <>
              <div className="flex items-center justify-between font-mono text-xs text-ink-2">
                <span>{hist.count} companies · {hist.metric ?? "composite"}</span>
                <span className="font-semibold text-accent">Median {typeof hist.median === "number" ? hist.median.toFixed(2) : "Not reported in filing"}</span>
              </div>

              <div className="mt-3 overflow-x-auto">
                <svg
                  width={600}
                  height={240}
                  viewBox="0 0 600 240"
                  role="img"
                  aria-label={`Composite score histogram for ${selected} — median ${hist.median ?? "unknown"}`}
                  className="w-full h-auto"
                >
                  <defs>
                    <linearGradient id={barGradId} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.95" />
                      <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.45" />
                    </linearGradient>
                  </defs>

                  {/* Gridlines */}
                  {[0, 1, 2, 3, 4].map((i) => (
                    <line key={i} x1={48} x2={560} y1={20 + i * 36} y2={20 + i * 36} stroke="var(--border)" strokeOpacity="0.3" strokeWidth={0.6} />
                  ))}
                  {/* Baseline */}
                  <line x1={48} y1={180} x2={560} y2={180} stroke="var(--border-subtle)" strokeWidth={1.2} />

                  {(() => {
                    const bins: number[] = hist.bins ?? [];
                    const max = Math.max(1, ...bins);
                    const binLabels = ["0–2", "2–4", "4–6", "6–8", "8–10"];
                    const plotW = 512;
                    const gap = 16;
                    const barW = (plotW - gap * (bins.length - 1)) / Math.max(1, bins.length);
                    const baseY = 180;
                    const maxH = 132;
                    return bins.map((b: number, i: number) => {
                      const h = Math.max(4, (b / max) * maxH);
                      const x = 48 + i * (barW + gap);
                      const y = baseY - h;
                      const binLabel = hist.bin_edges?.[i] ?? binLabels[i] ?? `${i * 2}–${(i + 1) * 2}`;
                      return (
                        <g key={i}>
                          <rect x={x} y={y} width={barW} height={h} rx={6} fill={`url(#${barGradId})`} stroke="var(--border)" strokeOpacity={0.2} />
                          {/* Count above bar */}
                          <text x={x + barW / 2} y={y - 8} textAnchor="middle" fontSize={12} fontWeight={700} fill="var(--ink-0)" fontFamily="IBM Plex Mono">
                            {b}
                          </text>
                          {/* Bin label */}
                          <text x={x + barW / 2} y={baseY + 16} textAnchor="middle" fontSize={11} fill="var(--ink-2)" fontFamily="IBM Plex Mono">
                            {binLabel}
                          </text>
                          {/* Bin range count subtitle */}
                          <text x={x + barW / 2} y={baseY + 28} textAnchor="middle" fontSize={9} fill="var(--ink-2)" fontFamily="IBM Plex Mono">
                            {b} names
                          </text>
                        </g>
                      );
                    });
                  })()}

                  {/* Median dashed line — unobstructed label above */}
                  {hist.median != null && typeof hist.median === "number" && (
                    <g>
                      {(() => {
                        const mx = 48 + (Math.max(0, Math.min(10, hist.median)) / 10) * 512;
                        return (
                          <>
                            <line x1={mx} x2={mx} y1={8} y2={180} stroke="var(--warn)" strokeDasharray="6 4" strokeWidth={1.8} />
                            <rect x={mx - 32} y={2} width={64} height={14} rx={3} fill="var(--warn)" />
                            <text x={mx} y={12} textAnchor="middle" fontSize={8} fontWeight={800} fill="white" fontFamily="IBM Plex Mono" letterSpacing="0.04em">
                              MEDIAN {hist.median.toFixed(2)}
                            </text>
                          </>
                        );
                      })()}
                    </g>
                  )}
                </svg>
              </div>

              <p className="mt-2 font-mono text-[11px] text-ink-2">
                Bins 0–10 composite score. Rounded top bars with counts above each bin. Amber dashed line marks sector median without colliding text.
              </p>
            </>
          ) : (
            <p className="font-mono text-xs text-ink-2">Loading histogram…</p>
          )}
        </Card>
      </div>

      <p className="border-t border-border pt-2 font-mono text-[11px] text-ink-2">Personal research software, not investment advice. Sector medians are score-only in ALL view; money per currency segregated. How sector stats are computed is documented per US-0900.</p>
    </Page>
  );
}
