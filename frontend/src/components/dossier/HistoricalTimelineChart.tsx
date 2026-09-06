import React, { useState } from "react";
import { money } from "../../lib/format";

interface HistoryPoint {
  fiscal_year: number;
  revenue?: number | null;
  net_income?: number | null;
  fcf_calc?: number | null;
  diluted_eps?: number | null;
  source?: string | null;
  as_of_date?: string | null;
  gross_profit?: number | null;
  operating_cash_flow?: number | null;
}

interface Props {
  history: HistoryPoint[];
  currency: string;
  title?: string;
}

function yoy(curr: number | null | undefined, prev: number | null | undefined): string | null {
  if (curr == null || prev == null || prev === 0) return null;
  const v = (curr - prev) / Math.abs(prev);
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(1)}% YoY`;
}

export const HistoricalTimelineChart: React.FC<Props> = ({ history, currency, title = "10-Year Financial Trajectory" }) => {
  const sorted = [...history].filter(h => h.fiscal_year != null).sort((a, b) => a.fiscal_year - b.fiscal_year);
  const last10 = sorted.slice(-10);
  const [pinned, setPinned] = useState<number | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const active = pinned ?? hovered;

  if (last10.length === 0) {
    return <p className="text-xs text-ink-2">Not reported in filing: insufficient history</p>;
  }

  const W = 560, H = 180, LM = 48, RM = 16, TM = 18, BM = 28;
  const plotW = W - LM - RM;
  const plotH = H - TM - BM;

  const revenues = last10.map(h => h.revenue).filter((v): v is number => v != null);
  const maxV = Math.max(...revenues, 1);
  const minV = Math.min(...revenues, 0);
  const pad = (maxV - minV) * 0.12 || maxV * 0.1;
  const yMin = Math.max(0, minV - pad);
  const yMax = maxV + pad;

  const x = (i: number) => LM + (i / Math.max(1, last10.length - 1)) * plotW;
  const y = (v: number) => TM + (1 - (v - yMin) / (yMax - yMin)) * plotH;

  const revenuePath = last10.map((h, i) => {
    const v = h.revenue ?? yMin;
    return `${i === 0 ? "M" : "L"} ${x(i)} ${y(v)}`;
  }).join(" ");

  const fcfVals = last10.map(h => h.fcf_calc);
  const hasFCF = fcfVals.some(v => v != null);

  return (
    <div className="rounded border border-border bg-bg-0 p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[11px] uppercase tracking-wider text-ink-0 font-semibold">{title}</span>
        <span className="font-mono text-[10px] text-ink-2">FY {last10[0].fiscal_year} - FY {last10[last10.length-1].fiscal_year} · Native {currency}</span>
      </div>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`10-year revenue trajectory ${last10.length} fiscal years`} className="w-full h-auto select-none">
        {/* grid */}
        {[0, 0.33, 0.66, 1].map(t => (
          <line key={t} x1={LM} x2={W - RM} y1={TM + t * plotH} y2={TM + t * plotH} stroke="var(--border)" strokeWidth={0.6} opacity={0.45} strokeDasharray="2 4" />
        ))}
        {/* revenue line */}
        <path d={revenuePath} fill="none" stroke="var(--accent)" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
        {/* points */}
        {last10.map((h, i) => {
          const v = h.revenue;
          const isActive = active === i;
          const prev = i > 0 ? last10[i-1].revenue : null;
          const yoyStr = yoy(v, prev);
          return (
            <g key={h.fiscal_year} onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)} onClick={() => setPinned(p => p === i ? null : i)} role="button" tabIndex={0} aria-label={`FY${h.fiscal_year} revenue ${v != null ? money(v, currency) : "Not reported in filing"} ${yoyStr ?? ""}`} onKeyDown={(e) => { if (e.key === "Enter") setPinned(p => p === i ? null : i); }}>
              <circle cx={x(i)} cy={y(v ?? yMin)} r={isActive ? 5 : 3.2} fill={isActive ? "var(--accent)" : "var(--bg-1)"} stroke="var(--accent)" strokeWidth={1.6} style={{ cursor: "pointer" }} />
              {/* tooltip trigger area */}
              <circle cx={x(i)} cy={y(v ?? yMin)} r={14} fill="transparent" />
              {/* year label */}
              <text x={x(i)} y={H - BM + 14} textAnchor="middle" fontSize={8} fill={isActive ? "var(--ink-0)" : "var(--ink-2)"} fontFamily="IBM Plex Mono" fontWeight={isActive ? 700 : 400}>{h.fiscal_year}</text>
            </g>
          );
        })}
        {/* y axis labels */}
        <text x={LM - 6} y={TM + 4} textAnchor="end" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{money(yMax, currency)}</text>
        <text x={LM - 6} y={H - BM} textAnchor="end" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{money(yMin, currency)}</text>
        {/* axis */}
        <line x1={LM} x2={W - RM} y1={H - BM} y2={H - BM} stroke="var(--border)" strokeWidth={1} />
        <line x1={LM} x2={LM} y1={TM} y2={H - BM} stroke="var(--border)" strokeWidth={1} />
      </svg>

      {/* Active tooltip */}
      {active != null && last10[active] && (
        <div className="mt-2 rounded border border-accent/30 bg-accent-weak px-3 py-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-mono font-semibold text-accent">FY{last10[active].fiscal_year}</span>
            <span className="font-mono text-[10px] text-ink-2">{last10[active].source ?? "SEC 10-K filed"} {last10[active].as_of_date ?? ""}</span>
            <button onClick={() => setPinned(null)} className="text-ink-2 hover:text-ink-0 ml-2" aria-label="Clear pinned">✕</button>
          </div>
          <div className="grid grid-cols-3 gap-2 mt-1.5 font-mono text-xs">
            <div><span className="text-ink-2 block text-[10px] uppercase">Revenue</span><span className="font-semibold text-ink-0">{last10[active].revenue != null ? money(last10[active].revenue!, currency) : "Not reported in filing"}</span>{(() => { const prev = active>0 ? last10[active-1].revenue : null; const s = yoy(last10[active].revenue, prev); return s ? <span className={`ml-1 text-[11px] ${s.startsWith("+") ? "text-pos" : "text-neg"}`}>{s}</span> : null; })()}</div>
            <div><span className="text-ink-2 block text-[10px] uppercase">Net Income</span><span className="font-semibold text-ink-0">{last10[active].net_income != null ? money(last10[active].net_income!, currency) : "Not reported in filing"}</span></div>
            <div><span className="text-ink-2 block text-[10px] uppercase">FCF</span><span className="font-semibold text-ink-0">{last10[active].fcf_calc != null ? money(last10[active].fcf_calc!, currency) : hasFCF ? "Not reported in filing" : "Not applicable: Bank model"}</span></div>
          </div>
          <p className="text-[11px] text-ink-2 mt-1">Click point to pin. Hover for exact values. YoY computed vs prior fiscal year.</p>
        </div>
      )}
      {! (active != null) && (
        <p className="text-[11px] text-ink-2 mt-1 font-mono">Hover point for exact figures. Click to pin. Native currency never converted.</p>
      )}
    </div>
  );
};

export default HistoricalTimelineChart;
