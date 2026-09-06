import React, { useMemo } from "react";

/**
 * Ittelson Three-Statement Cash Flow Bridge (analytical sprint WS5).
 * Pure SVG/CSS-token waterfall: NI → ±WC → CFO → CapEx → FCF → Debt Service →
 * Buybacks/Dividends → ΔCash. No chart libraries.
 *
 * Fully supports negative earnings, working capital swings, and CapEx outflows
 * with accurate zero-baseline scaling and connecting step geometry.
 */
export interface CashFlowBridgeInputs {
  net_income: number | null;
  cfo: number | null;
  capex: number | null;
  fcf: number | null;
  /** Net interest + debt repayment if known; falls back to interest expense. */
  debt_service?: number | null;
  /** Buybacks + dividends if known; else omitted from the bridge. */
  shareholder_returns?: number | null;
  currency?: string | null;
}

interface Step {
  label: string;
  shortLabel: string;
  value: number;
  kind: "start" | "delta" | "total";
}

const fmt = (v: number) => {
  const abs = Math.abs(v);
  const sign = v < 0 ? "−" : v > 0 ? "+" : "";
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(1)}M`;
  return `${sign}${abs.toFixed(0)}`;
};

const fmtTotal = (v: number) => {
  const abs = Math.abs(v);
  const sign = v < 0 ? "−" : "";
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(1)}M`;
  return `${sign}${abs.toFixed(0)}`;
};

export const CashFlowBridge: React.FC<{ inputs: CashFlowBridgeInputs; className?: string }> = ({
  inputs,
  className = "",
}) => {
  const steps = useMemo<Step[] | null>(() => {
    const { net_income, cfo, capex, fcf } = inputs;
    if (net_income === null || cfo === null) return null;
    const wc = cfo - net_income; // implied working-capital + non-cash bridge
    const out: Step[] = [
      { label: "Net income", shortLabel: "Net Income", value: net_income, kind: "start" },
    ];
    if (wc !== 0) {
      out.push({
        label: "± Working capital & non-cash",
        shortLabel: "WC & Non-Cash",
        value: wc,
        kind: "delta",
      });
    }
    out.push({ label: "CFO (Operating Cash)", shortLabel: "CFO", value: cfo, kind: "total" });
    if (capex !== null && capex !== 0) {
      out.push({ label: "CapEx (Reinvestment)", shortLabel: "CapEx", value: -Math.abs(capex), kind: "delta" });
      const f = fcf ?? cfo - Math.abs(capex);
      out.push({ label: "Free Cash Flow", shortLabel: "FCF", value: f, kind: "total" });
      if (inputs.debt_service) {
        out.push({
          label: "Debt service",
          shortLabel: "Debt Service",
          value: -Math.abs(inputs.debt_service),
          kind: "delta",
        });
      }
      if (inputs.shareholder_returns) {
        out.push({
          label: "Buybacks & dividends",
          shortLabel: "Capital Return",
          value: -Math.abs(inputs.shareholder_returns),
          kind: "delta",
        });
      }
      const last = out[out.length - 1];
      out.push({
        label: last.kind === "total" ? "Δ Cash retained" : "Δ Cash after outflows",
        shortLabel: "Net Cash Retained",
        value: last.value,
        kind: "total",
      });
    }
    return out;
  }, [inputs]);

  if (!steps) {
    return (
      <div className="rounded-card border border-border bg-bg-1 p-4 text-xs text-ink-2 font-mono">
        Cash-flow bridge needs net income and operating cash flow - not on file yet.
      </div>
    );
  }

  // Dimensions & padding
  const W = 780;
  const H = 260;
  const pad = { top: 32, bottom: 58, left: 16, right: 16 };
  const chartH = H - pad.top - pad.bottom;

  // Calculate cumulative runnings and min/max extent
  let running = 0;
  const allLevels: number[] = [0];
  const processed = steps.map((s) => {
    let startVal = 0;
    let endVal = 0;
    if (s.kind === "start") {
      startVal = 0;
      endVal = s.value;
      running = s.value;
    } else if (s.kind === "total") {
      startVal = 0;
      endVal = s.value;
      running = s.value;
    } else {
      startVal = running;
      endVal = running + s.value;
      running = endVal;
    }
    allLevels.push(startVal, endVal);
    return { ...s, startVal, endVal, runningLevel: running };
  });

  const maxVal = Math.max(...allLevels);
  const minVal = Math.min(...allLevels);
  const range = maxVal - minVal || 1;
  // Give 10% breathing room above and below
  const yDomainMax = maxVal > 0 ? maxVal + range * 0.08 : range * 0.05;
  const yDomainMin = minVal < 0 ? minVal - range * 0.08 : -range * 0.05;
  const totalSpan = yDomainMax - yDomainMin;

  const getY = (val: number) => pad.top + ((yDomainMax - val) / totalSpan) * chartH;
  const zeroY = getY(0);

  const slotW = (W - pad.left - pad.right) / steps.length;
  const barW = Math.min(58, slotW * 0.68);

  const bars = processed.map((s, i) => {
    const x = pad.left + i * slotW + (slotW - barW) / 2;
    const yTop = getY(Math.max(s.startVal, s.endVal));
    const yBottom = getY(Math.min(s.startVal, s.endVal));
    const h = Math.max(yBottom - yTop, 3);
    return {
      ...s,
      x,
      y: yTop,
      h,
      connectY: getY(s.endVal),
    };
  });

  return (
    <figure
      aria-label="Ittelson cash-flow bridge: from net income through working capital, CFO, CapEx, debt service and shareholder returns to retained cash"
      className={`relative w-full rounded-card border border-border bg-bg-1 p-3 shadow-card ${className}`}
    >
      <div className="flex items-center justify-between pb-2 mb-1 border-b border-border/70 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-heading font-bold uppercase tracking-wider text-ink-0 text-[11px]">
            Ittelson Bridge (Accounting Profit → Free Cash)
          </span>
          <span className="text-[10px] font-mono text-ink-2">
            {inputs.currency ? `Currency: ${inputs.currency}` : "Native Currency"}
          </span>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded bg-accent inline-block" /> Total / Landmark
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded bg-pos inline-block" /> Inflow / Absorption
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded bg-neg inline-block" /> Outflow / Deficit
          </span>
        </div>
      </div>

      <div className="overflow-x-auto no-scrollbar py-1">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full min-w-[620px]" role="presentation">
          <defs>
            <linearGradient id="bar-pos-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--pos)" stopOpacity="0.95" />
              <stop offset="100%" stopColor="var(--pos)" stopOpacity="0.75" />
            </linearGradient>
            <linearGradient id="bar-neg-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--neg)" stopOpacity="0.95" />
              <stop offset="100%" stopColor="var(--neg)" stopOpacity="0.75" />
            </linearGradient>
            <linearGradient id="bar-tot-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.95" />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Zero baseline */}
          <line
            x1={pad.left}
            x2={W - pad.right}
            y1={zeroY}
            y2={zeroY}
            stroke="var(--border-strong)"
            strokeWidth="1.5"
            strokeDasharray="4 3"
          />
          <text
            x={pad.left}
            y={zeroY - 4}
            fill="var(--ink-2)"
            fontSize="9"
            fontFamily="var(--font-mono, monospace)"
          >
            0
          </text>

          {/* Bars & Connections */}
          {bars.map((b, i) => {
            const isTotal = b.kind === "total";
            const isPositive = b.value >= 0;
            const fill = isTotal ? "url(#bar-tot-grad)" : isPositive ? "url(#bar-pos-grad)" : "url(#bar-neg-grad)";
            const strokeColor = isTotal ? "var(--accent)" : isPositive ? "var(--pos)" : "var(--neg)";

            const isValueAbove = b.kind === "delta" ? b.value >= 0 : b.endVal >= 0;
            const labelY = isValueAbove ? b.y - 7 : b.y + b.h + 13;

            return (
              <g key={`${b.label}-${i}`} className="transition-all hover:opacity-90">
                {/* Background column highlight */}
                <rect
                  x={pad.left + i * slotW + 2}
                  y={pad.top}
                  width={slotW - 4}
                  height={chartH}
                  fill="var(--bg-2)"
                  opacity="0.25"
                  rx="3"
                />

                {/* Main waterfall bar */}
                <rect
                  x={b.x}
                  y={b.y}
                  width={barW}
                  height={b.h}
                  fill={fill}
                  stroke={strokeColor}
                  strokeWidth="1"
                  rx="3"
                />

                {/* Value text tag */}
                <text
                  x={b.x + barW / 2}
                  y={labelY}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="600"
                  fill="var(--ink-0)"
                  fontFamily="var(--font-mono, monospace)"
                >
                  {isTotal ? fmtTotal(b.value) : fmt(b.value)}
                </text>

                {/* Connector line to next step */}
                {i < bars.length - 1 && (
                  <line
                    x1={b.x + barW}
                    x2={bars[i + 1].x}
                    y1={b.connectY}
                    y2={b.connectY}
                    stroke="var(--ink-2)"
                    strokeDasharray="2 2"
                    strokeWidth="1.2"
                    opacity="0.75"
                  />
                )}
              </g>
            );
          })}

          {/* X-axis labels */}
          {bars.map((b, i) => {
            const centerX = b.x + barW / 2;
            const words = b.shortLabel.split(" ");
            return (
              <g key={`lbl-${i}`}>
                {words.map((w, wi) => (
                  <text
                    key={wi}
                    x={centerX}
                    y={H - pad.bottom + 18 + wi * 12}
                    textAnchor="middle"
                    fontSize="9.5"
                    fontWeight="500"
                    fill={b.kind === "total" ? "var(--ink-0)" : "var(--ink-1)"}
                    fontFamily="var(--font-sans, sans-serif)"
                  >
                    {w}
                  </text>
                ))}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Accessible tabular fallback */}
      <figcaption className="mt-2 pt-2 border-t border-border/60">
        <details className="cursor-pointer group">
          <summary className="text-[11px] font-mono text-ink-2 group-hover:text-ink-0 flex items-center justify-between">
            <span>Show Waterfall Statement Table</span>
            <span className="text-[10px] text-accent">Expand ▼</span>
          </summary>
          <table className="mt-2.5 w-full text-xs font-mono">
            <thead>
              <tr className="border-b border-border text-left text-[10px] uppercase text-ink-2 tracking-wider">
                <th className="py-1">Step</th>
                <th className="py-1 text-right">Amount{inputs.currency ? ` (${inputs.currency})` : ""}</th>
                <th className="py-1 text-right">Running Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {processed.map((s, i) => (
                <tr key={`row-${i}`} className="hover:bg-bg-2/40">
                  <td className="py-1.5 text-ink-1">
                    <span className="font-semibold text-ink-0">{s.label}</span>
                  </td>
                  <td
                    className={`py-1.5 text-right font-semibold ${
                      s.kind === "total"
                        ? "text-accent"
                        : s.value >= 0
                        ? "text-pos"
                        : "text-neg"
                    }`}
                  >
                    {s.kind === "total" ? fmtTotal(s.value) : fmt(s.value)}
                  </td>
                  <td className="py-1.5 text-right text-ink-0 font-medium">
                    {fmtTotal(s.runningLevel)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      </figcaption>
    </figure>
  );
};

export default CashFlowBridge;