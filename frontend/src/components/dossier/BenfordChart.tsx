import React from "react";
import type { BenfordOut } from "../../api/types";
import { Card } from "../layout";

interface BenfordChartProps {
  data: BenfordOut | null;
  className?: string;
}

export const BenfordChart: React.FC<BenfordChartProps> = ({ data, className = "" }) => {
  if (!data) {
    return (
      <Card title="Benford's Law - First-Digit Test" subtitle="Statistical irregularity screening (informational, not proof)">
        <p className="text-xs text-ink-2">Loading Benford analysis…</p>
      </Card>
    );
  }

  if (!data.data_available || data.observed_freq == null || data.expected_freq == null) {
    return (
      <Card title="Benford's Law - First-Digit Test" subtitle={`Observed ${data.observations}/${data.min_required} figures - insufficient data`}>
        <p className="text-xs text-ink-1 leading-relaxed">{data.interpretation}</p>
        <p className="text-[11px] font-mono text-ink-2 mt-2">{data.disclaimer}</p>
      </Card>
    );
  }

  const observed = data.observed_freq;
  const expected = data.expected_freq;
  const digits = Array.from({ length: 9 }, (_, i) => i + 1);

  // SVG dimensions
  const W = 520;
  const H = 180;
  const padLeft = 36;
  const padRight = 12;
  const padTop = 16;
  const padBottom = 28;
  const innerW = W - padLeft - padRight;
  const innerH = H - padTop - padBottom;
  const barW = innerW / 9 - 6;

  const maxVal = Math.max(
    ...digits.map((d) => Math.max(observed[String(d)] ?? 0, expected[String(d)] ?? 0)),
    0.35
  );

  const y = (v: number) => padTop + innerH - (v / maxVal) * innerH;

  const verdictTone =
    data.verdict === "conforms"
      ? "text-pos"
      : data.verdict === "deviation_noted"
        ? "text-warn"
        : "text-neg";

  return (
    <Card
      title="Benford's Law - First-Digit Distribution"
      subtitle={`χ²=${data.chi2} (df=${data.degrees_of_freedom}) - ${data.verdict.replace("_", " ")} · n=${data.observations}`}
      className={className}
    >
      <div className="space-y-3">
        <svg
          width={W}
          height={H}
          viewBox={`0 0 ${W} ${H}`}
          role="img"
          aria-label={`Benford first-digit chart - chi-square ${data.chi2} verdict ${data.verdict} over ${data.observations} figures`}
          className="w-full h-auto"
        >
          {/* grid */}
          {[0, 0.1, 0.2, 0.3].map((v) => (
            <g key={v}>
              <line
                x1={padLeft}
                x2={W - padRight}
                y1={y(v)}
                y2={y(v)}
                stroke="var(--border)"
                strokeWidth={0.7}
                strokeDasharray="3 4"
              />
              <text x={padLeft - 6} y={y(v) + 3} textAnchor="end" fontSize={9} fill="var(--ink-2)" fontFamily="IBM Plex Mono">
                {(v * 100).toFixed(0)}%
              </text>
            </g>
          ))}

          {/* Expected Benford curve line */}
          <polyline
            fill="none"
            stroke="var(--accent)"
            strokeWidth={1.6}
            strokeLinecap="round"
            strokeLinejoin="round"
            points={digits
              .map((d) => {
                const xv = padLeft + (d - 1) * (innerW / 9) + barW + 3;
                const yv = y(expected[String(d)] ?? 0);
                return `${xv.toFixed(1)},${yv.toFixed(1)}`;
              })
              .join(" ")}
            opacity={0.95}
          />
          {digits.map((d) => {
            const xv = padLeft + (d - 1) * (innerW / 9) + barW + 3;
            const yv = y(expected[String(d)] ?? 0);
            return <circle key={`exp-${d}`} cx={xv} cy={yv} r={2.2} fill="var(--accent)" />;
          })}

          {/* Bars: observed */}
          {digits.map((d) => {
            const obs = observed[String(d)] ?? 0;
            const x = padLeft + (d - 1) * (innerW / 9) + 2;
            const barH = (obs / maxVal) * innerH;
            const isHigh = obs > (expected[String(d)] ?? 0) + 0.04;
            return (
              <g key={d}>
                <rect
                  x={x}
                  y={padTop + innerH - barH}
                  width={barW}
                  height={barH}
                  rx={2}
                  fill={isHigh ? "var(--neg)" : "var(--info)"}
                  opacity={0.85}
                />
                <text
                  x={x + barW / 2}
                  y={H - 8}
                  textAnchor="middle"
                  fontSize={10}
                  fontWeight={700}
                  fill="var(--ink-1)"
                  fontFamily="IBM Plex Mono"
                >
                  {d}
                </text>
                <text
                  x={x + barW / 2}
                  y={padTop + innerH - barH - 4}
                  textAnchor="middle"
                  fontSize={8}
                  fill="var(--ink-0)"
                  fontFamily="IBM Plex Mono"
                >
                  {(obs * 100).toFixed(0)}%
                </text>
              </g>
            );
          })}
        </svg>

        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-3 font-mono text-[11px]">
            <span className="inline-flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: "var(--info)" }} /> Observed
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="w-3 h-0.5 inline-block" style={{ background: "var(--accent)" }} /> Benford expected log10(1+1/d)
            </span>
          </div>
          <span className={`font-mono font-semibold ${verdictTone}`}>{data.verdict.toUpperCase()}</span>
        </div>

        <p className="text-xs text-ink-1 leading-relaxed border-t border-border pt-2">{data.interpretation}</p>
        <p className="text-[11px] font-mono text-ink-2">{data.disclaimer}</p>
      </div>
    </Card>
  );
};

export default BenfordChart;