import Tooltip from "../ui/Tooltip";

export interface PenmanDecompositionTableProps {
  rnoa?: number | null; // Core Operating Return
  flev?: number | null; // Financial Leverage Multiplier
  nbc?: number | null; // Net Borrowing Cost
  spread?: number | null; // Operating Spread (RNOA - NBC)
  roe?: number | null; // Return on Equity
  distortionAlert?: string | null; // Buyback distortion / negative equity warning
  className?: string;
}

export function PenmanDecompositionTable({
  rnoa,
  flev,
  nbc,
  spread,
  roe,
  distortionAlert,
  className = "",
}: PenmanDecompositionTableProps) {
  const calcSpread = spread ?? (rnoa != null && nbc != null ? rnoa - nbc : null);
  const isHealthySpread = calcSpread != null && calcSpread > 0;
  const isLeverageDangerous = flev != null && flev > 2.5;

  return (
    <div
      className={`rounded-card border border-border bg-bg-1 p-4 shadow-card transition-colors ${className}`}
    >
      <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-3">
        <div className="flex items-center gap-1.5">
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
            Stephen Penman Reformulation
          </span>
          <Tooltip term="flev" />
        </div>
        <span className="font-mono text-[10px] text-ink-2">
          Operating vs. Financing Decomposition
        </span>
      </div>

      {/* Formula Display */}
      <div className="rounded border border-border/70 bg-bg-0 p-2.5 text-center font-mono text-xs text-accent mb-3">
        <code>ROE = RNOA + [ FLEV × (RNOA - NBC) ]</code>
      </div>

      {/* Ratios Breakdown */}
      <div className="space-y-2 font-mono text-xs">
        <div className="flex items-center justify-between py-1 border-b border-border/40">
          <span className="text-ink-1">RNOA (Core Operating Return):</span>
          <span className="font-bold text-ink-0">
            {rnoa != null ? `${(rnoa * (rnoa < 1 ? 100 : 1)).toFixed(1)}%` : "—"}
          </span>
        </div>

        <div className="flex items-center justify-between py-1 border-b border-border/40">
          <span className="text-ink-1">FLEV (Debt Leverage Multiplier):</span>
          <span
            className={`font-bold ${
              isLeverageDangerous ? "text-warn" : "text-ink-0"
            }`}
          >
            {flev != null ? `${flev.toFixed(2)}x` : "—"}
          </span>
        </div>

        <div className="flex items-center justify-between py-1 border-b border-border/40">
          <span className="text-ink-1">NBC (Net Borrowing Cost):</span>
          <span className="text-ink-0">
            {nbc != null ? `${(nbc * (nbc < 1 ? 100 : 1)).toFixed(1)}%` : "—"}
          </span>
        </div>

        <div className="flex items-center justify-between py-1 border-b border-border/40">
          <span className="text-ink-1">Operating Spread (RNOA - NBC):</span>
          <span
            className={`font-bold ${
              isHealthySpread ? "text-pos" : "text-neg"
            }`}
          >
            {calcSpread != null ? `${(calcSpread * (calcSpread < 1 ? 100 : 1)).toFixed(1)}%` : "—"}
          </span>
        </div>

        {roe != null && (
          <div className="flex items-center justify-between py-1 pt-2 font-bold text-sm text-ink-0">
            <span>Reported ROE:</span>
            <span className="text-accent font-mono">
              {(roe * (roe < 1 ? 100 : 1)).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Buyback Distortion / Solvency Alert */}
      <div className="mt-3 pt-2.5 border-t border-border/60 flex items-center justify-between text-[11px] font-mono">
        <span className="text-ink-2">Buyback Distortion Alert:</span>
        <span
          className={`rounded-chip px-2 py-0.5 font-bold border ${
            distortionAlert
              ? "bg-warn-weak text-warn border-warn/40"
              : "bg-pos-weak text-pos border-pos/30"
          }`}
        >
          {distortionAlert ? distortionAlert.toUpperCase() : "NONE (GENUINE PROFIT)"}
        </span>
      </div>
    </div>
  );
}

export default PenmanDecompositionTable;
