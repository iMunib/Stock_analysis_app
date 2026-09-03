import React from "react";
import { Card } from "../layout";

interface PercentileMatrixProps {
  percentiles: Record<string, number | null> | null | undefined;
  sectorName?: string | null;
  currency?: string | null;
  className?: string;
}

interface MetricMeta {
  key: string;
  label: string;
  category: "Valuation" | "Profitability" | "Leverage" | "Cash Return";
  description: string;
}

const METRICS_META: MetricMeta[] = [
  {
    key: "pe_ratio",
    label: "P/E Multiple",
    category: "Valuation",
    description: "Price to Earnings (Inverted: lower multiple = higher percentile rank)",
  },
  {
    key: "ev_to_ebitda",
    label: "EV / EBITDA",
    category: "Valuation",
    description: "Enterprise Value to EBITDA (Inverted: cheaper valuation = higher percentile rank)",
  },
  {
    key: "pb_ratio",
    label: "P/B Multiple",
    category: "Valuation",
    description: "Price to Book Equity (Inverted: lower multiple = higher percentile rank)",
  },
  {
    key: "roe",
    label: "Return on Equity (ROE)",
    category: "Profitability",
    description: "Net Income / Book Equity (Higher = better)",
  },
  {
    key: "roic_or_rnoa",
    label: "ROIC / Penman RNOA",
    category: "Profitability",
    description: "Core operating asset productivity without buyback leverage distortion",
  },
  {
    key: "fcf_margin",
    label: "Free Cash Flow Margin",
    category: "Cash Return",
    description: "Free Cash Flow as % of Revenue (Higher = better cash generation)",
  },
  {
    key: "net_debt_to_ebitda",
    label: "Net Debt / EBITDA",
    category: "Leverage",
    description: "Balance sheet leverage ratio (Inverted: lower debt = higher percentile rank)",
  },
  {
    key: "total_shareholder_yield",
    label: "Total Shareholder Yield",
    category: "Cash Return",
    description: "Dividend Yield + Net Buyback Yield (Higher = greater cash returned to owners)",
  },
];

export const PercentileMatrix: React.FC<PercentileMatrixProps> = ({
  percentiles,
  sectorName,
  currency,
  className = "",
}) => {
  if (!percentiles || Object.keys(percentiles).length === 0) {
    return (
      <Card title="Sector Percentile Matrix" subtitle="Peer distribution across core ratios" padding="sm" className={className}>
        <div className="py-6 text-center text-xs text-ink-2">
          Sector percentile ranks not materialized for this company.
        </div>
      </Card>
    );
  }

  const getBarColor = (pct: number) => {
    if (pct >= 75) return "bg-pos";
    if (pct >= 25) return "bg-accent";
    return "bg-neg";
  };

  const getTextColor = (pct: number) => {
    if (pct >= 75) return "text-pos";
    if (pct >= 25) return "text-accent";
    return "text-neg";
  };

  return (
    <Card
      title="Sector Percentile Matrix"
      subtitle={`Exact 0–100 percentile rank vs ${sectorName || "same-currency"} peer group (${currency || "Local"})`}
      padding="md"
      className={className}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between text-[11px] text-ink-2 border-b border-border pb-2">
          <span>Core Fundamental Metric</span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-neg" /> Bottom 25%
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-accent" /> Mid 25–75%
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-pos" /> Top 75%+
            </span>
          </div>
        </div>

        <div className="space-y-3">
          {METRICS_META.map((m) => {
            const rawPct = percentiles[m.key];
            const pct = rawPct != null ? Math.max(0, Math.min(100, rawPct)) : null;

            return (
              <div key={m.key} className="group">
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-ink-0">{m.label}</span>
                    <span className="text-[10px] text-ink-2 font-mono uppercase">({m.category})</span>
                  </div>
                  <div className="font-mono text-xs font-semibold">
                    {pct != null ? (
                      <span className={getTextColor(pct)}>{pct.toFixed(1)}th pct</span>
                    ) : (
                      <span className="text-ink-2">—</span>
                    )}
                  </div>
                </div>

                {/* SVG Percentile Track */}
                <div className="relative h-3 w-full bg-surface-2 rounded-full overflow-hidden border border-border/50">
                  {/* Quartile Tick Lines */}
                  <div className="absolute top-0 bottom-0 left-[25%] w-px bg-border z-10 opacity-70" title="25th percentile" />
                  <div className="absolute top-0 bottom-0 left-[50%] w-px bg-ink-2/40 z-10" title="Median (50th percentile)" />
                  <div className="absolute top-0 bottom-0 left-[75%] w-px bg-border z-10 opacity-70" title="75th percentile" />

                  {pct != null && (
                    <div
                      className={`h-full transition-all duration-500 rounded-full ${getBarColor(pct)}`}
                      style={{ width: `${pct}%` }}
                      role="progressbar"
                      aria-valuenow={pct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${m.label}: ${pct.toFixed(1)}th percentile`}
                    />
                  )}
                </div>

                <div className="text-[10px] text-ink-2 mt-0.5 opacity-80 group-hover:opacity-100 transition-opacity">
                  {m.description}
                </div>
              </div>
            );
          })}
        </div>

        {/* Screen Reader Table */}
        <table className="sr-only">
          <caption>Sector Percentile Ranks</caption>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Category</th>
              <th>Percentile</th>
            </tr>
          </thead>
          <tbody>
            {METRICS_META.map((m) => (
              <tr key={m.key}>
                <td>{m.label}</td>
                <td>{m.category}</td>
                <td>{percentiles[m.key] != null ? `${percentiles[m.key]}%` : "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

export default PercentileMatrix;
