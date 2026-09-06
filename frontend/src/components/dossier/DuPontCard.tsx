import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { DuPontOut } from "../../api/types";
import { Card } from "../layout";

interface DuPontCardProps {
  companyId: string;
}

export const DuPontCard: React.FC<DuPontCardProps> = ({ companyId }) => {
  const [data, setData] = useState<DuPontOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<"3stage" | "5stage">("3stage");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.dupont(companyId)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load DuPont analysis");
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
        <div className="h-28 bg-bg-2/50 rounded" />
      </Card>
    );
  }

  if (error || !data || !data.history || data.history.length === 0) {
    return null;
  }

  const latest = data.latest;

  const driverColor =
    data.primary_driver === "Operational Margin Expansion"
      ? "text-pos bg-pos-weak border-pos/40"
      : data.primary_driver === "Asset Efficiency"
      ? "text-accent bg-accent-weak border-accent/40"
      : data.primary_driver === "Leverage Creep"
      ? "text-warn bg-warn-weak border-warn/40"
      : "text-ink-1 bg-bg-2 border-border";

  const pct = (val: number | null | undefined) =>
    val !== null && val !== undefined ? `${(val * 100).toFixed(1)}%` : "0.00";
  const num = (val: number | null | undefined, digits = 2) =>
    val !== null && val !== undefined ? `${val.toFixed(digits)}x` : "0.00";

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <span>DuPont ROE Decomposition</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-bg-2 text-info font-mono uppercase">
            3-Stage &amp; 5-Stage
          </span>
        </div>
      }
      subtitle="Deconstructs Return on Equity to separate operational margin power from balance sheet leverage"
      padding="md"
    >
      {/* Primary Driver Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-card bg-bg-2/50 border border-border mb-4">
        <div className="flex items-center gap-2.5">
          <span className="font-mono text-xs text-ink-2 font-medium">Primary ROE Driver:</span>
          <span className={`px-2.5 py-0.5 rounded text-xs font-semibold font-mono border ${driverColor}`}>
            {data.primary_driver}
          </span>
        </div>
        <p className="text-xs text-ink-1 leading-relaxed max-w-xl">{data.driver_explanation}</p>
      </div>

      {/* Latest Factor Cards (3-Stage Formula View) */}
      {latest && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5 font-mono">
          <div className="p-3 rounded border border-border bg-surface-1">
            <span className="text-[10px] uppercase text-ink-2">Net Profit Margin</span>
            <div className="text-lg font-bold text-ink-0 mt-1">{pct(latest.net_profit_margin)}</div>
            <span className="text-[10px] text-ink-2">Profitability power</span>
          </div>
          <div className="p-3 rounded border border-border bg-surface-1">
            <span className="text-[10px] uppercase text-ink-2">Asset Turnover</span>
            <div className="text-lg font-bold text-ink-0 mt-1">{num(latest.asset_turnover, 2)}</div>
            <span className="text-[10px] text-ink-2">Asset velocity</span>
          </div>
          <div className="p-3 rounded border border-border bg-surface-1">
            <span className="text-[10px] uppercase text-ink-2">Equity Multiplier</span>
            <div className="text-lg font-bold text-ink-0 mt-1">{num(latest.equity_multiplier, 2)}</div>
            <span className="text-[10px] text-ink-2">Financial leverage</span>
          </div>
          <div className="p-3 rounded border border-accent/40 bg-accent-weak/40">
            <span className="text-[10px] uppercase text-accent font-semibold">DuPont ROE</span>
            <div className="text-lg font-bold text-accent mt-1">{pct(latest.roe_3stage ?? latest.roe_direct)}</div>
            <span className="text-[10px] text-ink-1">Margin × Turnover × Leverage</span>
          </div>
        </div>
      )}

      {/* Mode Switcher */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-ink-0 font-heading">
          Multi-Year Decomposition History
        </span>
        <div className="inline-flex rounded-card p-0.5 bg-bg-0 border border-border text-xs font-mono">
          <button
            onClick={() => setActiveStage("3stage")}
            className={`px-2.5 py-0.5 rounded transition-colors ${
              activeStage === "3stage"
                ? "bg-accent text-bg-0 font-bold"
                : "text-ink-1 hover:text-ink-0"
            }`}
          >
            3-Stage Model
          </button>
          <button
            onClick={() => setActiveStage("5stage")}
            className={`px-2.5 py-0.5 rounded transition-colors ${
              activeStage === "5stage"
                ? "bg-accent text-bg-0 font-bold"
                : "text-ink-1 hover:text-ink-0"
            }`}
          >
            5-Stage Extended
          </button>
        </div>
      </div>

      {/* Historical Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-border text-ink-2 text-[11px]">
              <th className="py-2 text-left font-medium">FY</th>
              {activeStage === "3stage" ? (
                <>
                  <th className="py-2 text-right font-medium">Net Margin</th>
                  <th className="py-2 text-right font-medium">Asset Turnover</th>
                  <th className="py-2 text-right font-medium">Equity Multiplier</th>
                  <th className="py-2 text-right font-medium text-accent">DuPont ROE</th>
                  <th className="py-2 text-right font-medium">Reported ROE</th>
                </>
              ) : (
                <>
                  <th className="py-2 text-right font-medium">Tax Burden</th>
                  <th className="py-2 text-right font-medium">Int. Burden</th>
                  <th className="py-2 text-right font-medium">Oper. Margin</th>
                  <th className="py-2 text-right font-medium">Asset Turnover</th>
                  <th className="py-2 text-right font-medium">Leverage</th>
                  <th className="py-2 text-right font-medium text-accent">5-Stage ROE</th>
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {data.history.map((row) => (
              <tr key={row.fiscal_year} className="hover:bg-bg-2/40 transition-colors">
                <td className="py-2 text-left font-bold text-ink-0">FY{row.fiscal_year}</td>
                {activeStage === "3stage" ? (
                  <>
                    <td className="py-2 text-right text-ink-0">{pct(row.net_profit_margin)}</td>
                    <td className="py-2 text-right text-ink-0">{num(row.asset_turnover, 2)}</td>
                    <td className="py-2 text-right text-ink-0">{num(row.equity_multiplier, 2)}</td>
                    <td className="py-2 text-right font-bold text-accent">{pct(row.roe_3stage)}</td>
                    <td className="py-2 text-right text-ink-2">{pct(row.roe_direct)}</td>
                  </>
                ) : (
                  <>
                    <td className="py-2 text-right text-ink-0">{num(row.tax_burden, 2)}</td>
                    <td className="py-2 text-right text-ink-0">{num(row.interest_burden, 2)}</td>
                    <td className="py-2 text-right text-ink-0">{pct(row.operating_margin)}</td>
                    <td className="py-2 text-right text-ink-0">{num(row.asset_turnover, 2)}</td>
                    <td className="py-2 text-right text-ink-0">{num(row.equity_multiplier, 2)}</td>
                    <td className="py-2 text-right font-bold text-accent">{pct(row.roe_5stage)}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

export default DuPontCard;