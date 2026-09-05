import Tooltip from "../ui/Tooltip";

export interface ReverseDcfRuleBoxProps {
  currentPrice: number | null | undefined;
  currency: string;
  companyName: string;
  impliedCagr: number | null | undefined; // Required 10Y FCF CAGR to justify price
  historicalCagr: number | null | undefined; // Actual 5Y FCF CAGR
  className?: string;
}

export function ReverseDcfRuleBox({
  currentPrice,
  currency,
  companyName,
  impliedCagr,
  historicalCagr,
  className = "",
}: ReverseDcfRuleBoxProps) {
  const priceFormatted =
    currentPrice != null ? `$${currentPrice.toFixed(2)} ${currency}` : `current price`;
  const impliedFormatted =
    impliedCagr != null ? `${impliedCagr > 0 ? "+" : ""}${impliedCagr.toFixed(1)}%` : null;
  const histFormatted =
    historicalCagr != null ? `${historicalCagr > 0 ? "+" : ""}${historicalCagr.toFixed(1)}%` : null;

  const gap =
    impliedCagr != null && historicalCagr != null ? impliedCagr - historicalCagr : null;
  const isPricedForPerfection = gap != null && gap > 4;
  const isFairOrUndervalued = gap != null && gap <= 2;

  return (
    <div
      className={`rounded-card border border-border bg-bg-1 p-4 shadow-card transition-colors ${className}`}
    >
      <div className="flex items-center justify-between gap-2 border-b border-border/70 pb-2 mb-3">
        <div className="flex items-center gap-1.5">
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-accent">
            The Market's Expectation (Reverse DCF Rule)
          </span>
          <Tooltip term="reverse_dcf" />
        </div>
        <span className="font-mono text-[11px] text-ink-2">10-Year Horizon</span>
      </div>

      <div className="rounded border border-border/80 bg-bg-0 p-3.5 relative overflow-hidden">
        <div
          className="absolute left-0 top-0 bottom-0 w-1 bg-accent"
          aria-hidden="true"
        />
        <p className="font-display italic text-sm sm:text-base text-ink-0 leading-relaxed pl-2">
          &ldquo;To justify today's price of{" "}
          <strong className="font-semibold font-mono text-accent not-italic">
            {priceFormatted}
          </strong>
          , {companyName} must grow its free cash flow by{" "}
          <strong className="font-semibold font-mono text-accent not-italic">
            {impliedFormatted ?? "—"}
          </strong>{" "}
          every year for the next 10 years.
          {historicalCagr != null && (
            <>
              {" "}
              Over the last 5 years, it actually compounded cash flow at{" "}
              <strong className="font-semibold font-mono text-ink-0 not-italic">
                {histFormatted}
              </strong>{" "}
              annually.
            </>
          )}
          &rdquo;
        </p>

        {gap != null && (
          <div className="mt-3 pt-2.5 border-t border-border/60 flex flex-wrap items-center justify-between gap-2 pl-2">
            <span className="text-xs text-ink-1">
              Hurdle Gap:{" "}
              <strong
                className={`font-mono font-semibold ${
                  isPricedForPerfection
                    ? "text-warn"
                    : isFairOrUndervalued
                    ? "text-pos"
                    : "text-ink-0"
                }`}
              >
                {gap > 0 ? `+${gap.toFixed(1)}%` : `${gap.toFixed(1)}%`} vs history
              </strong>{" "}
              ({isPricedForPerfection
                ? "Priced for perfection / high growth required"
                : isFairOrUndervalued
                ? "Achievable hurdle within historical track record"
                : "Moderate growth demand"})
            </span>
            <span
              className={`rounded-chip px-2 py-0.5 font-mono text-[10px] font-semibold border ${
                isFairOrUndervalued
                  ? "bg-pos-weak border-pos/40 text-pos"
                  : isPricedForPerfection
                  ? "bg-warn-weak border-warn/40 text-warn"
                  : "bg-info-weak border-info/40 text-info"
              }`}
            >
              {isFairOrUndervalued ? "FAVORABLE HURDLE" : isPricedForPerfection ? "HIGH BAR" : "BALANCED BAR"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default ReverseDcfRuleBox;
