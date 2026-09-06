import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, Page, Chip } from "../components/layout";

export default function SectorRotation() {
  const [currency, setCurrency] = useState<"ALL"|"USD"|"CAD">("ALL");
  const [data, setData] = useState<any>(null);
  const [hist, setHist] = useState<any>(null);
  const [cycle, setCycle] = useState<any>(null);
  const [barrier, setBarrier] = useState<any>(null);
  const [selected, setSelected] = useState<string>("Information Technology");

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
      <Card title="Sector Rotation Tracker - Quarterly Δ Median Composite" subtitle="Expansion vs compression across 11 GICS (tax inclusive note: ALL is score-only)" padding="md">
        <div className="overflow-x-auto">
          <svg width={800} height={88} viewBox="0 0 800 88" role="img" aria-label="Sector rotation delta heatmap" className="w-full h-auto">
            {sectors.map((s: any, i: number) => {
              const delta = s.quarterly_delta ?? 0;
              const intensity = Math.min(1, Math.abs(delta) * 5);
              const fill = delta > 0 ? `rgba(34,197,94,${0.15 + intensity*0.6})` : delta < 0 ? `rgba(239,68,68,${0.15 + intensity*0.6})` : "var(--bg-2)";
              const x = 10 + i * 70;
              return (
                <g key={s.sector}>
                  <rect x={x} y={10} width={64} height={48} rx={6} fill={fill} stroke="var(--border)" />
                  <text x={x+32} y={30} textAnchor="middle" fontSize={9} fontWeight={600} fill="var(--ink-0)" fontFamily="IBM Plex Mono">{s.sector.slice(0,6)}</text>
                  <text x={x+32} y={42} textAnchor="middle" fontSize={8} fill="var(--ink-1)" fontFamily="IBM Plex Mono">{delta>0?`+${delta.toFixed(2)}`:delta.toFixed(2)}</text>
                  <text x={x+32} y={52} textAnchor="middle" fontSize={7} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{s.direction}</text>
                </g>
              );
            })}
          </svg>
        </div>
        <div className="grid sm:grid-cols-3 gap-2 mt-3 text-xs">
          {sectors.slice(0,6).map((s: any) => (
            <button key={s.sector} onClick={() => setSelected(s.sector)} className={`text-left rounded border px-2.5 py-1.5 ${selected===s.sector?"bg-accent-weak border-accent text-accent":"bg-bg-0 border-border text-ink-1"}`}>
              <span className="font-semibold">{s.sector}</span> <span className="font-mono text-ink-2">n={s.count} med {s.median_composite?.toFixed(1) ?? "0.00"}</span>
            </button>
          ))}
        </div>
      </Card>

      <div className="grid lg:grid-cols-3 gap-4">
        <Card title={`Cycle Tag - ${selected}`} padding="md">
          <Chip tone={cycle?.cycle_tag?.includes("Defensive") ? "positive" : cycle?.cycle_tag?.includes("Early") ? "info" : "warning"} size="sm">{cycle?.cycle_tag ?? "Not reported in filing"}</Chip>
          <p className="text-xs text-ink-1 mt-2 leading-relaxed">{cycle?.explanation ?? "Not reported in filing"}</p>
          <p className="text-[11px] font-mono text-ink-2 mt-2">Informational macro context, not a timing signal.</p>
        </Card>
        <Card title={`Barrier Proxy - ${selected}`} padding="md">
          <p className="text-xs text-ink-1"><span className="font-mono text-ink-2">Median stdev of gross margin:</span> <span className="font-mono font-bold text-ink-0">{barrier?.median_margin_stdev ?? "0.0%"}</span></p>
          <p className="text-xs mt-1"><Chip tone={barrier?.barrier_assessment?.includes("High") ? "positive" : barrier?.barrier_assessment?.includes("Low") ? "negative" : "info"}>{barrier?.barrier_assessment ?? "Not reported in filing"}</Chip></p>
          <p className="text-[11px] font-mono text-ink-2 mt-2">{barrier?.method}</p>
        </Card>
        <Card title={`Histogram - ${selected} (${hist?.metric ?? "composite"})`} padding="md">
          {hist && (
            <>
              <p className="text-xs font-mono text-ink-2">n={hist.count} · median {hist.median ?? "Not reported in filing"} · {hist.currency}</p>
              <svg width={280} height={80} viewBox="0 0 280 80" role="img" aria-label={`Histogram for ${selected}`} className="w-full h-auto mt-2">
                {hist.bins.map((b: number, i: number) => {
                  const max = Math.max(1, ...hist.bins);
                  const h = (b / max) * 50;
                  return (
                    <g key={i}>
                      <rect x={10 + i * 52} y={60 - h} width={40} height={h} rx={3} fill="var(--accent)" opacity={0.7 + (i * 0.06)} />
                      <text x={30 + i*52} y={72} textAnchor="middle" fontSize={7} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{hist.bin_edges[i]}</text>
                      <text x={30 + i*52} y={58 - h} textAnchor="middle" fontSize={7} fill="var(--ink-0)" fontFamily="IBM Plex Mono">{b}</text>
                    </g>
                  );
                })}
                {hist.median != null && (
                  <line x1={10 + (hist.median/10)*260} x2={10 + (hist.median/10)*260} y1={8} y2={60} stroke="var(--warn)" strokeDasharray="4 2" strokeWidth={1.5} />
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