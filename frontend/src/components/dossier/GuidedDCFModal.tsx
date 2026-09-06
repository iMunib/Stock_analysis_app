import React, { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
// Card not needed - modal uses pure divs with tokens

interface GuidedDCFModalProps {
  companyId: string;
  isOpen: boolean;
  onClose: () => void;
}

type Scenario = "bear" | "base" | "bull";

const SCENARIOS: Record<Scenario, { label: string; growth: number; margin: number; wacc: number; terminal_g: number }> = {
  bear: { label: "Bear", growth: 0.02, margin: 0.12, wacc: 0.10, terminal_g: 0.02 },
  base: { label: "Base", growth: 0.05, margin: 0.15, wacc: 0.09, terminal_g: 0.025 },
  bull: { label: "Bull", growth: 0.08, margin: 0.18, wacc: 0.08, terminal_g: 0.03 },
};

export const GuidedDCFModal: React.FC<GuidedDCFModalProps> = ({ companyId, isOpen, onClose }) => {
  const [scenario, setScenario] = useState<Scenario>("base");
  const [growth, setGrowth] = useState(SCENARIOS.base.growth);
  const [margin, setMargin] = useState(SCENARIOS.base.margin);
  const [wacc, setWacc] = useState(SCENARIOS.base.wacc);
  const [terminalG, setTerminalG] = useState(SCENARIOS.base.terminal_g);
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [showMath, setShowMath] = useState(false);
  const [scenarioName, setScenarioName] = useState("");
  const [thesis, setThesis] = useState("");

  // Load scenario from localStorage on open
  useEffect(() => {
    if (!isOpen) return;
    const preset = SCENARIOS[scenario];
    setGrowth(preset.growth);
    setMargin(preset.margin);
    setWacc(preset.wacc);
    setTerminalG(preset.terminal_g);
  }, [isOpen, scenario]);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    api.requestGuided(companyId, { revenue_growth: growth, operating_margin: margin, wacc, terminal_g: terminalG })
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [companyId, isOpen, growth, margin, wacc, terminalG]);

  const saveScenario = () => {
    if (!scenarioName.trim()) return;
    try {
      const key = `valuation_scenarios:${companyId}`;
      const existing = JSON.parse(localStorage.getItem(key) || "[]");
      const entry = { name: scenarioName.trim(), notes: thesis.slice(0, 1000), growth, margin, wacc, terminal_g: terminalG, per_share: data?.per_share, saved_at: new Date().toISOString() };
      const next = [...existing.filter((s: any) => s.name !== entry.name), entry].slice(-10);
      localStorage.setItem(key, JSON.stringify(next));
      setScenarioName("");
    } catch {}
  };

  const heatmap = useMemo(() => {
    if (!data) return null;
    // Build 5x5 heatmap: growth rows x wacc cols
    const gVals = [growth - 0.02, growth - 0.01, growth, growth + 0.01, growth + 0.02].map((v) => Math.max(-0.05, Math.min(0.25, v)));
    const wVals = [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02].map((v) => Math.max(0.06, Math.min(0.14, v)));
    return { gVals, wVals };
  }, [data, growth, wacc]);

  if (!isOpen) return null;

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="guided-dcf-title" className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-0/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-5xl bg-bg-1 rounded-card border border-border shadow-2xl max-h-[92vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-bg-0 sticky top-0">
          <div>
            <h2 id="guided-dcf-title" className="font-heading text-base font-bold text-ink-0">Guided DCF Sandbox - Step-by-Step</h2>
            <p className="text-xs text-ink-2">Revenue → EBIT → NOPAT → FCF → Discount → Terminal → EV → Equity → per-share. Native currency.</p>
          </div>
          <button onClick={onClose} aria-label="Close guided DCF" className="p-2 text-ink-2 hover:text-ink-0">✕</button>
        </div>

        <div className="overflow-y-auto p-5 space-y-4">
          {/* Scenario toggle */}
          <div className="flex items-center gap-2" role="tablist" aria-label="Scenario">
            {(["bear", "base", "bull"] as Scenario[]).map((s) => (
              <button key={s} role="tab" aria-selected={scenario === s} onClick={() => setScenario(s)} className={`px-3 py-1.5 rounded-chip text-xs font-mono font-semibold border ${scenario === s ? "bg-accent text-bg-0 border-accent" : "bg-bg-0 text-ink-1 border-border"}`}>
                {SCENARIOS[s].label}
              </button>
            ))}
            <span className="text-xs text-ink-2 ml-2">Bear 2%/12%/10% · Base 5%/15%/9% · Bull 8%/18%/8%</span>
          </div>

          {/* Sliders */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <label className="block">
              <span className="flex justify-between text-xs text-ink-1"><span>Revenue growth</span><span className="font-mono text-accent">{(growth*100).toFixed(1)}%</span></span>
              <input type="range" min={-0.1} max={0.25} step={0.005} value={growth} onChange={(e) => setGrowth(parseFloat(e.target.value))} className="w-full accent-[var(--accent)]" aria-label="Revenue growth" />
            </label>
            <label className="block">
              <span className="flex justify-between text-xs text-ink-1"><span>Operating margin</span><span className="font-mono text-accent">{(margin*100).toFixed(1)}%</span></span>
              <input type="range" min={0.05} max={0.4} step={0.005} value={margin} onChange={(e) => setMargin(parseFloat(e.target.value))} className="w-full accent-[var(--accent)]" aria-label="Operating margin" />
            </label>
            <label className="block">
              <span className="flex justify-between text-xs text-ink-1"><span>WACC</span><span className="font-mono text-accent">{(wacc*100).toFixed(1)}%</span></span>
              <input type="range" min={0.06} max={0.14} step={0.0025} value={wacc} onChange={(e) => setWacc(parseFloat(e.target.value))} className="w-full accent-[var(--accent)]" aria-label="WACC" />
            </label>
            <label className="block">
              <span className="flex justify-between text-xs text-ink-1"><span>Terminal g</span><span className="font-mono text-accent">{(terminalG*100).toFixed(1)}%</span></span>
              <input type="range" min={0.0} max={0.045} step={0.0025} value={terminalG} onChange={(e) => setTerminalG(parseFloat(e.target.value))} className="w-full accent-[var(--accent)]" aria-label="Terminal growth" />
            </label>
          </div>

          {/* WACC build */}
          {data?.wacc_build && (
            <div className="rounded-card border border-border bg-bg-0 p-3 text-xs">
              <span className="font-mono text-[10px] uppercase text-ink-2">WACC Build</span>
              <p className="font-mono text-accent mt-1">{data.wacc_build.formula}</p>
              <p className="text-ink-2 text-xs mt-1">Risk-Free 4.0% + ERP 5.0% × Beta {data.wacc_build.beta}. Override via slider.</p>
            </div>
          )}

          {loading ? <p className="text-xs text-ink-2">Computing…</p> : data?.status === "financial_institution_excluded" ? (
            <div className="rounded-card border border-warn/40 bg-warn-weak p-3 text-sm">
              <strong className="text-warn">FCF DCF not meaningful for banks/insurers.</strong>
              <p className="text-xs text-ink-1 mt-1">{data.reason} - Use DDM and Residual Income cards.</p>
            </div>
          ) : data?.status === "computed" ? (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded border border-border bg-bg-0"><span className="font-mono text-[10px] uppercase text-ink-2 block">Enterprise Value</span><span className="font-mono font-bold text-ink-0">${(data.enterprise_value/1e9).toFixed(2)}B</span></div>
                <div className="p-3 rounded border border-border bg-bg-0"><span className="font-mono text-[10px] uppercase text-ink-2 block">Equity Value</span><span className="font-mono font-bold text-ink-0">${(data.equity_value/1e9).toFixed(2)}B</span></div>
                <div className="p-3 rounded border border-border bg-bg-0"><span className="font-mono text-[10px] uppercase text-ink-2 block">Per Share</span><span className="font-mono font-bold text-accent">{data.per_share != null ? `$${data.per_share.toFixed(2)}` : "0.00"}</span>{data.premium_discount_pct != null && <span className={`ml-2 text-xs ${data.premium_discount_pct < 0 ? "text-pos" : "text-warn"}`}>{data.premium_discount_pct > 0 ? `+${data.premium_discount_pct}% premium` : `${data.premium_discount_pct}% discount`}</span>}</div>
                <div className={`p-3 rounded border ${data.terminal_heavy ? "border-warn bg-warn-weak" : "border-border bg-bg-0"}`}><span className="font-mono text-[10px] uppercase text-ink-2 block">Terminal %</span><span className="font-mono font-bold">{data.terminal_pct.toFixed(1)}% of EV</span>{data.terminal_heavy && <span className="text-warn text-[11px] block">TERMINAL_HEAVY &gt;70% - fragile</span>}</div>
              </div>

              {/* 10-Year Projected Cash-Flow Fan Chart — pure SVG with hover points */}
              {(() => {
                const rev0 = data.steps?.[0]?.revenue ? data.steps[0].revenue / (1 + growth) : 50000;
                const baseGrowth = growth;
                const bearGrowth = Math.max(-0.05, baseGrowth - 0.03);
                const bullGrowth = Math.min(0.25, baseGrowth + 0.03);
                const tax = data.inputs?.tax_rate ?? 0.21;
                const proj = (g: number) => {
                  let rev = rev0;
                  const pts: { year: number; fcf: number; pv: number; df: number }[] = [];
                  for (let t = 1; t <= 10; t++) {
                    rev *= 1 + g;
                    const ebit = rev * margin;
                    const fcf = ebit * (1 - tax);
                    const df = 1 / Math.pow(1 + wacc, t);
                    pts.push({ year: t, fcf, pv: fcf * df, df });
                  }
                  return pts;
                };
                const basePts = proj(baseGrowth);
                const bearPts = proj(bearGrowth);
                const bullPts = proj(bullGrowth);
                const allFcf = [...basePts, ...bearPts, ...bullPts].map(p => p.fcf);
                const fMin = Math.min(...allFcf);
                const fMax = Math.max(...allFcf);
                const pad = (fMax - fMin) * 0.15 || 1;
                const yMin = fMin - pad;
                const yMax = fMax + pad;
                const W = 520, H = 180, LM = 48, RM = 16, TM = 20, BM = 28;
                const plotW = W - LM - RM;
                const plotH = H - TM - BM;
                const x = (t: number) => LM + ((t - 1) / 9) * plotW;
                const y = (v: number) => TM + (1 - (v - yMin) / (yMax - yMin)) * plotH;
                const pathFor = (pts: typeof basePts) => pts.map((p, i) => `${i === 0 ? "M" : "L"} ${x(p.year)} ${y(p.fcf)}`).join(" ");
                const areaFor = (lower: typeof bearPts, upper: typeof bullPts) => {
                  const upperPath = upper.map((p, i) => `${i === 0 ? "M" : "L"} ${x(p.year)} ${y(p.fcf)}`).join(" ");
                  const lowerRev = [...lower].reverse().map(p => `L ${x(p.year)} ${y(p.fcf)}`).join(" ");
                  return `${upperPath} ${lowerRev} Z`;
                };
                return (
                  <div className="rounded-card border border-border bg-bg-0 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-[11px] uppercase tracking-wider text-ink-0 font-semibold">10-Year Projected Cash-Flow Trajectory</span>
                      <span className="font-mono text-[10px] text-ink-2">Bear {(bearGrowth*100).toFixed(1)}% · Base {(baseGrowth*100).toFixed(1)}% · Bull {(bullGrowth*100).toFixed(1)}% · WACC {(wacc*100).toFixed(1)}%</span>
                    </div>
                    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`10-year FCF fan chart base ${(baseGrowth*100).toFixed(1)}% bear ${(bearGrowth*100).toFixed(1)}% bull ${(bullGrowth*100).toFixed(1)}%`} className="w-full h-auto select-none">
                      {/* grid */}
                      {[0, 0.25, 0.5, 0.75, 1].map((t) => (
                        <line key={t} x1={LM} x2={W - RM} y1={TM + t * plotH} y2={TM + t * plotH} stroke="var(--border)" strokeWidth={0.6} opacity={0.5} strokeDasharray="2 4" />
                      ))}
                      {/* confidence band */}
                      <path d={areaFor(bearPts, bullPts)} fill="var(--accent)" opacity={0.08} stroke="none" />
                      {/* bear line */}
                      <path d={pathFor(bearPts)} fill="none" stroke="var(--warn)" strokeWidth={1.6} strokeDasharray="6 3" opacity={0.9} />
                      {/* base line */}
                      <path d={pathFor(basePts)} fill="none" stroke="var(--accent)" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
                      {/* bull line */}
                      <path d={pathFor(bullPts)} fill="none" stroke="var(--pos)" strokeWidth={1.6} opacity={0.9} />
                      {/* axes */}
                      <line x1={LM} x2={W - RM} y1={H - BM} y2={H - BM} stroke="var(--border)" strokeWidth={1} />
                      <line x1={LM} x2={LM} y1={TM} y2={H - BM} stroke="var(--border)" strokeWidth={1} />
                      {/* x labels t+1 .. t+10 */}
                      {Array.from({ length: 10 }, (_, i) => i + 1).map((t) => (
                        <text key={t} x={x(t)} y={H - BM + 14} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">t+{t}</text>
                      ))}
                      {/* y labels */}
                      <text x={LM - 4} y={TM + 4} textAnchor="end" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">${(yMax/1e6).toFixed(0)}M</text>
                      <text x={LM - 4} y={H - BM} textAnchor="end" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">${(yMin/1e6).toFixed(0)}M</text>
                      {/* hover points */}
                      {basePts.map((p) => (
                        <g key={p.year}>
                          <circle cx={x(p.year)} cy={y(p.fcf)} r={10} fill="transparent" stroke="transparent" style={{ cursor: "pointer" }}>
                            <title>{`Year t+${p.year}: FCF $${(p.fcf/1e6).toFixed(1)}M · DF ${p.df.toFixed(3)} · PV $${(p.pv/1e6).toFixed(1)}M`}</title>
                          </circle>
                          <circle cx={x(p.year)} cy={y(p.fcf)} r={3.2} fill="var(--accent)" stroke="var(--bg-1)" strokeWidth={1.2} />
                          <circle cx={x(bearPts[p.year-1].year)} cy={y(bearPts[p.year-1].fcf)} r={2.2} fill="var(--warn)" stroke="var(--bg-1)" strokeWidth={1} opacity={0.9} />
                          <circle cx={x(bullPts[p.year-1].year)} cy={y(bullPts[p.year-1].fcf)} r={2.2} fill="var(--pos)" stroke="var(--bg-1)" strokeWidth={1} opacity={0.9} />
                        </g>
                      ))}
                    </svg>
                    <div className="flex flex-wrap gap-2 mt-2 text-[11px] font-mono">
                      <span className="inline-flex items-center gap-1.5"><span className="w-3 h-0.5 bg-warn inline-block" style={{ borderStyle: "dashed" }} /> Bear {(bearGrowth*100).toFixed(1)}%</span>
                      <span className="inline-flex items-center gap-1.5"><span className="w-3 h-1 bg-accent inline-block" /> Base {(baseGrowth*100).toFixed(1)}%</span>
                      <span className="inline-flex items-center gap-1.5"><span className="w-3 h-0.5 bg-pos inline-block" /> Bull {(bullGrowth*100).toFixed(1)}%</span>
                      <span className="ml-auto text-ink-2">Hover point for FCF, DF, PV · Confidence band  bear to bull</span>
                    </div>
                    <div className="mt-2 rounded bg-bg-2/40 border border-border px-2.5 py-1.5 text-[11px] text-ink-1">
                      <span className="font-semibold text-ink-0">WACC build:</span> {(data.wacc_build?.formula) ?? `WACC ${(wacc*100).toFixed(1)}%`} · Terminal { (terminalG*100).toFixed(1)}% · Terminal share <strong className={data.terminal_heavy ? "text-warn" : "text-ink-0"}>{data.terminal_pct?.toFixed(1) ?? "0.0"}% of EV</strong> {data.terminal_heavy && <span className="ml-1 px-1.5 py-0.5 rounded bg-warn text-white font-mono text-[10px]">High terminal &gt;70% - fragile</span>}
                    </div>
                  </div>
                );
              })()}

              {/* Uncertainty range */}
              <div className="rounded-card border border-border bg-bg-0 p-3">
                <span className="font-mono text-[10px] uppercase text-ink-2 block">Uncertainty Range (10th–50th–90th)</span>
                <div className="flex items-center gap-2 mt-2">
                  <span className="font-mono text-xs">P10: <strong>{data.uncertainty_range.p10_per_share != null ? `$${data.uncertainty_range.p10_per_share.toFixed(2)}` : "0.00"}</strong></span>
                  <span className="text-ink-2">·</span>
                  <span className="font-mono text-xs">P50: <strong className="text-accent">{data.uncertainty_range.p50_per_share != null ? `$${data.uncertainty_range.p50_per_share.toFixed(2)}` : "0.00"}</strong></span>
                  <span className="text-ink-2">·</span>
                  <span className="font-mono text-xs">P90: <strong>{data.uncertainty_range.p90_per_share != null ? `$${data.uncertainty_range.p90_per_share.toFixed(2)}` : "0.00"}</strong></span>
                </div>
                <svg width={360} height={18} viewBox="0 0 360 18" role="img" aria-label="Uncertainty range bar" className="mt-2 w-full max-w-[360px]">
                  <rect x={10} y={6} width={340} height={6} rx={3} fill="var(--bg-2)" />
                  <rect x={10} y={6} width={340 * 0.8} height={6} rx={3} fill="var(--pos)" opacity={0.3} />
                  <circle cx={10 + 340 * 0.15} cy={9} r={4} fill="var(--info)" />
                  <circle cx={10 + 340 * 0.5} cy={9} r={5} fill="var(--accent)" />
                  <circle cx={10 + 340 * 0.85} cy={9} r={4} fill="var(--warn)" />
                </svg>
                <p className="text-[11px] text-ink-2 mt-1">Range via ±1.5pp growth and ±1pp WACC shocks. Single-point fair value is false precision.</p>
              </div>

              {/* Sensitivity heatmap (growth × WACC) */}
              {heatmap && (
                <div className="rounded-card border border-border bg-bg-2/30 p-3">
                  <span className="font-mono text-[10px] uppercase text-ink-2">Sensitivity: per-share vs Growth × WACC</span>
                  <div className="overflow-x-auto mt-2">
                    <table className="w-full text-xs border-collapse" role="grid" aria-label="Sensitivity heatmap">
                      <thead>
                        <tr>
                          <th className="text-left font-mono text-[10px] text-ink-2 p-1">g \ WACC</th>
                          {heatmap.wVals.map((w) => <th key={w} className="font-mono text-ink-1 p-1">{(w*100).toFixed(1)}%</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {heatmap.gVals.map((g) => (
                          <tr key={g}>
                            <td className="font-mono text-ink-1 p-1">{(g*100).toFixed(1)}%</td>
                            {heatmap.wVals.map((w) => {
                              const isBase = Math.abs(g - growth) < 0.001 && Math.abs(w - wacc) < 0.001;
                              return <td key={`${g}-${w}`} role="gridcell" aria-label={`growth ${(g*100).toFixed(1)}% WACC ${(w*100).toFixed(1)}%`} className={`p-1 text-center font-mono ${isBase ? "bg-accent text-bg-0 font-bold" : "bg-bg-0 text-ink-0"}`}>{isBase && data.per_share ? `$${data.per_share.toFixed(0)}` : "·"}</td>;
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-[11px] text-ink-2 mt-1">Pure CSS heatmap; no chart libraries. Base cell highlighted.</p>
                </div>
              )}

              {/* Show math */}
              <div>
                <button onClick={() => setShowMath((v) => !v)} className="text-xs font-mono text-accent hover:underline">{showMath ? "Hide math" : "Show me the math →"}</button>
                {showMath && (
                  <div className="mt-2 rounded-card border border-border bg-bg-0 p-3 text-xs font-mono space-y-1 max-h-48 overflow-y-auto" role="region" aria-label="Arithmetic resolution">
                    {data.steps.map((s: any) => <div key={s.year} className="text-ink-1">{s.formula}</div>)}
                    <div className="pt-2 border-t border-border text-ink-0">PV sum: ${data.pv_sum.toLocaleString()} + PV terminal ${data.pv_terminal.toLocaleString()} = EV ${data.enterprise_value.toLocaleString()} − Net debt ${data.net_debt.toLocaleString()} = Equity ${data.equity_value.toLocaleString()} / {data.shares?.toLocaleString() ?? "0.00"} = ${data.per_share?.toFixed(2) ?? "0.00"} per share.</div>
                  </div>
                )}
              </div>

              {/* Save scenario */}
              <div className="rounded-card border border-border bg-bg-0 p-3">
                <span className="font-mono text-[10px] uppercase text-ink-2 block">Save Scenario (local)</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  <input value={scenarioName} onChange={(e) => setScenarioName(e.target.value)} placeholder="e.g., Bull - 8% growth, 18% margin" className="flex-1 min-w-[180px] rounded border border-border bg-bg-1 px-2 py-1 text-xs" aria-label="Scenario name" />
                  <input value={thesis} onChange={(e) => setThesis(e.target.value)} placeholder="Thesis notes (1000 chars)" className="flex-1 min-w-[180px] rounded border border-border bg-bg-1 px-2 py-1 text-xs" aria-label="Thesis" />
                  <button onClick={saveScenario} disabled={!scenarioName.trim()} className="px-3 py-1 rounded bg-accent text-bg-0 text-xs font-mono disabled:opacity-40">Save</button>
                </div>
                <p className="text-[11px] text-ink-2 mt-1">Persists to <code>valuation_scenarios:{companyId}</code> (max 10, local only).</p>
              </div>

              {/* Failure modes */}
              <details className="rounded-card border border-border bg-bg-0 p-3">
                <summary className="text-xs font-mono font-semibold text-ink-0 cursor-pointer">Ways this valuation fails (assumption breaks)</summary>
                <ul className="list-disc list-inside text-xs text-ink-1 mt-2 space-y-1">
                  <li>Revenue growth never materializes - terminal value dominates (&gt;70% EV) and fragile.</li>
                  <li>WACC underestimated - risk-free or ERP × Beta too low; use 10%/12%/15% required-return view.</li>
                  <li>Operating margin compresses - verify gross margin stability and DSO/inventory flags.</li>
                  <li>Share dilution - SBC offsets buybacks; see dilution tracker.</li>
                  <li>For banks/insurers - FCF DCF invalid; use DDM/Residual Income.</li>
                </ul>
              </details>
            </>
          ) : (
            <p className="text-xs text-ink-2">Insufficient data for guided DCF.</p>
          )}

          <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2 mt-2">Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.</p>
        </div>
      </div>
    </div>
  );
};

export default GuidedDCFModal;