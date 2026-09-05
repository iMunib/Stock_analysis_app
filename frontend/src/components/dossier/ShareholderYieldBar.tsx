import Tooltip from "../ui/Tooltip";
import { money } from "../../lib/format";

export interface ShareholderYieldBarProps {
  dividendYield?: number | null; // e.g. 0.44%
  buybackYield?: number | null; // e.g. 3.12%
  buybackDollars?: number | null;
  sbcDilutionYield?: number | null; // e.g. 0.32%
  sbcDollars?: number | null;
  netFloatShrinkPct?: number | null; // e.g. -2.8%
  currency?: string;
  className?: string;
}

export function ShareholderYieldBar({
  dividendYield = 0,
  buybackYield = 0,
  buybackDollars,
  sbcDilutionYield = 0,
  sbcDollars,
  netFloatShrinkPct,
  currency = "USD",
  className = "",
}: ShareholderYieldBarProps) {
  const divY = dividendYield ?? 0;
  const bbY = buybackYield ?? 0;
  const sbcY = sbcDilutionYield ?? 0;
  const trueYield = divY + bbY - sbcY;

  // SVG Bar calculations
  const totalPositive = Math.max(divY + bbY, 0.1);
  const divWidthPct = (divY / totalPositive) * 100;
  const bbWidthPct = (bbY / totalPositive) * 100;

  return (
    <div
      className={`rounded-card border border-border bg-bg-1 p-4 shadow-card transition-colors ${className}`}
    >
      <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-3">
        <div className="flex items-center gap-1.5">
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
            True Shareholder Yield
          </span>
          <Tooltip term="shareholder_yield" />
        </div>
        <span className="font-mono text-[10px] text-ink-2">
          Dilution-Adjusted Capital Return
        </span>
      </div>

      <div className="space-y-3">
        {/* Metric summary rows */}
        <div className="space-y-1.5 font-mono text-xs">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-ink-1">
              <span className="h-2 w-2 rounded-sm bg-info inline-block" />
              <span>Dividend Yield:</span>
            </span>
            <span className="text-ink-0 font-semibold">
              +{divY.toFixed(2)}%
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-ink-1">
              <span className="h-2 w-2 rounded-sm bg-pos inline-block" />
              <span>Gross Buyback Yield:</span>
            </span>
            <span className="text-pos font-semibold">
              +{bbY.toFixed(2)}%
              {buybackDollars != null && (
                <span className="text-[10px] text-ink-2 font-normal ml-1.5">
                  ({money(buybackDollars, currency)})
                </span>
              )}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-ink-1">
              <span className="h-2 w-2 rounded-sm bg-neg inline-block" />
              <span>Less: SBC Dilution:</span>
            </span>
            <span className="text-neg font-semibold">
              -{sbcY.toFixed(2)}%
              {sbcDollars != null && (
                <span className="text-[10px] text-ink-2 font-normal ml-1.5">
                  ({money(sbcDollars, currency)})
                </span>
              )}
            </span>
          </div>
        </div>

        {/* Pure SVG Stacked Bar Visualizing Yield Components */}
        <div className="pt-2">
          <svg
            className="w-full h-5 rounded overflow-hidden"
            viewBox="0 0 100 16"
            preserveAspectRatio="none"
            role="img"
            aria-label={`True shareholder yield composition: dividends ${divY.toFixed(2)}%, buybacks ${bbY.toFixed(2)}%`}
          >
            {/* Background */}
            <rect width="100" height="16" fill="var(--bg-2)" />
            {/* Dividend chunk */}
            {divY > 0 && (
              <rect
                x="0"
                y="0"
                width={Math.min(divWidthPct, 100)}
                height="16"
                fill="var(--info)"
                opacity="0.9"
              />
            )}
            {/* Buyback chunk */}
            {bbY > 0 && (
              <rect
                x={divWidthPct}
                y="0"
                width={Math.min(bbWidthPct, 100 - divWidthPct)}
                height="16"
                fill="var(--pos)"
                opacity="0.9"
              />
            )}
          </svg>
          <div className="flex justify-between text-[10px] font-mono text-ink-2 mt-1">
            <span>0%</span>
            <span>Dividends + Repurchases</span>
            <span>Total Gross: {(divY + bbY).toFixed(2)}%</span>
          </div>
        </div>

        {/* Bottom Total Result */}
        <div className="border-t border-border/80 pt-2.5 flex items-center justify-between">
          <div>
            <span className="font-heading text-xs font-bold text-ink-0">
              True Shareholder Yield:
            </span>
            {netFloatShrinkPct != null && (
              <span className="block font-mono text-[10px] text-ink-2">
                Net Share Float Shrink: {netFloatShrinkPct.toFixed(1)}%/yr
              </span>
            )}
          </div>
          <div className="text-right">
            <span
              className={`font-mono text-base font-bold ${
                trueYield >= 3.0 ? "text-pos" : trueYield > 0 ? "text-accent" : "text-neg"
              }`}
            >
              {trueYield.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ShareholderYieldBar;
