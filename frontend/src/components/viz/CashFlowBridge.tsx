import React, { useMemo } from "react";

/**
 * Ittelson Three-Statement Cash Flow Bridge (analytical sprint WS5).
 * Pure SVG/CSS-token waterfall: NI → ±WC → CFO → CapEx → FCF → Debt Service →
 * Buybacks/Dividends → ΔCash. No chart libraries.
 *
 * All inputs are single-currency (one company, one reporting currency) and
 * drawn from the dossier payload only. Missing steps are skipped, never faked.
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
  value: number;
  kind: "start" | "delta" | "total";
}

const fmt = (v: number) => {
  const abs = Math.abs(v);
  const sign = v < 0 ? "−" : "";
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(0)}M`;
  return `${sign}${abs.toFixed(0)}`;
};

export const CashFlowBridge: React.FC<{ inputs: CashFlowBridgeInputs }> = ({ inputs }) => {
  const steps = useMemo<Step[] | null>(() => {
    const { net_income, cfo, capex, fcf } = inputs;
    if (net_income === null || cfo === null) return null;
    const wc = cfo - net_income; // implied working-capital + non-cash bridge
    const out: Step[] = [{ label: "Net income", value: net_income, kind: "start" }];
    if (wc !== 0) out.push({ label: "± Working capital & non-cash", value: wc, kind: "delta" });
    out.push({ label: "CFO", value: cfo, kind: "total" });
    if (capex !== null && capex !== 0) {
      out.push({ label: "CapEx", value: -Math.abs(capex), kind: "delta" });
      const f = fcf ?? cfo - Math.abs(capex);
      out.push({ label: "FCF", value: f, kind: "total" });
      if (inputs.debt_service) {
        out.push({ label: "Debt service", value: -Math.abs(inputs.debt_service), kind: "delta" });
      }
      if (inputs.shareholder_returns) {
        out.push({
          label: "Buybacks & dividends",
          value: -Math.abs(inputs.shareholder_returns),
          kind: "delta",
        });
      }
      const last = out[out.length - 1];
      out.push({
        label: last.kind === "total" ? "Δ Cash retained" : "Δ Cash after outflows",
        value: last.value,
        kind: "total",
      });
    }
    return out;
  }, [inputs]);

  if (!steps) {
    return (
      <p className="text-xs text-ink-2">
        Cash-flow bridge needs net income and operating cash flow — not on file yet.
      </p>
    );
  }

  const W = 640;
  const H = 220;
  const pad = { top: 24, bottom: 46, left: 8, right: 8 };
  const maxAbs = Math.max(...steps.map((s) => Math.abs(s.value))) || 1;
  const baseline = H - pad.bottom;
  const scale = (baseline - pad.top) / maxAbs;
  const slot = (W - pad.left - pad.right) / steps.length;
  const barW = Math.min(56, slot * 0.62);

  let running = 0;
  const bars = steps.map((s, i) => {
    const x = pad.left + i * slot + (slot - barW) / 2;
    if (s.kind === "start") {
      const h = Math.abs(s.value) * scale;
      running = s.value;
      return { ...s, x, y: baseline - h, h, running };
    }
    if (s.kind === "total") {
      running = s.value;
      const h = Math.abs(s.value) * scale;
      return { ...s, x, y: baseline - h, h, running };
    }
    const from = running;
    running += s.value;
    const top = Math.max(from, running);
    const h = Math.abs(s.value) * scale;
    return { ...s, x, y: baseline - top * scale, h, running };
  });

  return (
    <figure aria-label="Ittelson cash-flow bridge: from net income through working capital, CFO, CapEx, debt service and shareholder returns to retained cash">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="presentation">
        {/* baseline */}
        <line x1={pad.left} x2={W - pad.right} y1={baseline} y2={baseline} stroke="var(--border-strong)" strokeWidth="1" />
        {bars.map((b, i) => {
          const color =
            b.kind === "total"
              ? "var(--accent)"
              : b.value >= 0
                ? "var(--pos)"
                : "var(--neg)";
          const labelY = b.y - 6;
          return (
            <g key={`${b.label}-${i}`}>
              <rect
                x={b.x}
                y={b.y}
                width={barW}
                height={Math.max(b.h, 1)}
                fill={color}
                opacity={b.kind === "delta" ? 0.75 : 1}
                rx="2"
              />
              <text
                x={b.x + barW / 2}
                y={Math.max(labelY, 12)}
                textAnchor="middle"
                fontSize="10"
                fill="var(--ink-0)"
                fontFamily="var(--font-mono, monospace)"
              >
                {fmt(b.value)}
              </text>
              {/* connector to next bar */}
              {i < bars.length - 1 && (
                <line
                  x1={b.x + barW}
                  x2={b.x + slot + (slot - barW) / 2}
                  y1={baseline - b.running * scale}
                  y2={baseline - b.running * scale}
                  stroke="var(--border)"
                  strokeDasharray="3 3"
                  strokeWidth="1"
                />
              )}
            </g>
          );
        })}
        {/* x labels */}
        {steps.map((s, i) => {
          const words = s.label.split(" ");
          const x = pad.left + i * slot + slot / 2;
          return (
            <g key={`lbl-${i}`}>
              {words.slice(0, 3).map((w, wi) => (
                <text
                  key={wi}
                  x={x}
                  y={baseline + 14 + wi * 11}
                  textAnchor="middle"
                  fontSize="9"
                  fill="var(--ink-2)"
                >
                  {w}
                </text>
              ))}
            </g>
          );
        })}
      </svg>
      {/* Accessible tabular fallback */}
      <figcaption>
        <details className="mt-2">
          <summary className="cursor-pointer text-[11px] text-ink-2">Cash bridge as table</summary>
          <table className="mt-2 w-full text-xs">
            <thead>
              <tr className="border-b border-border text-left font-mono text-[10px] uppercase text-ink-2">
                <th className="py-1">Step</th>
                <th className="py-1 text-right">Amount{inputs.currency ? ` (${inputs.currency})` : ""}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {steps.map((s, i) => (
                <tr key={`row-${i}`}>
                  <td className="py-1 text-ink-1">{s.label}</td>
                  <td className="py-1 text-right font-mono tabular-nums text-ink-0">{fmt(s.value)}</td>
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
