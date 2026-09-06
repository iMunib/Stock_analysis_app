import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Card } from "../layout";
import InfoTip from "../InfoTip";

interface EPVCardProps {
  companyId: string;
}

export const EPVCard: React.FC<EPVCardProps> = ({ companyId }) => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .requestEPV(companyId)
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [companyId]);

  if (loading) return <Card padding="md" className="animate-pulse"><div className="h-20 bg-bg-2 rounded" /></Card>;
  if (!data) return null;

  if (data.status === "insufficient_data") {
    return (
      <Card title={<span>Greenwald Earnings Power Value (EPV) <InfoTip term="EPV" /></span>} subtitle="Reproduction-cost floor vs market cap">
        <p className="text-xs text-ink-1">Insufficient data for EPV — {data.reason ?? "EBIT missing"} <InfoTip term="EBIT" /></p>
        <p className="text-[11px] font-mono text-ink-2 mt-1">{data.disclaimer}</p>
      </Card>
    );
  }

  const epv = data.epv;
  const repro = data.reproduction_cost;
  const mcap = data.market_cap;
  const floor = data.floor_value;
  const disc = data.premium_discount_pct;
  const isCheap = disc != null && disc < 0;
  const isSpeculative = disc != null && disc > 30;
  const franchiseMargin = epv != null && repro != null ? epv - repro : null;
  const franchisePositive = franchiseMargin != null && franchiseMargin > 0;
  const barMax = Math.max(epv ?? 0, repro ?? 0, mcap ?? 0, floor ?? 0, 1);
  const pct = (v: number | null | undefined) => (v != null ? (v / barMax) * 100 : 0);

  return (
    <Card
      title={<span>Valuation Spectrum & Margin of Safety Floor <InfoTip term="EPV" /></span>}
      subtitle="Greenwald Earnings Power Value — Normalized Earnings Power vs Reproduction Cost"
      padding="md"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-2.5 rounded border border-border bg-bg-0">
            <span className="font-mono text-[10px] uppercase text-ink-2 block">Normalized Earnings Power <InfoTip term="EBIT" /></span>
            <span className="font-mono font-bold text-ink-0">{data.normalized_ebit != null ? `$${(data.normalized_ebit/1e9).toFixed(2)}B` : "Not reported in filing"} <span className="text-ink-2 text-[10px]">x (1-{(data.tax_rate*100).toFixed(0)}%) / {(data.wacc*100).toFixed(1)}% <InfoTip term="WACC" /></span></span>
            <span className="text-[10px] text-ink-2 block">Median EBIT 5Y · {data.ebit_source}</span>
            {data.thin_history && <span className="text-[10px] text-warn">Thin history: assumption uses 1-2 points</span>}
          </div>
          <div className="p-2.5 rounded border border-border bg-bg-0">
            <span className="font-mono text-[10px] uppercase text-ink-2 block">Earnings Power Value <InfoTip term="EPV" /></span>
            <span className="font-mono font-bold text-ink-0">{epv != null ? `$${(epv/1e9).toFixed(2)}B` : "Not reported in filing"}</span>
            <span className="text-[10px] text-ink-2 block">NOPAT <InfoTip term="NOPAT" /> / WACC <InfoTip term="WACC" /> · Franchise value</span>
          </div>
          <div className="p-2.5 rounded border border-border bg-bg-0">
            <span className="font-mono text-[10px] uppercase text-ink-2 block">Reproduction Cost Floor</span>
            <span className="font-mono font-bold text-ink-0">{repro != null ? `$${(repro/1e9).toFixed(2)}B` : "Not reported in filing"}</span>
            <span className="text-[10px] text-ink-2 block">Proxy: Total Assets · Capital required to replicate</span>
          </div>
        </div>

        {/* Institutional Valuation Spectrum — horizontal floor vs EPV vs Market */}
        <div className="rounded border border-border bg-bg-2/30 p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider text-ink-0 font-semibold">Capital Efficiency Spectrum</span>
            <span className="font-mono text-[10px] text-ink-2">Franchise Margin {franchiseMargin != null ? `${franchisePositive ? "+" : ""}$${(franchiseMargin/1e9).toFixed(2)}B` : "Not reported in filing"} {franchisePositive ? "· Economic rents above capital" : franchiseMargin != null ? "· No moat" : ""}</span>
          </div>
          <svg width={520} height={84} viewBox="0 0 520 84" role="img" aria-label={`Valuation spectrum: Reproduction floor ${repro ? (repro/1e9).toFixed(1)+'B' : 'Not reported'} vs EPV ${epv ? (epv/1e9).toFixed(1)+'B' : 'Not reported'} vs Market ${mcap ? (mcap/1e9).toFixed(1)+'B' : 'Not reported'}`} className="w-full h-auto">
            {/* Track */}
            <rect x={12} y={28} width={496} height={16} rx={8} fill="var(--bg-2)" stroke="var(--border)" strokeWidth={1} />
            {/* Reproduction floor bar (bottom) */}
            {repro != null && <rect x={12} y={46} width={pct(repro)*4.96} height={10} rx={5} fill="var(--warn)" opacity={0.9} />}
            {/* EPV bar (top) */}
            {epv != null && <rect x={12} y={28} width={pct(epv)*4.96} height={16} rx={8} fill="var(--info)" opacity={0.95} />}
            {/* Franchise margin highlight between repro and EPV when EPV > repro */}
            {franchisePositive && epv != null && repro != null && (
              <rect x={12 + pct(repro)*4.96} y={28} width={(pct(epv)-pct(repro))*4.96} height={16} rx={0} fill="var(--pos)" opacity={0.25} />
            )}
            {/* Tick markers at 25/50/75/100% */}
            {[25,50,75,100].map((p) => (
              <g key={p}>
                <line x1={12 + (p/100)*496} x2={12 + (p/100)*496} y1={24} y2={64} stroke="var(--border)" strokeWidth={0.7} strokeDasharray="2 3" opacity={0.6} />
                <text x={12 + (p/100)*496} y={74} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{p}%</text>
              </g>
            ))}
            {/* Market cap needle */}
            {mcap != null && <g>
              <line x1={12 + pct(mcap)*4.96} x2={12 + pct(mcap)*4.96} y1={14} y2={60} stroke="var(--accent)" strokeWidth={2.4} strokeLinecap="round" />
              <circle cx={12 + pct(mcap)*4.96} cy={14} r={5} fill="var(--accent)" stroke="var(--bg-1)" strokeWidth={1.8} />
              <text x={12 + pct(mcap)*4.96} y={12} textAnchor="middle" fontSize={8} fill="var(--accent)" fontFamily="IBM Plex Mono" fontWeight={700}>Market</text>
            </g>}
            <text x={12} y={18} fontSize={9} fill="var(--ink-2)" fontFamily="IBM Plex Mono">Floor: Reproduction (warn) · Value: EPV (info) · Market needle (accent) · Franchise margin shaded pos</text>
          </svg>
          <div className="flex flex-wrap gap-2 text-[11px] font-mono mt-2">
            {repro != null && <span className="px-2 py-0.5 rounded bg-warn-weak text-warn border border-warn/30">Floor ${ (repro/1e9).toFixed(1)}B Reproduction</span>}
            {epv != null && <span className="px-2 py-0.5 rounded bg-info-weak text-info border border-info/30">EPV ${ (epv/1e9).toFixed(1)}B Earnings Power</span>}
            {mcap != null && <span className="px-2 py-0.5 rounded bg-accent-weak text-accent border border-accent/30">Market ${ (mcap/1e9).toFixed(1)}B Enterprise</span>}
            {franchiseMargin != null && (
              <span className={`px-2 py-0.5 rounded border text-[11px] font-semibold ${franchisePositive ? "bg-pos-weak text-pos border-pos/30" : "bg-neg-weak text-neg border-neg/30"}`}>
                Franchise Margin {franchisePositive ? "+" : ""}${(franchiseMargin/1e9).toFixed(2)}B {franchisePositive ? "· Moat present" : "· Competitive"}
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-mono">Margin of Safety Floor: <strong className="text-ink-0">{floor != null ? `$${(floor/1e9).toFixed(2)}B` : "Not reported in filing"}</strong></span>
          {disc != null && (
            <span className={`px-2.5 py-1 rounded-chip font-mono text-xs font-semibold border ${isCheap ? "bg-pos-weak text-pos border-pos/30" : isSpeculative ? "bg-neg-weak text-neg border-neg/30" : "bg-warn-weak text-warn border-warn/30"}`} role="status" aria-label={`Margin of safety ${disc > 0 ? "premium" : "discount"} ${disc}%`}>
              {disc > 0 ? `Premium +${disc}%` : `Margin of Safety ${disc}%`}
              {isSpeculative ? " · Speculative territory" : isCheap ? " · Value opportunity" : ""}
            </span>
          )}
          {data.cheap_for_reason_flag && <span className="px-2 py-0.5 rounded-chip bg-neg-weak text-neg border border-neg/30 text-xs font-mono">Cheap for reason: verify forensic flags</span>}
        </div>

        <p className="text-xs text-ink-1 leading-relaxed">Normalized Earnings Power = Median EBIT (5-year) x (1 - tax) / WACC. Reproduction Cost proxied via Total Assets as capital required to replicate operating assets. Franchise Margin quantifies economic rents above capital costs.</p>
        <p className="text-[11px] font-mono text-ink-2">{data.disclaimer}</p>
      </div>
    </Card>
  );
};

export default EPVCard;