import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { ForensicsOut } from "../api/types";
import { Card, Chip } from "./layout";

interface ForensicCardProps {
  companyId: string;
}

export const ForensicCard: React.FC<ForensicCardProps> = ({ companyId }) => {
  const [data, setData] = useState<ForensicsOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [schilit, setSchilit] = useState<{ eqr: number | null; triggered_flags: string[] } | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.schilit(companyId)
      .then((d) => {
        if (!cancelled) setSchilit(d as { eqr: number | null; triggered_flags: string[] });
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [companyId]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.forensics(companyId)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load forensic data");
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
        <div className="h-20 bg-bg-2/60 rounded" />
      </Card>
    );
  }

  if (error || !data) {
    return null;
  }

  const sloan = data.sloan_accrual_ratio;
  const ccer = data.cash_conversion_ratio;
  const roic = data.roic;
  const fcfYield = data.fcf_yield;
  const history = data.fcf_vs_ni_history || [];

  // SVG Chart calculation for FCF vs Net Income
  const chartHeight = 120;
  const chartWidth = 320;
  const padding = 20;

  const validPoints = history.filter((h) => h.net_income !== null || h.fcf !== null);
  const allValues = validPoints.flatMap((h) => [h.net_income ?? 0, h.fcf ?? 0]);
  const minVal = allValues.length ? Math.min(0, ...allValues) : 0;
  const maxVal = allValues.length ? Math.max(1, ...allValues) : 1;
  const range = maxVal - minVal || 1;

  const getY = (val: number | null) => {
    if (val === null) return chartHeight - padding;
    return chartHeight - padding - ((val - minVal) / range) * (chartHeight - padding * 2);
  };

  const getX = (idx: number, count: number) => {
    if (count <= 1) return chartWidth / 2;
    return padding + (idx / (count - 1)) * (chartWidth - padding * 2);
  };

  const niPath = validPoints
    .map((p, i) => `${i === 0 ? "M" : "L"} ${getX(i, validPoints.length)} ${getY(p.net_income)}`)
    .join(" ");

  const fcfPath = validPoints
    .map((p, i) => `${i === 0 ? "M" : "L"} ${getX(i, validPoints.length)} ${getY(p.fcf)}`)
    .join(" ");

  const cardTone =
    data.sloan_signal === "red"
      ? "negative"
      : data.cash_conversion_signal === "weak"
        ? "warning"
        : "positive";

  return (
    <Card
      tone={cardTone}
      title={
        <div className="flex items-center gap-2">
          <span>Forensic Quality Suite</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-bg-2 text-ink-1 font-mono uppercase">
            Institutional Screener
          </span>
          {schilit && schilit.eqr !== null && (
            <span className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase ${schilit.eqr >= 75 ? "bg-pos-weak text-pos" : schilit.eqr >= 50 ? "bg-warn-weak text-warn" : "bg-neg-weak text-neg"}`}
              title="Earnings Quality Rating: 100 base, −25 per triggered Schilit flag">
              EQR {schilit.eqr}
            </span>
          )}
        </div>
      }
      subtitle="Audit-level accrual quality, cash conversion efficiency, and earnings divergence"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {/* Sloan Accrual */}
        <div className="p-3 bg-bg-2/50 rounded-card border border-border">
          <div className="text-xs font-medium text-ink-1 mb-1 flex items-center justify-between">
            <span>Sloan Accruals</span>
            {data.sloan_signal === "red" && (
              <Chip tone="negative" size="sm">RED FLAG</Chip>
            )}
            {data.sloan_signal === "green" && (
              <Chip tone="positive" size="sm">HEALTHY</Chip>
            )}
          </div>
          <div className="text-lg font-bold font-mono text-ink-0">
            {sloan !== null ? `${(sloan * 100).toFixed(1)}%` : "0.00"}
          </div>
          <p className="text-[11px] text-ink-2 mt-0.5 leading-relaxed">
            {sloan !== null
              ? sloan > 0.10
                ? "Aggressive accounting: net income outstrips operating cash flow by >10% of assets."
                : sloan < -0.10
                ? "Conservative: operating cash flow strongly exceeds net income."
                : "Balanced accrual drag (-10% to +10%)."
              : "Insufficient asset history"}
          </p>
        </div>

        {/* Cash Conversion */}
        <div className="p-3 bg-bg-2/50 rounded-card border border-border">
          <div className="text-xs font-medium text-ink-1 mb-1 flex items-center justify-between">
            <span>Cash Conversion (CCER)</span>
            {data.cash_conversion_signal === "weak" && (
              <Chip tone="warning" size="sm">WEAK (&lt;70%)</Chip>
            )}
            {data.cash_conversion_signal === "healthy" && (
              <Chip tone="positive" size="sm">HEALTHY</Chip>
            )}
          </div>
          <div className="text-lg font-bold font-mono text-ink-0">
            {ccer !== null ? `${Math.round(ccer * 100)}%` : "0.00"}
          </div>
          <p className="text-[11px] text-ink-2 mt-0.5 leading-relaxed">
            {ccer !== null
              ? ccer >= 1.0
                ? "Free cash flow fully backs or exceeds accounting net income."
                : ccer >= 0.70
                ? "Adequate cash conversion efficiency."
                : "Weak cash conversion: earnings not translating to cash."
              : "Net income non-positive or FCF unavailable"}
          </p>
        </div>

        {/* TTM ROIC */}
        <div className="p-3 bg-bg-2/50 rounded-card border border-border">
          <div className="text-xs font-medium text-ink-1 mb-1 flex items-center justify-between">
            <span>TTM ROIC</span>
            {roic !== null && roic >= 0.15 && data.roic_confidence !== "low" && (
              <Chip tone="positive" size="sm">MOAT (≥15%)</Chip>
            )}
            {data.roic_confidence === "low" && (
              <Chip
                tone="warning"
                size="sm"
                title="ROIC distorted - denominator small/buybacks. High ROIC driven by low book equity from share repurchases or cash offsets; evaluate alongside ROE, ROA, and FCF margin."
              >
                ROIC distorted
              </Chip>
            )}
            {data.roic_interpretation === "not_meaningful" && (
              <Chip tone="neutral" size="sm" title="Corporate ROIC is not meaningful for banks/insurers - use CET1, efficiency, and ROE instead.">n/m</Chip>
            )}
          </div>
          <div className="text-lg font-bold font-mono text-ink-0">
            {roic !== null ? `${(roic * 100).toFixed(1)}%` : "0.00"}
          </div>
          <p className="text-[11px] text-ink-2 mt-0.5 leading-relaxed">
            NOPAT / (Total Debt + Equity − Cash)
            {data.roic_confidence === "low" &&
              " High ROIC reflects low book equity (buybacks/cash offsets), not necessarily operational returns."
            }
          </p>
        </div>

        {/* FCF Yield */}
        <div className="p-3 bg-bg-2/50 rounded-card border border-border">
          <div className="text-xs font-medium text-ink-1 mb-1 flex items-center justify-between">
            <span>FCF Yield</span>
          </div>
          <div className="text-lg font-bold font-mono text-ink-0">
            {fcfYield !== null ? `${(fcfYield * 100).toFixed(1)}%` : "0.00"}
          </div>
          <p className="text-[11px] text-ink-2 mt-0.5 leading-relaxed">
            Free cash flow relative to market capitalization
          </p>
        </div>
      </div>

      {/* Trajectory SVG */}
      <div className="p-4 bg-bg-2/40 rounded-card border border-border">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <span className="text-xs font-semibold text-ink-0">
            5-Year Free Cash Flow vs. Net Income Trajectory
          </span>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-pos inline-block" />
              <span className="text-ink-1">Free Cash Flow</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-info inline-block" />
              <span className="text-ink-1">Net Income</span>
            </span>
          </div>
        </div>

        <div className="w-full flex justify-center py-1">
          <svg
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            className="w-full max-w-lg h-32 overflow-visible"
            role="img"
            aria-label="5-year trajectory comparison of Free Cash Flow versus Net Income"
          >
            {/* Zero or Baseline Axis */}
            <line
              x1={padding}
              y1={getY(0)}
              x2={chartWidth - padding}
              y2={getY(0)}
              stroke="var(--border-strong)"
              strokeWidth="1"
              strokeDasharray="3 3"
            />

            {/* Net Income Line */}
            {validPoints.length > 1 && (
              <path
                d={niPath}
                fill="none"
                stroke="var(--info)"
                strokeWidth="2"
                strokeDasharray="4 2"
              />
            )}

            {/* Free Cash Flow Line */}
            {validPoints.length > 1 && (
              <path
                d={fcfPath}
                fill="none"
                stroke="var(--pos)"
                strokeWidth="2.5"
              />
            )}

            {/* Data Points */}
            {validPoints.map((p, i) => {
              const x = getX(i, validPoints.length);
              const yNI = getY(p.net_income);
              const yFCF = getY(p.fcf);
              return (
                <g key={p.fiscal_year}>
                  {p.net_income !== null && (
                    <circle cx={x} cy={yNI} r="3" fill="var(--info)" />
                  )}
                  {p.fcf !== null && (
                    <circle cx={x} cy={yFCF} r="3.5" fill="var(--pos)" />
                  )}
                  <text
                    x={x}
                    y={chartHeight - 4}
                    textAnchor="middle"
                    className="font-mono text-[9px] fill-ink-2"
                  >
                    {p.fiscal_year}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </Card>
  );
};