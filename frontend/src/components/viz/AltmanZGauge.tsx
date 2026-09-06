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
                {scoreVal != null ? scoreVal.toFixed(2) : "0.00"}
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
        <div className="relative pt-4 pb-2" role="img" aria-label="Altman Z-Score Meter">
          {/* Active pointer needle */}
          {scoreVal != null && (
            <div
              className="absolute top-0 -translate-x-1/2 flex flex-col items-center transition-all duration-500 z-20"
              style={{ left: `${needlePct}%` }}
            >
              <span className="font-mono text-[10px] font-bold text-ink-0 bg-surface-1 px-1 rounded shadow-sm border border-border">
                {scoreVal.toFixed(2)}
              </span>
              <svg width="10" height="6" viewBox="0 0 10 6" className="text-ink-0 fill-current">
                <polygon points="5,6 0,0 10,0" />
              </svg>
            </div>
          )}

          {/* Segmented Track */}
          <div className="h-4 w-full flex rounded-full overflow-hidden border border-border/60 bg-surface-2">
            <div
              style={{ width: `${distressWidthPct}%` }}
              className="h-full bg-neg/80 relative"
              title={`Distress Zone (< ${distressMax})`}
            />
            <div
              style={{ width: `${greyWidthPct}%` }}
              className="h-full bg-warn/80 relative"
              title={`Grey Zone (${distressMax} - ${greyMax})`}
            />
            <div
              style={{ width: `${safeWidthPct}%` }}
              className="h-full bg-pos/80 relative"
              title={`Safe Zone (> ${greyMax})`}
            />
          </div>

          {/* Scale Labels */}
          <div className="flex justify-between text-[10px] text-ink-2 font-mono mt-1 px-1">
            <span className="text-neg">0.0 (Distress)</span>
            <span className="text-warn">{distressMax.toFixed(2)}</span>
            <span className="text-pos">{greyMax.toFixed(2)}+ (Safe)</span>
          </div>
        </div>

        {/* Factor Breakdown */}
        {distress.factors && (
          <div className="pt-2 border-t border-border grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-ink-2">WC / Total Assets:</span>{" "}
              <span className="font-mono font-medium text-ink-0">
                {distress.factors.x1_working_capital_to_ta != null ? distress.factors.x1_working_capital_to_ta.toFixed(2) : "0.00"}
              </span>
            </div>
            <div>
              <span className="text-ink-2">Equity / Total Assets:</span>{" "}
              <span className="font-mono font-medium text-ink-0">
                {distress.factors.x2_retained_earnings_to_ta != null ? distress.factors.x2_retained_earnings_to_ta.toFixed(2) : "0.00"}
              </span>
            </div>
            <div>
              <span className="text-ink-2">EBIT / Total Assets:</span>{" "}
              <span className="font-mono font-medium text-ink-0">
                {distress.factors.x3_ebit_to_ta != null ? distress.factors.x3_ebit_to_ta.toFixed(2) : "0.00"}
              </span>
            </div>
            <div>
              <span className="text-ink-2">Equity / Total Liab:</span>{" "}
              <span className="font-mono font-medium text-ink-0">
                {distress.factors.x4_market_equity_to_tl != null ? distress.factors.x4_market_equity_to_tl.toFixed(2) : "0.00"}
              </span>
            </div>
            {isMfg && (
              <div className="col-span-2">
                <span className="text-ink-2">Sales / Total Assets (Turnover):</span>{" "}
                <span className="font-mono font-medium text-ink-0">
                  {distress.factors.x5_sales_to_ta != null ? distress.factors.x5_sales_to_ta.toFixed(2) : "0.00"}
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