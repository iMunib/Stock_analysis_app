import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { ValuationOut } from "../api/types";
import { Card, Chip } from "./layout";

interface ReverseDCFCardProps {
  companyId: string;
}

export const ReverseDCFCard: React.FC<ReverseDCFCardProps> = ({ companyId }) => {
  const [data, setData] = useState<ValuationOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          <span>Deterministic Reverse DCF</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-bg-2 text-info font-mono uppercase">
            Expectations Investing
          </span>
        </div>
      }
      subtitle="Solves for 10-year FCF compound growth rate priced into current Enterprise Value"
    >
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
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
            {/* Implied Growth */}
            <div className="p-3 bg-bg-2/50 rounded-card border border-border">
              <div className="text-xs font-medium text-ink-1 mb-1">
                Market-Implied 10Y FCF CAGR
              </div>
              <div className="text-xl font-bold font-mono text-ink-0">
                {impliedG !== null ? `${(impliedG * 100).toFixed(1)}%` : "—"}
              </div>
              <p className="text-[11px] text-ink-2 mt-0.5 font-mono">
                At WACC {(data.wacc * 100).toFixed(1)}%, Terminal g {(data.terminal_growth_rate * 100).toFixed(1)}%
              </p>
            </div>

            {/* Historical 5Y CAGR */}
            <div className="p-3 bg-bg-2/50 rounded-card border border-border">
              <div className="text-xs font-medium text-ink-1 mb-1">
                Historical FCF CAGR (5Y)
              </div>
              <div className="text-xl font-bold font-mono text-ink-0">
                {histCAGR !== null ? `${(histCAGR * 100).toFixed(1)}%` : "—"}
              </div>
              <p className="text-[11px] text-ink-2 mt-0.5">
                Past realized annual growth rate
              </p>
            </div>

            {/* Expectations Spread */}
            <div className="p-3 bg-bg-2/50 rounded-card border border-border">
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
                {gap !== null ? `${gap > 0 ? "+" : ""}${(gap * 100).toFixed(1)}%` : "—"}
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
                            return (
                              <td
                                key={`${cell.wacc}-${cell.terminal_g}`}
                                className={`py-1.5 px-2 font-mono ${
                                  isBaseline
                                    ? "bg-accent/20 font-bold text-accent rounded-chip"
                                    : "text-ink-0"
                                }`}
                              >
                                {cell.implied_growth !== null
                                  ? `${(cell.implied_growth * 100).toFixed(1)}%`
                                  : "—"}
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
