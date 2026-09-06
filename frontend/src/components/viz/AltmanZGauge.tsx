import React from "react";
import type { DistressAnalysis } from "../../api/types";
import { Card } from "../layout";

interface AltmanZGaugeProps {
  distress: DistressAnalysis | null | undefined;
  className?: string;
}

export const AltmanZGauge: React.FC<AltmanZGaugeProps> = ({
  distress,
  className = "",
}) => {
  if (!distress) {
    return (
      <Card
        title="Altman Solvency & Distress"
        subtitle="Capital structure & bankruptcy risk gauge"
        padding="sm"
        className={className}
      >
        <div className="py-6 text-center text-xs text-ink-2">
          Altman Z distress analysis unavailable.
        </div>
      </Card>
    );
  }

  if (distress.status === "financial_institution_excluded" || distress.zone === "Excluded" || (distress as any).is_bank) {
    return (
      <Card
        title="Altman Solvency & Distress"
        subtitle="Capital structure & bankruptcy risk gauge"
        padding="md"
        className={className}
      >
        <div className="py-4 px-3 rounded border border-border bg-surface-2 text-xs text-ink-1 flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-info" />
          <span>
            <strong>Bank / Insurer Excluded:</strong> Excluded from corporate Altman Z-score models because bank/insurance liability structures do not reflect corporate insolvency mechanics.
          </span>
        </div>
      </Card>
    );
  }

  const isMfg = distress.model_used === "manufacturing";
  const scoreVal = distress.active_z ?? (isMfg ? distress.z_score : distress.z_double_prime);

  // Define scale thresholds
  // For classic Z: Distress < 1.81, Grey 1.81-2.99, Safe > 2.99. Range 0 to 5.0.
  // For Z'': Distress < 1.10, Grey 1.10-2.60, Safe > 2.60. Range 0 to 5.0.
  const distressMax = isMfg ? 1.81 : 1.10;
  const greyMax = isMfg ? 2.99 : 2.60;
  const scaleMax = 5.0;

  // Percentage widths on a 0 to 5.0 scale
  const distressWidthPct = (distressMax / scaleMax) * 100;
  const greyWidthPct = ((greyMax - distressMax) / scaleMax) * 100;
  const safeWidthPct = 100 - distressWidthPct - greyWidthPct;

  // Pointer position clamped 0-100%
  const normalizedVal = scoreVal != null ? Math.max(0, Math.min(scaleMax, scoreVal)) : 0;
  const needlePct = (normalizedVal / scaleMax) * 100;

  const zoneColor =
    distress.zone === "Safe"
      ? "text-pos"
      : distress.zone === "Grey"
        ? "text-warn"
        : "text-neg";

  const zoneBadgeBg =
    distress.zone === "Safe"
      ? "bg-pos-weak text-pos border-pos/30"
      : distress.zone === "Grey"
        ? "bg-warn-weak text-warn border-warn/30"
        : "bg-neg-weak text-neg border-neg/30";

  const getFactor = (longKey: string, shortKey: string) => {
    if (!distress?.factors) return "—";
    const f = distress.factors as Record<string, any>;
    const val = f[longKey] ?? f[shortKey];
    return typeof val === "number" && !isNaN(val) ? val.toFixed(2) : "—";
  };

  return (
    <Card
      title="Altman Solvency & Distress"
      subtitle={`${isMfg ? "Classic 5-Factor Z-Score (Manufacturing)" : "4-Factor Z''-Score (Service & Tech)"}`}
      padding="md"
      className={className}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-baseline gap-2">
              <span className={`font-mono text-2xl font-bold ${zoneColor}`}>
                {scoreVal != null ? scoreVal.toFixed(2) : "—"}
              </span>
              <span className="text-xs text-ink-2 font-mono">Score</span>
            </div>
            <p className="text-[11px] text-ink-1 mt-0.5">
              Model: <span className="font-semibold text-ink-0">{isMfg ? "Manufacturing (Z)" : "Service / Tech (Z'')" }</span>
            </p>
          </div>

          <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${zoneBadgeBg}`}>
            {distress.zone} Zone
          </span>
        </div>

        {/* Segmented Meter */}
        <div className="relative pt-5 pb-2" role="img" aria-label="Altman Z-Score Meter">
          {/* Active pointer needle */}
          {scoreVal != null && (
            <div
              className="absolute top-0 -translate-x-1/2 flex flex-col items-center transition-all duration-700 z-20"
              style={{ left: `${needlePct}%` }}
            >
              <span className="font-mono text-[10px] font-bold text-ink-0 bg-bg-2 px-1.5 py-0.5 rounded shadow-sm border border-accent/40 text-accent">
                {scoreVal.toFixed(2)}
              </span>
              <svg width="10" height="6" viewBox="0 0 10 6" className="text-accent fill-current drop-shadow-xs">
                <polygon points="5,6 0,0 10,0" />
              </svg>
            </div>
          )}

          {/* Segmented Track with 3D depth and subtle inner bevel */}
          <div className="h-4 w-full flex rounded-full overflow-hidden border border-border/80 bg-bg-0 shadow-inner">
            <div
              style={{ width: `${distressWidthPct}%` }}
              className="h-full bg-gradient-to-r from-red-700 to-red-500 relative border-r border-black/30"
              title={`Distress Zone (< ${distressMax})`}
            />
            <div
              style={{ width: `${greyWidthPct}%` }}
              className="h-full bg-gradient-to-r from-amber-600 to-amber-400 relative border-r border-black/30"
              title={`Grey Zone (${distressMax} - ${greyMax})`}
            />
            <div
              style={{ width: `${safeWidthPct}%` }}
              className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 relative"
              title={`Safe Zone (> ${greyMax})`}
            />
          </div>

          {/* Scale Labels */}
          <div className="flex justify-between text-[10px] text-ink-2 font-mono mt-1.5 px-1 font-medium">
            <span className="text-neg">0.0 (Distress)</span>
            <span className="text-warn">{distressMax.toFixed(2)}</span>
            <span className="text-pos">{greyMax.toFixed(2)}+ (Safe)</span>
          </div>
        </div>

        {/* Factor Breakdown */}
        {distress.factors && (
          <div className="pt-3 border-t border-border grid grid-cols-2 gap-2 text-[11px]">
            <div className="rounded bg-bg-2/50 p-2 border border-border/50">
              <span className="text-ink-2 block text-[10px] uppercase font-mono">WC / Total Assets</span>
              <span className="font-mono font-semibold text-ink-0 text-xs">
                {getFactor("x1_working_capital_to_ta", "x1_wc_ta")}
              </span>
            </div>
            <div className="rounded bg-bg-2/50 p-2 border border-border/50">
              <span className="text-ink-2 block text-[10px] uppercase font-mono">Retained / Total Assets</span>
              <span className="font-mono font-semibold text-ink-0 text-xs">
                {getFactor("x2_retained_earnings_to_ta", "x2_re_ta")}
              </span>
            </div>
            <div className="rounded bg-bg-2/50 p-2 border border-border/50">
              <span className="text-ink-2 block text-[10px] uppercase font-mono">EBIT / Total Assets</span>
              <span className="font-mono font-semibold text-ink-0 text-xs">
                {getFactor("x3_ebit_to_ta", "x3_ebit_ta")}
              </span>
            </div>
            <div className="rounded bg-bg-2/50 p-2 border border-border/50">
              <span className="text-ink-2 block text-[10px] uppercase font-mono">Equity / Total Liab</span>
              <span className="font-mono font-semibold text-ink-0 text-xs">
                {getFactor("x4_market_equity_to_tl", "x4_bve_tl")}
              </span>
            </div>
            {isMfg && (
              <div className="col-span-2 rounded bg-bg-2/50 p-2 border border-border/50">
                <span className="text-ink-2 block text-[10px] uppercase font-mono">Sales / Total Assets (Turnover)</span>
                <span className="font-mono font-semibold text-ink-0 text-xs">
                  {getFactor("x5_sales_to_ta", "x5_sales_ta")}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default AltmanZGauge;