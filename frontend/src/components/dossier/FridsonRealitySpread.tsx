import Tooltip from "../ui/Tooltip";
import { money } from "../../lib/format";

export interface FridsonRealitySpreadProps {
  ebitda?: number | null;
  cfo?: number | null;
  currency?: string;
  className?: string;
}

export function FridsonRealitySpread({
  ebitda,
  cfo,
  currency = "USD",
  className = "",
}: FridsonRealitySpreadProps) {
  const spread = ebitda != null && cfo != null ? ebitda - cfo : null;
  const spreadPct = ebitda != null && ebitda > 0 && spread != null ? (spread / ebitda) * 100 : null;

  const isHealthy = spreadPct != null && spreadPct < 25;

  return (
    <div
      className={`rounded-card border border-border bg-bg-1 p-4 shadow-card transition-colors ${className}`}
    >
      <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-3">
        <div className="flex items-center gap-1.5">
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
            Martin Fridson Reality Spread
          </span>
          <Tooltip term="fridson" />
        </div>
        <span className="font-mono text-[10px] text-ink-2">
          Earnings vs. Real Cash Flow
        </span>
      </div>

      <div className="space-y-2.5 font-mono text-xs">
        <div className="flex items-center justify-between">
          <span className="text-ink-1">EBITDA (Accounting Earnings):</span>
          <span className="font-semibold text-ink-0">
            {ebitda != null ? money(ebitda, currency) : "Not reported in filing"}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-ink-1">Cash Flow from Operations (CFO):</span>
          <span className="font-semibold text-pos">
            {cfo != null ? money(cfo, currency) : "Not reported in filing"}
          </span>
        </div>

        <div className="flex items-center justify-between border-t border-border/60 pt-2 font-bold">
          <span>Spread (EBITDA - CFO):</span>
          <span className={isHealthy ? "text-pos" : "text-warn"}>
            {spread != null ? money(spread, currency) : "Not reported in filing"}
          </span>
        </div>
      </div>

      <div className="mt-3 pt-2 border-t border-border/40 text-[11px] font-sans text-ink-2">
        {isHealthy ? (
          <span className="text-pos font-mono">
            ● Normal working capital flow: EBITDA is backed by real cash collections.
          </span>
        ) : (
          <span className="text-warn font-mono">
            ▲ Elevated spread: substantial EBITDA is trapped in uncollected receivables or inventory build.
          </span>
        )}
      </div>
    </div>
  );
}

export default FridsonRealitySpread;