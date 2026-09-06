import { useState } from "react";
import Tooltip from "../ui/Tooltip";
import { money } from "../../lib/format";

export interface CashFlowWaterfallProps {
  revenue?: number | null;
  grossProfit?: number | null;
  netIncome?: number | null;
  cfo?: number | null;
  fcf?: number | null;
  currency?: string | null;
  className?: string;
}

export function CashFlowWaterfall({
  revenue,
  grossProfit,
  netIncome,
  cfo,
  fcf,
  currency = "USD",
  className = "",
}: CashFlowWaterfallProps) {
  const [activeView, setActiveView] = useState<"cascade" | "steps">("cascade");

  // If revenue is null/missing (e.g. Banks and financial institutions as per AGENTS.md)
  if (revenue === null || revenue === undefined || revenue <= 0) {
    return (
      <div className={`rounded-card border border-border bg-bg-1 p-5 shadow-card transition-colors ${className}`}>
        <div className="flex items-center justify-between border-b border-border pb-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-base">🌊</span>
            <h3 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">
              Ittelson Cash Flow Waterfall
            </h3>
            <Tooltip
              title="Converting Accounting Revenue to Real Free Cash"
              content="Tracks how every dollar of revenue flows down to real, spendable cash after cost of sales, operating expenses, taxes, and capital expenditures."
            />
          </div>
          <span className="rounded-chip border border-border px-2 py-0.5 text-[11px] font-mono text-ink-2 bg-bg-2">
            Not Applicable
          </span>
        </div>
        <p className="text-xs text-ink-2 leading-relaxed font-mono py-3">
          Financial institutions and specialized filers do not report industrial gross profit or revenue-to-FCF waterfalls. Net interest income and loan loss provisions apply instead.
        </p>
      </div>
    );
  }

  const rev = revenue;
  const gp = grossProfit ?? null;
  const ni = netIncome ?? null;
  const opCash = cfo ?? null;
  const freeCash = fcf ?? null;

  // Implied deltas
  const cogs = gp != null ? rev - gp : null;
  const opexTaxes = gp != null && ni != null ? gp - ni : null;
  const nonCashWc = opCash != null && ni != null ? opCash - ni : null;
  const capex = opCash != null && freeCash != null ? opCash - freeCash : null;

  // Key conversion KPIs
  const grossMarginPct = gp != null && rev > 0 ? (gp / rev) * 100 : null;
  const netMarginPct = ni != null && rev > 0 ? (ni / rev) * 100 : null;
  const cfoNiRatio = opCash != null && ni != null && Math.abs(ni) > 0 ? opCash / ni : null;
  const fcfConversionPct = freeCash != null && rev > 0 ? (freeCash / rev) * 100 : null;

  const fmtVal = (val: number | null) => (val != null ? money(val, currency) : "Not reported in filing");
  const fmtDelta = (val: number | null) => {
    if (val == null) return "Not reported in filing";
    const sign = val > 0 ? "+" : "";
    return `${sign}${money(val, currency)}`;
  };

  // Waterfall Steps Definition
  const waterfallSteps = [
    {
      id: "rev",
      name: "Revenue",
      type: "pillar",
      val: rev,
      pctOfRev: 100,
      subtext: "Top-line gross sales volume",
      tone: "accent",
    },
    {
      id: "cogs",
      name: "Cost of Goods Sold (COGS)",
      type: "delta",
      val: cogs != null ? -cogs : null,
      pctOfRev: cogs != null ? (cogs / rev) * 100 : null,
      subtext: "Direct production & delivery costs",
      tone: "neg",
    },
    {
      id: "gp",
      name: "Gross Profit",
      type: "pillar",
      val: gp,
      pctOfRev: grossMarginPct,
      subtext: `Retained margin: ${grossMarginPct != null ? grossMarginPct.toFixed(1) : "0.00"}%`,
      tone: "info",
    },
    {
      id: "opex",
      name: "SG&A, R&D & Tax Burden",
      type: "delta",
      val: opexTaxes != null ? -opexTaxes : null,
      pctOfRev: opexTaxes != null ? (opexTaxes / rev) * 100 : null,
      subtext: "Overhead, salaries & government taxes",
      tone: "neg",
    },
    {
      id: "ni",
      name: "Net Income",
      type: "pillar",
      val: ni,
      pctOfRev: netMarginPct,
      subtext: `Accounting profit: ${netMarginPct != null ? netMarginPct.toFixed(1) : "0.00"}% net margin`,
      tone: ni != null && ni >= 0 ? "pos" : "neg",
    },
    {
      id: "wc",
      name: "± Working Capital & D&A",
      type: "delta",
      val: nonCashWc,
      pctOfRev: nonCashWc != null ? (nonCashWc / rev) * 100 : null,
      subtext:
        nonCashWc != null && nonCashWc >= 0
          ? "Accretive cash conversion (D&A addback)"
          : "Working capital cash drag / inventory buildup",
      tone: nonCashWc != null && nonCashWc >= 0 ? "pos" : "warn",
    },
    {
      id: "cfo",
      name: "Cash from Operations (CFO)",
      type: "pillar",
      val: opCash,
      pctOfRev: opCash != null ? (opCash / rev) * 100 : null,
      subtext: `Cash generation: ${cfoNiRatio != null ? cfoNiRatio.toFixed(2) + "x CFO/NI" : "0.00"}`,
      tone: cfoNiRatio != null && cfoNiRatio >= 1.0 ? "pos" : "warn",
    },
    {
      id: "capex",
      name: "Capital Expenditures (CapEx)",
      type: "delta",
      val: capex != null ? -Math.abs(capex) : null,
      pctOfRev: capex != null ? (Math.abs(capex) / rev) * 100 : null,
      subtext: "Property, plant, equipment & tech reinvestment",
      tone: "neg",
    },
    {
      id: "fcf",
      name: "Free Cash Flow (FCF)",
      type: "pillar",
      val: freeCash,
      pctOfRev: fcfConversionPct,
      subtext: `Cash to shareholders: ${fcfConversionPct != null ? fcfConversionPct.toFixed(1) : "0.00"}% of revenue`,
      tone: freeCash != null && freeCash >= 0 ? "pos" : "neg",
    },
  ];

  return (
    <div className={`rounded-card border border-border bg-bg-1 p-5 shadow-card transition-colors ${className}`}>
      {/* Executive Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-base">🌊</span>
            <h3 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">
              Ittelson Cash Flow Waterfall
            </h3>
            <Tooltip
              title="Converting Accounting Revenue to Real Free Cash"
              content="Visualizes how every single dollar of top-line revenue cascades down to genuine Free Cash Flow after COGS, operating overhead, taxes, working capital changes, and capital expenditures."
            />
          </div>
          <p className="text-xs text-ink-2 mt-0.5">
            Top-line accounting sales to real distributable owner cash flow ({currency})
          </p>
        </div>

        {/* View Switcher Controls */}
        <div className="inline-flex rounded-card p-0.5 bg-bg-0 border border-border text-xs font-mono self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveView("cascade")}
            className={`px-2.5 py-1 rounded transition-colors ${
              activeView === "cascade"
                ? "bg-accent text-bg-0 font-bold shadow-xs"
                : "text-ink-1 hover:text-ink-0 hover:bg-bg-2"
            }`}
          >
            Cascade Chart
          </button>
          <button
            type="button"
            onClick={() => setActiveView("steps")}
            className={`px-2.5 py-1 rounded transition-colors ${
              activeView === "steps"
                ? "bg-accent text-bg-0 font-bold shadow-xs"
                : "text-ink-1 hover:text-ink-0 hover:bg-bg-2"
            }`}
          >
            Step Breakdown
          </button>
        </div>
      </div>

      {/* KPI Highlight Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-5">
        <div className="rounded-card border border-border/70 bg-bg-2/40 p-2.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block">
            Gross Margin
          </span>
          <span className="text-sm font-mono font-bold text-ink-0">
            {grossMarginPct != null ? `${grossMarginPct.toFixed(1)}%` : "0.00"}
          </span>
        </div>
        <div className="rounded-card border border-border/70 bg-bg-2/40 p-2.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block">
            Net Margin
          </span>
          <span className={`text-sm font-mono font-bold ${netMarginPct != null && netMarginPct < 0 ? "text-neg" : "text-ink-0"}`}>
            {netMarginPct != null ? `${netMarginPct.toFixed(1)}%` : "0.00"}
          </span>
        </div>
        <div className="rounded-card border border-border/70 bg-bg-2/40 p-2.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block">
            Cash Conversion (CFO/NI)
          </span>
          <span className={`text-sm font-mono font-bold ${cfoNiRatio != null && cfoNiRatio >= 1.0 ? "text-pos" : "text-warn"}`}>
            {cfoNiRatio != null ? `${cfoNiRatio.toFixed(2)}x` : "0.00"}
          </span>
        </div>
        <div className="rounded-card border border-border/70 bg-bg-2/40 p-2.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block">
            FCF Conversion Rate
          </span>
          <span className={`text-sm font-mono font-bold ${freeCash != null && freeCash >= 0 ? "text-pos" : "text-neg"}`}>
            {fcfConversionPct != null ? `${fcfConversionPct.toFixed(1)}%` : "0.00"}
          </span>
        </div>
      </div>

      {/* Main Visualization */}
      {activeView === "cascade" ? (
        <div className="space-y-2.5 pt-1">
          {waterfallSteps.map((step) => {
            const isPillar = step.type === "pillar";
            const absVal = step.val != null ? Math.abs(step.val) : 0;
            const widthPct = Math.min(Math.max((absVal / rev) * 100, isPillar ? 2 : 1), 100);
            const isNegative = step.val != null && step.val < 0;

            return (
              <div
                key={step.id}
                className={`p-2 rounded-card border transition-all ${
                  isPillar
                    ? "border-border/80 bg-bg-2/30"
                    : "border-border/40 bg-bg-0/30 pl-4"
                }`}
              >
                <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      step.tone === "accent"
                        ? "bg-accent"
                        : step.tone === "pos"
                        ? "bg-pos"
                        : step.tone === "neg"
                        ? "bg-neg"
                        : step.tone === "warn"
                        ? "bg-warn"
                        : "bg-info"
                    }`} />
                    <span className={`font-semibold ${isPillar ? "text-ink-0" : "text-ink-1"}`}>
                      {step.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`font-bold ${
                      isNegative
                        ? "text-neg"
                        : isPillar
                        ? "text-ink-0"
                        : "text-pos"
                    }`}>
                      {isPillar ? fmtVal(step.val) : fmtDelta(step.val)}
                    </span>
                    {step.pctOfRev != null && (
                      <span className="text-[11px] text-ink-2">
                        ({step.pctOfRev.toFixed(1)}%)
                      </span>
                    )}
                  </div>
                </div>

                {/* Waterfall Visual Bar */}
                <div className="relative w-full h-2.5 rounded-full bg-bg-0 overflow-hidden border border-border/40">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${widthPct}%`,
                      backgroundColor:
                        step.tone === "accent"
                          ? "var(--accent)"
                          : step.tone === "pos"
                          ? "var(--pos)"
                          : step.tone === "neg"
                          ? "var(--neg)"
                          : step.tone === "warn"
                          ? "var(--warn)"
                          : "var(--info)",
                      opacity: step.val != null ? 0.9 : 0.25,
                    }}
                  />
                </div>
                <div className="mt-1 flex items-center justify-between text-[10px] font-mono text-ink-2">
                  <span>{step.subtext}</span>
                  <span>{isPillar ? "Subtotal" : "Flow Delta"}</span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Detailed Step Table View */
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-border text-[10px] uppercase text-ink-2 bg-bg-2/30">
                <th className="py-2.5 px-3">Flow Item</th>
                <th className="py-2.5 px-3">Nature</th>
                <th className="py-2.5 px-3 text-right">Amount</th>
                <th className="py-2.5 px-3 text-right">% of Revenue</th>
                <th className="py-2.5 px-3">Economic Interpretation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {waterfallSteps.map((step) => (
                <tr
                  key={step.id}
                  className={`hover:bg-bg-2/40 transition-colors ${
                    step.type === "pillar" ? "font-semibold bg-bg-2/20" : ""
                  }`}
                >
                  <td className="py-2 px-3 text-ink-0 flex items-center gap-1.5">
                    <span>{step.type === "pillar" ? "◼" : "↳"}</span>
                    <span>{step.name}</span>
                  </td>
                  <td className="py-2 px-3 text-ink-2 capitalize">
                    {step.type === "pillar" ? "Statement Base" : "Operating Delta"}
                  </td>
                  <td className={`py-2 px-3 text-right font-bold ${
                    step.val != null && step.val < 0
                      ? "text-neg"
                      : step.type === "pillar"
                      ? "text-ink-0"
                      : "text-pos"
                  }`}>
                    {step.type === "pillar" ? fmtVal(step.val) : fmtDelta(step.val)}
                  </td>
                  <td className="py-2 px-3 text-right text-ink-1">
                    {step.pctOfRev != null ? `${step.pctOfRev.toFixed(1)}%` : "0.00"}
                  </td>
                  <td className="py-2 px-3 text-[11px] text-ink-2">
                    {step.subtext}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer Takeaway */}
      <div className="mt-4 pt-3 border-t border-border/70 flex flex-wrap items-center justify-between text-[11px] font-mono text-ink-2">
        <span>
          Quality Check: {cfoNiRatio != null && cfoNiRatio >= 1.0 ? "✓ High Quality (CFO > NI)" : "⚠ Working capital or accrual drag detected"}
        </span>
        <span>
          Net Realization: {fcfConversionPct != null ? `${fcfConversionPct.toFixed(1)}¢ per $1 revenue retained` : "0.00"}
        </span>
      </div>
    </div>
  );
}

export default CashFlowWaterfall;