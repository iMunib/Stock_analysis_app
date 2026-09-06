import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Card, Chip } from "../layout";

interface TechnicalContextCardProps {
  companyId: string;
}

export const TechnicalContextCard: React.FC<TechnicalContextCardProps> = ({ companyId }) => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .requestTechnicals(companyId)
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [companyId]);

  if (loading) return <Card padding="md" className="animate-pulse"><div className="h-32 bg-bg-2 rounded" /></Card>;
  if (!data) return null;

  const mom = data.momentum_12_1;
  const momPct = data.momentum_percentile;
  const sma50 = data.sma50;
  const sma200 = data.sma200;
  const price = data.current_price;
  const high = data.high_52w;
  const low = data.low_52w;
  const pos = data.position_in_52w_range_pct;
  const dd = data.max_drawdown?.max_drawdown_pct;
  const rec = data.max_drawdown?.recovery_days;
  const beta = data.beta;
  const corr = data.correlation_vs_benchmark;

  // 12-1 momentum meter: -40% to +40% mapped to 0-100
  const momNorm = mom != null ? Math.max(-0.4, Math.min(0.4, mom)) : 0;
  const momX = ((momNorm + 0.4) / 0.8) * 480;

  return (
    <Card
      title="Technical Context - 12-1 Momentum & Price Overlays"
      subtitle="Academic 12-1 (Jegadeesh & Titman 1993) - P_{t-1}/P_{t-12} −1, skipping most recent month"
      padding="md"
    >
      <div className="space-y-4">
        {/* 12-1 Momentum Meter - pure SVG */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="font-mono text-xs font-semibold text-ink-0">12-1 Momentum</span>
            <span className="flex items-center gap-1">
              <Chip tone={mom != null && mom > 0.1 ? "positive" : mom != null && mom < -0.1 ? "negative" : "info"} size="sm">
                {momPct != null ? `${momPct}th percentile` : "0.00"}
              </Chip>
              <span className="font-mono text-xs text-ink-1">{mom != null ? `${(mom*100).toFixed(1)}%` : "0.00"}</span>
            </span>
          </div>
          <svg width={520} height={48} viewBox="0 0 520 48" role="img" aria-label={`12-1 momentum ${(mom!=null?(mom*100).toFixed(1):"n/a")}% percentile ${momPct ?? "n/a"}`} className="w-full h-auto">
            <rect x={10} y={16} width={480} height={10} rx={5} fill="var(--bg-2)" stroke="var(--border)" />
            <rect x={10} y={16} width={240} height={10} rx={5} fill="var(--neg-weak)" />
            <rect x={250} y={16} width={240} height={10} rx={5} fill="var(--pos-weak)" />
            <line x1={250} x2={250} y1={12} y2={30} stroke="var(--ink-2)" strokeWidth={1} strokeDasharray="3 3" />
            {mom != null && <g>
              <line x1={20 + momX} x2={20 + momX} y1={10} y2={32} stroke="var(--accent)" strokeWidth={2} />
              <circle cx={20 + momX} cy={10} r={4} fill="var(--accent)" stroke="var(--bg-1)" strokeWidth={1.5} />
            </g>}
            <text x={10} y={42} fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">-40%</text>
            <text x={250} y={42} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">0%</text>
            <text x={490} y={42} textAnchor="end" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">+40%</text>
          </svg>
          <p className="text-[11px] font-mono text-ink-2 mt-1">{data.momentum_formula}</p>
          <p className="text-[11px] text-ink-2">Technical context only - 12-1 momentum is NOT a scoring pillar and does not alter locked composite math.</p>
        </div>

        {/* 52-Week Range & SMA Gauge - pure SVG */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="font-mono text-xs font-semibold text-ink-0">52-Week Range & SMA 50/200</span>
            <span className="font-mono text-xs text-ink-1">Price ${price?.toFixed(2) ?? "0.00"}</span>
          </div>
          <svg width={520} height={40} viewBox="0 0 520 40" role="img" aria-label={`Price ${price ?? "n/a"} in 52-week range`} className="w-full h-auto">
            <rect x={10} y={16} width={480} height={8} rx={4} fill="var(--bg-2)" stroke="var(--border)" />
            {/* SMA markers */}
            {sma50 != null && high != null && low != null && high !== low && (
              <line x1={10 + ((sma50 - low)/(high - low))*480} x2={10 + ((sma50 - low)/(high - low))*480} y1={12} y2={28} stroke="var(--info)" strokeWidth={1.5} strokeDasharray="4 2" />
            )}
            {sma200 != null && high != null && low != null && high !== low && (
              <line x1={10 + ((sma200 - low)/(high - low))*480} x2={10 + ((sma200 - low)/(high - low))*480} y1={12} y2={28} stroke="var(--warn)" strokeWidth={1.5} strokeDasharray="4 2" />
            )}
            {/* Price marker */}
            {price != null && high != null && low != null && high !== low && (
              <g>
                <line x1={10 + ((price - low)/(high - low))*480} x2={10 + ((price - low)/(high - low))*480} y1={10} y2={30} stroke="var(--accent)" strokeWidth={2} />
                <circle cx={10 + ((price - low)/(high - low))*480} cy={10} r={4} fill="var(--accent)" stroke="var(--bg-1)" strokeWidth={1.5} />
              </g>
            )}
            <text x={10} y={36} fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">${low?.toFixed(0) ?? "0.00"} low</text>
            <text x={490} y={36} textAnchor="end" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">${high?.toFixed(0) ?? "0.00"} high</text>
          </svg>
          <div className="flex gap-2 text-[11px] font-mono text-ink-2">
            <span className="inline-flex items-center gap-1"><span className="w-2 h-0.5 bg-info inline-block" /> SMA50 ${sma50?.toFixed(2) ?? "0.00"}</span>
            <span className="inline-flex items-center gap-1"><span className="w-2 h-0.5 bg-warn inline-block" /> SMA200 ${sma200?.toFixed(2) ?? "0.00"}</span>
            <span>{pos != null ? `${pos}% of 52w range` : ""}</span>
          </div>
        </div>

        {/* Drawdown & Beta */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="rounded border border-border bg-bg-0 p-2.5">
            <span className="font-mono text-[10px] uppercase text-ink-2 block">Max Drawdown</span>
            <span className="font-mono font-bold text-neg">{dd != null ? `-${dd}%` : "0.00"}</span>
            <span className="text-[11px] text-ink-2 block">Recovery: {rec != null ? `${rec}d` : "- (not recovered)"}</span>
            {/* Recovery bar - pure SVG */}
            <svg width={120} height={8} viewBox="0 0 120 8" role="img" aria-label={`Max drawdown ${dd ?? "n/a"}%`} className="mt-1 w-full">
              <rect x={0} y={0} width={120} height={8} rx={4} fill="var(--bg-2)" />
              <rect x={0} y={0} width={Math.min(120, (dd ?? 0) * 2)} height={8} rx={4} fill="var(--neg)" opacity={0.8} />
            </svg>
          </div>
          <div className="rounded border border-border bg-bg-0 p-2.5">
            <span className="font-mono text-[10px] uppercase text-ink-2 block">Beta vs {data.benchmark}</span>
            <span className="font-mono font-bold text-ink-0">{beta ?? "Not reported in filing"}</span>
            <span className="text-[11px] text-ink-2 block">Correlation {corr ?? "Not reported in filing"}</span>
          </div>
          <div className="rounded border border-border bg-bg-0 p-2.5">
            <span className="font-mono text-[10px] uppercase text-ink-2 block">Volatility 30d</span>
            <span className="font-mono font-bold text-ink-0">{data.volatility_30d_pct != null ? `${data.volatility_30d_pct}%` : "0.00"}</span>
            <span className="text-[11px] text-ink-2 block">Annualized</span>
          </div>
        </div>

        {/* Valuation-Price Alignment */}
        {data.valuation_price_alignment && (
          <div className="rounded border border-border bg-bg-2/40 p-2.5">
            <span className="font-mono text-xs font-semibold text-ink-0">Valuation–Price Alignment</span>
            <p className="text-xs text-ink-1 mt-1">
              Price ${data.valuation_price_alignment.price?.toFixed(2) ?? "0.00"} vs DCF ${data.valuation_price_alignment.per_share?.toFixed(2) ?? "0.00"} → <strong className={data.valuation_price_alignment.zone === "Undervalued" ? "text-pos" : data.valuation_price_alignment.zone === "Overvalued" ? "text-neg" : "text-warn"}>{data.valuation_price_alignment.zone}</strong> ({data.valuation_price_alignment.discount_pct != null ? `${data.valuation_price_alignment.discount_pct > 0 ? "+" : ""}${data.valuation_price_alignment.discount_pct.toFixed(1)}%` : "0.00"})
            </p>
          </div>
        )}

        <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Price momentum is market sentiment context, not an intrinsic verdict. Insider transactions are filed historical facts.</p>
      </div>
    </Card>
  );
};

export default TechnicalContextCard;