import { useEffect, useId, useState } from "react";
import { api } from "../api/client";
import { Card, Page, Chip } from "../components/layout";

export default function SectorRotation() {
  const [currency, setCurrency] = useState<"ALL"|"USD"|"CAD">("ALL");
  const [data, setData] = useState<any>(null);
  const [hist, setHist] = useState<any>(null);
  const [cycle, setCycle] = useState<any>(null);
  const [barrier, setBarrier] = useState<any>(null);
  const [selected, setSelected] = useState<string>("Information Technology");

  const rawId = useId().replace(/:/g, "_");
  const posGradId = `posHeatmapGrad_${rawId}`;
  const negGradId = `negHeatmapGrad_${rawId}`;
  const neutralGradId = `neutralHeatmapGrad_${rawId}`;
  const barGradId = `histBarGrad_${rawId}`;

  useEffect(() => {
    api.requestSectorRotation(currency).then(setData).catch(() => {});
  }, [currency]);

  useEffect(() => {
    api.requestSectorHistogram(selected, currency).then(setHist).catch(()=>{});
    api.requestCycleTag(selected).then(setCycle).catch(()=>{});
    api.requestBarrier(selected, currency === "ALL" ? "USD" : currency).then(setBarrier).catch(()=>{});
  }, [selected, currency]);

  const sectors: any[] = data?.sectors ?? [];

  return (
    <Page
      title="Sectors - Rotation & Market Structure"
      description="Quarterly multiple compression/expansion, cycle tags, barrier-to-entry proxies, and pure SVG histograms. Personal research software, not investment advice."
      actions={
        <div className="flex items-center gap-2" role="group" aria-label="Currency view">
          {(["ALL","USD","CAD"] as const).map((c) => (
            <button key={c} onClick={() => setCurrency(c)} aria-pressed={currency===c} className={`rounded-chip px-3 py-1 text-xs border ${currency===c?"bg-accent text-bg-0 border-accent":"bg-bg-1 border-border text-ink-1"}`}>{c}</button>
          ))}
        </div>
      }
    >
      {/* Rotation heatmap - pure SVG */}
      <Card title="Sector Rotation Tracker — Quarterly Δ Median Composite" subtitle="Expansion vs compression across 11 GICS (tax inclusive note: ALL is score-only)" padding="md">
        <div className="overflow-x-auto">
          <svg width={800} height={96} viewBox="0 0 800 96" role="img" aria-label="Sector rotation delta heatmap" className="w-full h-auto">
            <defs>
              <linearGradient id={posGradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--pos)" stopOpacity="0.35" />
                <stop offset="100%" stopColor="var(--pos)" stopOpacity="0.10" />
              </linearGradient>
              <linearGradient id={negGradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--neg)" stopOpacity="0.35" />
                <stop offset="100%" stopColor="var(--neg)" stopOpacity="0.10" />
              </linearGradient>
              <linearGradient id={neutralGradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--bg-2)" stopOpacity="0.8" />
                <stop offset="100%" stopColor="var(--bg-2)" stopOpacity="0.3" />
              </linearGradient>
            </defs>
            {sectors.map((s: any, i: number) => {
              const delta = s.quarterly_delta ?? 0;
              const isSelected = selected === s.sector;
              const fill = delta > 0 ? `url(#${posGradId})` : delta < 0 ? `url(#${negGradId})` : `url(#${neutralGradId})`;
              const strokeColor = isSelected ? "var(--accent)" : delta > 0 ? "rgba(34,197,94,0.4)" : delta < 0 ? "rgba(239,68,68,0.4)" : "var(--border)";
              const x = 10 + i * 70;
              return (
                <g
                  key={s.sector}
                  onClick={() => setSelected(s.sector)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelected(s.sector);
                    }
                  }}
                  className="cursor-pointer transition-transform duration-150 hover:opacity-90"
                  role="button"
                  tabIndex={0}
                  aria-label={`${s.sector}: delta ${delta > 0 ? "+" : ""}${delta.toFixed(2)}, ${s.direction}`}
                >
                  <rect
                    x={x}
                    y={10}
                    width={64}
                    height={54}
                    rx={8}
                    fill={fill}
                    stroke={strokeColor}
                    strokeWidth={isSelected ? 2 : 1}
                  />
                  {isSelected && (
                    <circle cx={x + 32} cy={8} r={3} fill="var(--accent)" />
                  )}
                  <text x={x + 32} y={28} textAnchor="middle" fontSize={9} fontWeight={600} fill="var(--ink-0)" fontFamily="IBM Plex Mono">
                    {s.sector.length > 7 ? s.sector.slice(0, 6) + "…" : s.sector}
                  </text>
                  <text
                    x={x + 32}
                    y={42}
                    textAnchor="middle"
                    fontSize={10}
                    fontWeight={700}
                    fill={delta > 0 ? "var(--pos)" : delta < 0 ? "var(--neg)" : "var(--ink-1)"}
                    fontFamily="IBM Plex Mono"
                  >
                    {delta > 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)}
                  </text>
                  <text x={x + 32} y={54} textAnchor="middle" fontSize={7.5} fill="var(--ink-2)" fontFamily="IBM Plex Mono" letterSpacing="0.05em">
                    {s.direction?.toUpperCase()}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
        <div className="grid sm:grid-cols-3 lg:grid-cols-6 gap-2 mt-4 text-xs">
          {sectors.map((s: any) => (
            <button
              key={s.sector}
              type="button"
              onClick={() => setSelected(s.sector)}
              className={`text-left rounded-card border px-2.5 py-2 transition-all ${
                selected === s.sector
                  ? "bg-accent-weak border-accent text-accent shadow-xs"
                  : "bg-bg-0 border-border text-ink-1 hover:border-accent/40 hover:text-ink-0"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold truncate">{s.sector}</span>
                {selected === s.sector && <span className="text-[10px] text-accent">●</span>}
              </div>
              <div className="font-mono text-[10px] text-ink-2 mt-0.5">
                <span>n={s.count}</span> · <span>med {s.median_composite?.toFixed(1) ?? "0.00"}</span>
              </div>
            </button>
          ))}
        </div>
      </Card>

      <div className="grid lg:grid-cols-3 gap-4">
        <Card title={`Cycle Tag — ${selected}`} padding="md">
          <Chip tone={cycle?.cycle_tag?.includes("Defensive") ? "positive" : cycle?.cycle_tag?.includes("Early") ? "info" : "warning"} size="sm">{cycle?.cycle_tag ?? "Not reported in filing"}</Chip>
          <p className="text-xs text-ink-1 mt-2.5 leading-relaxed">{cycle?.explanation ?? "Not reported in filing"}</p>
          <p className="text-[11px] font-mono text-ink-2 mt-3 pt-2 border-t border-border">Informational macro context, not a timing signal.</p>
        </Card>
        <Card title={`Barrier Proxy — ${selected}`} padding="md">
          <p className="text-xs text-ink-1"><span className="font-mono text-ink-2">Median stdev of gross margin:</span> <span className="font-mono font-bold text-ink-0">{barrier?.median_margin_stdev ?? "0.0%"}</span></p>
          <p className="text-xs mt-2"><Chip tone={barrier?.barrier_assessment?.includes("High") ? "positive" : barrier?.barrier_assessment?.includes("Low") ? "negative" : "info"}>{barrier?.barrier_assessment ?? "Not reported in filing"}</Chip></p>
          <p className="text-[11px] font-mono text-ink-2 mt-3 pt-2 border-t border-border">{barrier?.method}</p>
        </Card>
        <Card title={`Histogram — ${selected} (${hist?.metric ?? "composite"})`} padding="md">
          {hist && (
            <>
              <div className="flex items-center justify-between text-xs font-mono text-ink-2">
                <span>n={hist.count} constituents</span>
                <span className="text-accent font-semibold">median {hist.median ?? "Not reported in filing"}</span>
              </div>
              <svg width={280} height={90} viewBox="0 0 280 90" role="img" aria-label={`Histogram for ${selected}`} className="w-full h-auto mt-2">
                <defs>
                  <linearGradient id={barGradId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.4" />
                  </linearGradient>
                </defs>
                {/* Horizontal baseline */}
                <line x1={8} y1={68} x2={272} y2={68} stroke="var(--border)" strokeWidth={1} />
                {hist.bins.map((b: number, i: number) => {
                  const max = Math.max(1, ...hist.bins);
                  const h = Math.max(2, (b / max) * 54);
                  return (
                    <g key={i}>
                      <rect x={12 + i * 52} y={68 - h} width={38} height={h} rx={4} fill={`url(#${barGradId})`} />
                      <text x={31 + i * 52} y={80} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{hist.bin_edges[i]}</text>
                      <text x={31 + i * 52} y={64 - h} textAnchor="middle" fontSize={8} fontWeight={600} fill="var(--ink-0)" fontFamily="IBM Plex Mono">{b}</text>
                    </g>
                  );
                })}
                {hist.median != null && (
                  <g>
                    <line x1={12 + (hist.median / 10) * 250} x2={12 + (hist.median / 10) * 250} y1={6} y2={68} stroke="var(--warn)" strokeDasharray="3 2" strokeWidth={1.5} />
                    <text x={12 + (hist.median / 10) * 250} y={5} textAnchor="middle" fontSize={7.5} fontWeight={700} fill="var(--warn)" fontFamily="IBM Plex Mono">MEDIAN</text>
                  </g>
                )}
              </svg>
            </>
          )}
        </Card>
      </div>

      <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Sector medians are score-only in ALL view; money per currency segregated. How sector stats are computed is documented per US-0900.</p>
    </Page>
  );
}