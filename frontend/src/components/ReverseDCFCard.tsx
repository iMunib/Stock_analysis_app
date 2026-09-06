import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { ValuationOut } from "../api/types";
import { Card, Chip } from "./layout";
import InfoTip from "./InfoTip";

interface ReverseDCFCardProps {
  companyId: string;
}

export const ReverseDCFCard: React.FC<ReverseDCFCardProps> = ({ companyId }) => {
  const [data, setData] = useState<ValuationOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);
  // Trust sprint C3: local what-if rates (client-side only; defaults from the payload)
  const [localWacc, setLocalWacc] = useState(0.09);
  const [localGTerm, setLocalGTerm] = useState(0.025);

  // Trust sprint C: "Refresh Price & Recompute" enqueues a single-company backfill
  // (202 + poll). The button never mutates scores directly - the worker does.
  const refreshPrice = async () => {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const res = await api.refreshCompanyPrice(companyId);
      setRefreshMsg(`Queued job ${res.job_id ?? ""} - poll Jobs page`);
    } catch (err) {
      setRefreshMsg(err instanceof Error ? err.message : "Could not queue refresh");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.valuation(companyId)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load valuation data");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [companyId]);

  // Client-side solve of the same 10y DCF polynomial at the user's local rates.
  // Pure bisection on [-0.40, 0.60]; no API call, nothing persisted.
  const localG = useMemo(() => {
    if (!data || data.baseline_fcf === null || data.baseline_fcf === undefined || data.baseline_fcf <= 0) return null;
    if (data.current_share_price === null || data.current_share_price === undefined || !data.diluted_shares) return null;
    if (localWacc <= localGTerm) return null;
    const fcf0 = data.baseline_fcf;
    const shares = data.diluted_shares;
    const netDebt = data.net_debt ?? 0;
    const evTarget = data.current_share_price * shares + netDebt;
    const f = (g: number) => {
      let pv = 0;
      for (let t = 1; t <= 10; t++) pv += (fcf0 * Math.pow(1 + g, t)) / Math.pow(1 + localWacc, t);
      const fcf10 = fcf0 * Math.pow(1 + g, 10);
      pv += (fcf10 * (1 + localGTerm)) / (localWacc - localGTerm) / Math.pow(1 + localWacc, 10);
      return pv - evTarget;
    };
    let lo = -0.4, hi = 0.6;
    const flo = f(lo), fhi = f(hi);
    if (flo * fhi > 0) return null;
    for (let i = 0; i < 80; i++) {
      const mid = (lo + hi) / 2;
      if (f(lo) * f(mid) <= 0) hi = mid; else lo = mid;
    }
    return (lo + hi) / 2;
  }, [data, localWacc, localGTerm]);
  if (loading) {
    return (
      <Card padding="md" className="animate-pulse">
        <div className="h-5 bg-bg-2 rounded w-1/3 mb-4" />
        <div className="h-24 bg-bg-2/60 rounded" />
      </Card>
    );
  }

  if (error || !data) {
    return null;
  }

  const isNegativeFCF = data.status === "dcf_unviable_negative_fcf" || (data.baseline_fcf !== null && data.baseline_fcf <= 0);
  const impliedG = data.market_implied_growth_10y;
  const histCAGR = data.historical_5y_cagr;
  const gap = data.expectations_gap;
  const matrix = data.sensitivity_matrix;


  const cardTone = isNegativeFCF
    ? "warning"
    : gap !== null && gap < -0.04
      ? "positive"
      : gap !== null && gap > 0.05
        ? "warning"
        : "neutral";

  return (
    <Card
      tone={cardTone}
      title={
        <div className="flex items-center gap-2">
          <span>Deterministic Reverse DCF <InfoTip term="DCF" /></span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-bg-2 text-info font-mono uppercase">
            Expectations Investing
          </span>
        </div>
      }
      subtitle={<span>Solves for 10-year FCF <InfoTip term="FCF" /> compound growth rate (CAGR <InfoTip term="CAGR" />) priced into current Enterprise Value (EV <InfoTip term="EV" />)</span>}
    >
      {/* Analytical sprint WS5: Opportunity cost vs index hurdle */}
      {(() => {
        const fcf0 = data.baseline_fcf;
        const shares = data.diluted_shares;
        if (fcf0 === null || fcf0 === undefined || fcf0 <= 0 || !shares) return null;
        const marketCap = (data.current_share_price ?? 0) * shares;
        if (!marketCap) return null;
        const fcfYield = fcf0 / marketCap; // owner earnings yield vs the 4.5% index baseline
        const baseline = 0.045;
        const wacc = data.wacc || 0.09;
        // Required growth g so that the DCF value of the firm's FCF stream matches
        // an 8% index compounding promise on the same capital: solve the same
        // polynomial at implied growth for EV = marketCap x (8% horizon premium).
        // Practitioner simplification: required g = wacc x (1 + shortfall) where
        // shortfall = max(0, baseline - fcfYield)/baseline, capped for display.
        const shortfall = Math.max(0, baseline - fcfYield) / baseline;
        const requiredG = wacc * (1 + Math.min(shortfall, 1.5));
        const beats = fcfYield >= baseline;
        return (
          <div className="mb-3 rounded-card border border-border bg-bg-2/50 px-3 py-2 text-[11px] leading-relaxed text-ink-1">
            <span className="font-semibold text-ink-0">Opportunity cost vs index: </span>
            owner FCF <InfoTip term="FCF" /> yield {`${(fcfYield * 100).toFixed(1)}%`} vs index baseline 4.5%.{" "}
            {beats ? (
              <span className="text-pos">Current cash generation clears the hurdle; growth above {(requiredG * 100).toFixed(1)}% is upside.</span>
            ) : (
              <span className="text-warn">
                If company growth &lt; {(requiredG * 100).toFixed(1)}% (required to cover the yield gap vs an 8% index
                compounding), holding a low-cost index ETF provides superior risk-adjusted return.
              </span>
            )}
          </div>
        );
      })()}      {/* Trust sprint C: method banner */}
      <div className="mb-4 rounded-card border border-info/30 bg-bg-2/60 px-3 py-2 text-[11px] leading-relaxed text-ink-1">
        Reverse DCF solves for market-implied growth based on the displayed share price. It is not an analyst forecast.
      </div>
      {isNegativeFCF ? (
        <div className="p-4 rounded-card bg-warn-weak border border-warn/40 flex items-start gap-3">
          <span className="text-warn font-bold text-base" aria-hidden="true">⚠️</span>
          <div>
            <div className="text-xs font-bold text-warn tracking-wide uppercase font-mono">
              dcf_unviable_negative_fcf
            </div>
            <p className="text-xs text-ink-1 mt-1 leading-relaxed">
              Baseline Free Cash Flow is non-positive ({data.baseline_fcf ? `$${(data.baseline_fcf / 1e6).toFixed(1)}M` : "NULL"}).
              Reverse DCF root-solving requires positive baseline cash generation to project compounding.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Freshness badges + stale-price warning (Trust sprint C) */}
          <div className="mb-4 flex flex-wrap items-center gap-2 text-[11px] font-mono">
            <span className="rounded-chip border border-border bg-bg-2 px-2 py-0.5 text-ink-1">
              Price {data.price_freshness ?? "unknown"}
              {data.price_as_of ? ` · ${data.price_as_of.slice(0, 10)}` : ""}
            </span>
            <span className="rounded-chip border border-border bg-bg-2 px-2 py-0.5 text-ink-1">
              FCF base {data.baseline_fcf_basis ?? "?"} · {data.fcf_freshness ?? "unknown"}
              {data.baseline_fcf_period_end ? ` · ${data.baseline_fcf_period_end.slice(0, 10)}` : ""}
            </span>
            {data.price_freshness === "red" && (
              <span role="alert" className="rounded-chip border border-warn/50 bg-warn-weak px-2 py-0.5 text-warn">
                Valuation based on stale price ({data.price_as_of?.slice(0, 10) ?? "unknown date"}). Implied growth may not reflect current market conditions.
              </span>
            )}
            <button
              type="button"
              onClick={refreshPrice}
              disabled={refreshing}
              className="rounded-chip border border-accent/60 bg-accent-weak px-2.5 py-0.5 text-accent disabled:opacity-40"
            >
              {refreshing ? "Queued…" : "Refresh Price & Recompute"}
            </button>
            {refreshMsg && <span className="text-ink-2">{refreshMsg}</span>}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
            {/* Implied Growth */}
            <div className="p-3 bg-bg-2/50 rounded-card border border-border" style={{ padding: "var(--space-3)" }}>
              <div className="text-xs font-medium text-ink-1 mb-1">
                Market-Implied 10Y FCF CAGR
              </div>
              <div className="text-xl font-bold font-mono text-ink-0">
                {impliedG !== null ? `${(impliedG * 100).toFixed(1)}%` : "0.00"}
              </div>
              <p className="text-[11px] text-ink-2 mt-0.5 font-mono">
                At WACC {(data.wacc * 100).toFixed(1)}%, Terminal g {(data.terminal_growth_rate * 100).toFixed(1)}%
              </p>
            </div>

            {/* Historical 5Y CAGR */}
            <div className="p-3 bg-bg-2/50 rounded-card border border-border" style={{ padding: "var(--space-3)" }}>
              <div className="text-xs font-medium text-ink-1 mb-1">
                Historical FCF CAGR (5Y)
              </div>
              <div className="text-xl font-bold font-mono text-ink-0">
                {histCAGR !== null ? `${(histCAGR * 100).toFixed(1)}%` : "0.00"}
              </div>
              <p className="text-[11px] text-ink-2 mt-0.5">
                Past realized annual growth rate
              </p>
            </div>

            {/* Expectations Spread */}
            <div className="p-3 bg-bg-2/50 rounded-card border border-border" style={{ padding: "var(--space-3)" }}>
              <div className="text-xs font-medium text-ink-1 mb-1 flex items-center justify-between">
                <span>Expectations Spread</span>
                {gap !== null && gap < -0.04 && (
                  <Chip tone="positive" size="sm">DISCOUNTED</Chip>
                )}
                {gap !== null && gap > 0.05 && (
                  <Chip tone="warning" size="sm">DEMANDING</Chip>
                )}
              </div>
              <div
                className={`text-xl font-bold font-mono ${
                  gap !== null && gap < 0
                    ? "text-pos"
                    : gap !== null && gap > 0.05
                    ? "text-warn"
                    : "text-ink-0"
                }`}
              >
                {gap !== null ? `${gap > 0 ? "+" : ""}${(gap * 100).toFixed(1)}%` : "0.00"}
              </div>
              <p className="text-[11px] text-ink-2 mt-0.5 leading-relaxed">
                {gap !== null
                  ? gap < -0.04
                    ? "Market prices in significant deceleration vs. historical trajectory (potential margin of safety)."
                    : gap > 0.05
                    ? "Market requires acceleration over past trajectory."
                    : "Market expectations closely track historical trajectory."
                  : "Requires both implied growth and historical CAGR."}
              </p>
            </div>
          </div>

          {/* Elegant horizontal comparative bars - Implied vs Historical */}
          {impliedG !== null && histCAGR !== null && (
            <svg width={520} height={64} viewBox="0 0 520 64" role="img" aria-label={`Implied growth ${(impliedG*100).toFixed(1)}% vs historical ${(histCAGR*100).toFixed(1)}%`} className="w-full h-auto mb-4">
              <text x={12} y={14} fontSize={9} fill="var(--ink-2)" fontFamily="IBM Plex Mono">Comparative Growth - Implied (accent) vs Historical (info)</text>
              {/* gridlines */}
              {[0, 10, 20].map((v) => (
                <g key={v}>
                  <line x1={140 + (v/20)*360} x2={140 + (v/20)*360} y1={18} y2={56} stroke="var(--border)" strokeWidth={0.6} strokeDasharray="2 3" opacity={0.5} />
                  <text x={140 + (v/20)*360} y={62} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{v}%</text>
                </g>
              ))}
              {/* Historical bar */}
              <rect x={140} y={22} width={Math.max(4, Math.min(360, (Math.max(0, histCAGR)*100/20)*360))} height={12} rx={6} fill="var(--info)" opacity={0.9} />
              <text x={146} y={30} fontSize={9} fill="white" fontFamily="IBM Plex Mono" fontWeight={600}>{(histCAGR*100).toFixed(1)}% hist</text>
              {/* Implied bar */}
              <rect x={140} y={38} width={Math.max(4, Math.min(360, (Math.max(0, impliedG)*100/20)*360))} height={12} rx={6} fill="var(--accent)" opacity={0.95} />
              <text x={146} y={46} fontSize={9} fill="var(--bg-0)" fontFamily="IBM Plex Mono" fontWeight={700}>{(impliedG*100).toFixed(1)}% implied</text>
              {/* Benchmark marker at 8% hurdle */}
              <line x1={140 + (8/20)*360} x2={140 + (8/20)*360} y1={18} y2={56} stroke="var(--warn)" strokeWidth={1.2} strokeDasharray="4 3" />
              <text x={140 + (8/20)*360} y={14} textAnchor="middle" fontSize={8} fill="var(--warn)" fontFamily="IBM Plex Mono">8% hurdle</text>
            </svg>
          )}

          {/* Trust sprint C3: local what-if sliders (client-side only, never stored) */}
          <div className="mb-4 p-3 rounded-card border border-border bg-bg-2/40">
            <div className="text-xs font-semibold text-ink-0 mb-2 flex items-center justify-between">
              <span>What-if (local only - never stored, never changes scores)</span>
              {localG !== null && (
                <span className="font-mono text-[11px] text-accent">implied g @ your rates: {(localG * 100).toFixed(1)}%</span>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label className="block">
                <span className="flex items-baseline justify-between text-[11px] text-ink-1">
                  <span>WACC</span>
                  <span className="font-mono text-accent">{(localWacc * 100).toFixed(1)}%</span>
                </span>
                <input
                  type="range"
                  min={0.06}
                  max={0.14}
                  step={0.005}
                  value={localWacc}
                  onChange={(e) => setLocalWacc(Number(e.target.value))}
                  className="mt-1 w-full accent-[var(--accent)]"
                  aria-label="Discount rate (WACC)"
                />
              </label>
              <label className="block">
                <span className="flex items-baseline justify-between text-[11px] text-ink-1">
                  <span>Terminal growth</span>
                  <span className="font-mono text-accent">{(localGTerm * 100).toFixed(1)}%</span>
                </span>
                <input
                  type="range"
                  min={0.0}
                  max={0.045}
                  step={0.0025}
                  value={localGTerm}
                  onChange={(e) => setLocalGTerm(Number(e.target.value))}
                  className="mt-1 w-full accent-[var(--accent)]"
                  aria-label="Terminal growth rate"
                />
              </label>
            </div>
            {localG === null && (
              <p className="mt-1.5 text-[10px] text-warn">
                No solution at these rates - the implied-growth bracket does not cross zero (try a higher WACC or lower terminal growth).
              </p>
            )}
          </div>

          {/* Sensitivity Matrix */}
          {matrix && matrix.grid && matrix.grid.length > 0 && (
            <div className="p-3.5 bg-bg-2/40 rounded-card border border-border">
              <div className="text-xs font-semibold text-ink-0 mb-2 flex items-center justify-between">
                <span>Sensitivity Matrix: Implied Growth Rate (WACC vs. Terminal g)</span>
                <span className="text-[10px] font-mono text-ink-2">Solved via Brent's method</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-center border-collapse">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="py-1.5 px-2 text-ink-2 font-mono text-[10px] uppercase text-left">
                        WACC \ Terminal g
                      </th>
                      {matrix.terminal_g_headers.map((tg) => (
                        <th key={tg} className="py-1.5 px-2 text-ink-1 font-mono">
                          {(tg * 100).toFixed(1)}%
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {matrix.grid.map((row, rowIdx) => {
                      const waccVal = matrix.wacc_headers[rowIdx];
                      return (
                        <tr key={waccVal} className="hover:bg-bg-2/60 transition-colors">
                          <td className="py-1.5 px-2 text-ink-1 font-mono text-left font-medium">
                            {(waccVal * 100).toFixed(1)}%
                          </td>
                           {row.map((cell) => {
                            const isBaseline =
                              Math.abs(cell.wacc - data.wacc) < 0.001 &&
                              Math.abs(cell.terminal_g - data.terminal_growth_rate) < 0.001;
                            const val = cell.implied_growth;
                            const tint = val == null ? "bg-bg-0 text-ink-2" : val < 0.05 ? "bg-pos-weak text-pos" : val > 0.12 ? "bg-neg-weak text-neg" : "bg-accent-weak text-accent";
                            return (
                              <td
                                key={`${cell.wacc}-${cell.terminal_g}`}
                                role="gridcell"
                                aria-label={`Implied growth ${(val != null ? (val*100).toFixed(1) : "n/a")}% at WACC ${(cell.wacc*100).toFixed(1)}% terminal ${(cell.terminal_g*100).toFixed(1)}%`}
                                className={`py-1.5 px-2 font-mono text-center transition-colors hover:bg-accent/10 ${isBaseline ? "bg-accent text-bg-0 font-bold rounded" : tint + " rounded"}`}
                              >
                                {val !== null ? `${(val * 100).toFixed(1)}%` : "0.00"}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </Card>
  );
};