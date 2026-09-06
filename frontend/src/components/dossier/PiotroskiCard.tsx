import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { PiotroskiOut, PiotroskiTest } from "../../api/types";
import { Card } from "../layout";

interface PiotroskiCardProps {
  companyId: string;
}

export const PiotroskiCard: React.FC<PiotroskiCardProps> = ({ companyId }) => {
  const [data, setData] = useState<PiotroskiOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.piotroski(companyId)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load Piotroski score");
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

  if (error || !data) {
    return null;
  }

  const signalColor =
    data.signal === "Strong"
      ? "text-pos bg-pos-weak border-pos/40"
      : data.signal === "Moderate"
      ? "text-warn bg-warn-weak border-warn/40"
      : "text-neg bg-neg-weak border-neg/40";

  const renderTestRow = (test: PiotroskiTest, idx: number) => {
    const isPass = test.passed === true;
    const isFail = test.passed === false;
    const isNa = test.passed === null;

    return (
      <div
        key={idx}
        className="flex items-start justify-between py-2 px-2.5 rounded hover:bg-bg-2/40 transition-colors text-xs border-b border-border/50 last:border-b-0"
      >
        <div className="flex items-start gap-2.5 min-w-0 pr-2">
          <span
            className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold shrink-0 mt-0.5 ${
              isPass
                ? "bg-pos-weak text-pos border border-pos/40"
                : isFail
                ? "bg-neg-weak text-neg border border-neg/40"
                : "bg-bg-2 text-ink-2 border border-border"
            }`}
          >
            {isPass ? "✓" : isFail ? "✕" : "Not reported in filing"}
          </span>
          <div>
            <div className="font-medium text-ink-0 flex items-center gap-2">
              <span>{test.name}</span>
              {isNa && (
                <span className="text-[10px] text-ink-2 font-mono uppercase bg-bg-2 px-1.5 py-0.2 rounded">
                  N/A
                </span>
              )}
            </div>
            <p className="text-[11px] text-ink-2 mt-0.5 leading-snug">{test.description}</p>
          </div>
        </div>
        <div className="text-right shrink-0 font-mono text-[11px]">
          {test.current_value !== null && (
            <div className="text-ink-0 font-semibold">
              {typeof test.current_value === "number" && Math.abs(test.current_value) < 1
                ? `${(test.current_value * 100).toFixed(1)}%`
                : test.current_value.toLocaleString()}
            </div>
          )}
          {test.prior_value !== null && (
            <div className="text-[10px] text-ink-2">
              prior:{" "}
              {typeof test.prior_value === "number" && Math.abs(test.prior_value) < 1
                ? `${(test.prior_value * 100).toFixed(1)}%`
                : test.prior_value.toLocaleString()}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <Card
      title={
        <div className="flex flex-wrap items-center gap-2">
          <span>Piotroski F-Score (9-Factor Accounting Test)</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-bg-2 text-info font-mono">
            Piotroski (2000): 1972–1996 High B/M sample
          </span>
        </div>
      }
      subtitle="Binary accounting health framework separating operational turnarounds from value traps"
      padding="md"
    >
      {/* Score Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-card bg-bg-2/60 border border-border mb-5">
        <div className="flex items-center gap-3">
          <div className="flex items-baseline gap-1 font-mono">
            <span className="text-3xl font-extrabold text-ink-0 tracking-tight">
              {data.f_score}
            </span>
            <span className="text-sm font-semibold text-ink-2">
              / {data.f_possible}
            </span>
          </div>
          <div>
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider border ${signalColor}`}
            >
              {data.signal}
            </span>
            <p className="text-xs text-ink-1 mt-1">{data.interpretation}</p>
          </div>
        </div>
        <div className="text-right font-mono text-[11px] text-ink-2">
          {data.fiscal_year && <div>Fiscal Year: FY{data.fiscal_year}</div>}
          {data.prior_fiscal_year && <div>Base Period: FY{data.prior_fiscal_year}</div>}
          {data.is_bank && <div className="text-accent">Bank Model (Rule #8 Applied)</div>}
        </div>
      </div>

      {/* False-Positive / Limitation Disclosure (US-0947) */}
      {data.signal === "Weak" && (
        <div className="mb-4 rounded border border-warn/40 bg-warn-weak/30 p-2.5 text-xs text-ink-1 font-sans">
          <strong className="text-warn font-mono text-[11px]">Model Limitation / False-Alarm Risk:</strong> Piotroski F-Score was designed to separate distressed value stocks from turnarounds. Fast-growing companies investing heavily in R&D or working capital expansion often score poorly (F &lt; 4) without balance sheet distress.
        </div>
      )}

      {/* 3 Categories Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        {/* Category 1: Profitability */}
        <div className="rounded-card border border-border bg-surface-1 p-3">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-border">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink-0">
              Profitability
            </span>
            <span className="text-[11px] font-mono text-ink-2">4 Tests</span>
          </div>
          <div className="space-y-1">
            {data.categories.profitability?.map(renderTestRow)}
          </div>
        </div>

        {/* Category 2: Leverage & Liquidity */}
        <div className="rounded-card border border-border bg-surface-1 p-3">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-border">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink-0">
              Leverage &amp; Liquidity
            </span>
            <span className="text-[11px] font-mono text-ink-2">3 Tests</span>
          </div>
          <div className="space-y-1">
            {data.categories.leverage_liquidity?.map(renderTestRow)}
          </div>
        </div>

        {/* Category 3: Operating Efficiency */}
        <div className="rounded-card border border-border bg-surface-1 p-3">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-border">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink-0">
              Operating Efficiency
            </span>
            <span className="text-[11px] font-mono text-ink-2">2 Tests</span>
          </div>
          <div className="space-y-1">
            {data.categories.efficiency?.map(renderTestRow)}
          </div>
        </div>
      </div>

      {/* Historical Behavior & Decay Disclosure (US-0063) */}
      <div className="border-t border-border/50 pt-2 text-[10px] font-mono text-ink-2">
        <span>Model Decay: Piotroski published 2000; post-2000 out-of-sample long/short alpha decayed by ~40% due to factor crowding, algorithmic adoption, and accounting changes.</span>
      </div>
    </Card>
  );
};

export default PiotroskiCard;