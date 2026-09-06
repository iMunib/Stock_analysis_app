import Tooltip from "../ui/Tooltip";
import { money } from "../../lib/format";

export interface LynchArchetypeCardProps {
  archetype?: string | null;
  epsGrowth5y?: number | null;
  peRatio?: number | null;
  pegRatio?: number | null;
  netIncome?: number | null;
  depreciation?: number | null;
  capex?: number | null;
  ownerEarnings?: number | null;
  ownerEarningsYield?: number | null;
  currency?: string;
  className?: string;
}

export function LynchArchetypeCard({
  archetype = "STALWART COMPOUNDER",
  epsGrowth5y,
  peRatio,
  pegRatio,
  netIncome,
  depreciation,
  capex,
  ownerEarnings,
  ownerEarningsYield,
  currency = "USD",
  className = "",
}: LynchArchetypeCardProps) {
  // Determine PEG valuation commentary
  const pegComment =
    pegRatio != null
      ? pegRatio < 1.0
        ? "Undervalued for growth rate"
        : pegRatio <= 1.8
        ? "Fair growth valuation"
        : "Stretched valuation / Premium"
      : "Insufficient growth history";

  const calcOwnerEarnings =
    ownerEarnings != null
      ? ownerEarnings
      : netIncome != null
      ? netIncome + (depreciation ?? 0) - (capex ?? 0)
      : null;

  return (
    <div
      className={`rounded-card border border-border bg-bg-1 p-4 shadow-card transition-colors ${className}`}
    >
      <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-3">
        <div className="flex items-center gap-1.5">
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
            Peter Lynch Archetype & Valuation
          </span>
          <Tooltip term="owner_earnings" />
        </div>
        <span className="font-mono text-[10px] text-ink-2">Rule of Thumb Matrix</span>
      </div>

      <div className="space-y-4">
        {/* Classification Badge */}
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block mb-1">
            Classification:
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-card border border-accent/40 bg-accent-weak px-3 py-1 font-mono text-xs font-bold text-accent">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
            {archetype ? archetype.toUpperCase() : "STALWART COMPOUNDER"}
          </span>
        </div>

        {/* Core Ratios */}
        <div className="grid grid-cols-3 gap-2 border-y border-border/60 py-2.5">
          <div>
            <span className="text-[10px] font-mono text-ink-2 block">5Y EPS CAGR</span>
            <span className="font-mono text-xs font-semibold text-ink-0">
              {epsGrowth5y != null ? `${epsGrowth5y > 0 ? "+" : ""}${epsGrowth5y.toFixed(1)}%` : "0.00"}
            </span>
          </div>
          <div>
            <span className="text-[10px] font-mono text-ink-2 block">Trailing P/E</span>
            <span className="font-mono text-xs font-semibold text-ink-0">
              {peRatio != null ? `${peRatio.toFixed(1)}x` : "0.00"}
            </span>
          </div>
          <div>
            <span className="text-[10px] font-mono text-ink-2 block">PEG Ratio</span>
            <span
              className={`font-mono text-xs font-semibold ${
                pegRatio != null && pegRatio <= 1.2
                  ? "text-pos"
                  : pegRatio != null && pegRatio > 2.0
                  ? "text-warn"
                  : "text-ink-0"
              }`}
            >
              {pegRatio != null ? pegRatio.toFixed(2) : "0.00"}
            </span>
          </div>
        </div>

        <div className="text-[11px] text-ink-2 font-mono">
          PEG Verdict: <span className="text-ink-1">{pegComment}</span>
        </div>

        {/* Buffett Owner Earnings Breakdown */}
        <div className="rounded border border-border/60 bg-bg-0 p-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="font-heading font-semibold text-ink-0">
              Buffett Owner Earnings
            </span>
            {ownerEarningsYield != null && (
              <span className="font-mono text-[11px] font-bold text-accent">
                Yield: {ownerEarningsYield.toFixed(2)}%
              </span>
            )}
          </div>
          <div className="text-[11px] font-mono text-ink-2 space-y-1">
            <div className="flex justify-between">
              <span>Net Income:</span>
              <span className="text-ink-0 font-medium">
                {netIncome != null ? money(netIncome, currency) : "Not reported in filing"}
              </span>
            </div>
            {capex != null && (
              <div className="flex justify-between">
                <span>Maint. CapEx:</span>
                <span className="text-ink-1">
                  -{money(Math.abs(capex), currency)}
                </span>
              </div>
            )}
            <div className="flex justify-between border-t border-border/50 pt-1 text-ink-0 font-semibold">
              <span>Owner Earnings:</span>
              <span className="text-accent">
                {calcOwnerEarnings != null
                  ? money(calcOwnerEarnings, currency)
                  : "Not reported in filing"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LynchArchetypeCard;