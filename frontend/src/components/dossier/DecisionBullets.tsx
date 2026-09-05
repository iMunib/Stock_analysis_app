export interface DecisionBulletsProps {
  strengths: string[];
  keyRisk: string;
  expectedReturn?: number | null; // e.g. 10.8
  indexBaseline?: number; // default 8.0% for S&P 500 / TSX
  currency?: string;
  className?: string;
}

export function DecisionBullets({
  strengths = [],
  keyRisk,
  expectedReturn,
  indexBaseline = 8.0,
  currency = "USD",
  className = "",
}: DecisionBulletsProps) {
  const hurdleBeaten = expectedReturn != null && expectedReturn > indexBaseline;
  const hurdleMargin = expectedReturn != null ? expectedReturn - indexBaseline : null;

  return (
    <div
      className={`rounded-card border border-border bg-bg-1 p-4 shadow-card transition-colors ${className}`}
    >
      <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-3">
        <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-2">
          Plain-English Decision Summary
        </span>
        <span className="font-mono text-[10px] text-ink-2">2-Minute Decision Filter</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 1. Why Buy / Top Strengths */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-pos font-heading">
            <span className="h-1.5 w-1.5 rounded-full bg-pos" aria-hidden="true" />
            <span>Why Buy (Core Strengths)</span>
          </div>
          {strengths.length > 0 ? (
            <ul className="space-y-1.5 text-xs text-ink-0">
              {strengths.slice(0, 3).map((st, i) => (
                <li key={i} className="flex items-start gap-1.5 leading-snug">
                  <span className="font-mono text-[10px] text-ink-2 shrink-0">{i + 1}.</span>
                  <span>{st}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-ink-2">Evaluating core qualitative strengths…</p>
          )}
        </div>

        {/* 2. Key Risk to Watch */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-warn font-heading">
            <span className="h-1.5 w-1.5 rounded-full bg-warn" aria-hidden="true" />
            <span>Key Risk to Watch</span>
          </div>
          <p className="text-xs text-ink-0 leading-relaxed font-sans">
            {keyRisk || "Vulnerability to macro downturns, margin pressure, or customer concentration."}
          </p>
        </div>

        {/* 3. Index Opportunity Cost */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-info font-heading">
            <span className="h-1.5 w-1.5 rounded-full bg-info" aria-hidden="true" />
            <span>Index Opportunity Cost</span>
          </div>
          <p className="text-xs text-ink-0 leading-relaxed font-sans">
            {expectedReturn != null ? (
              <>
                Estimated hurdle return:{" "}
                <strong className="font-mono font-semibold text-accent">
                  {expectedReturn.toFixed(1)}%
                </strong>{" "}
                vs. {currency === "CAD" ? "TSX 60" : "S&P 500"} baseline of{" "}
                <strong className="font-mono text-ink-1">{indexBaseline.toFixed(1)}%</strong>.
                {hurdleMargin != null && (
                  <span
                    className={`block mt-1 text-[11px] font-mono font-medium ${
                      hurdleBeaten ? "text-pos" : "text-warn"
                    }`}
                  >
                    {hurdleBeaten
                      ? `+${hurdleMargin.toFixed(1)}% annual premium over passive indexing`
                      : `${hurdleMargin.toFixed(1)}% lag behind passive index expectation`}
                  </span>
                )}
              </>
            ) : (
              <>
                Requires compounding capital faster than the market baseline of{" "}
                <strong className="font-mono">{indexBaseline.toFixed(1)}%</strong> nominal return to justify single-stock risk.
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}

export default DecisionBullets;
