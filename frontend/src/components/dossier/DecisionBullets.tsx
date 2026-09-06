import type { BearCaseOut } from "../../api/types";

export interface DecisionBulletsProps {
  strengths: string[];
  keyRisk: string;
  expectedReturn?: number | null; // e.g. 10.8
  indexBaseline?: number; // default 8.0% for S&P 500 / TSX
  currency?: string;
  bearCase?: BearCaseOut | null;
  className?: string;
}

export function DecisionBullets({
  strengths = [],
  keyRisk,
  expectedReturn,
  indexBaseline = 8.0,
  currency = "USD",
  bearCase,
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
        <span className="font-mono text-[10px] text-ink-2">Equal-Billing Bull vs. Bear Counter-Weight</span>
      </div>

      {/* Structural Equal-Billing Layout (US-0705 & US-0074) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Bull Case / Investment Thesis Highlights */}
        <div
          data-testid="bull-case-panel"
          className="rounded border border-pos/30 bg-bg-0 p-3.5 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between border-b border-border/60 pb-2 mb-2.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-pos font-heading">
                <span className="h-2 w-2 rounded-full bg-pos" aria-hidden="true" />
                <span>Why Buy (Core Strengths)</span>
              </div>
              <span className="rounded-chip bg-pos-weak border border-pos/30 px-2 py-0.5 font-mono text-[10px] font-bold text-pos">
                Bull Case
              </span>
            </div>
            {strengths.length > 0 ? (
              <ul className="space-y-2 text-xs text-ink-0">
                {strengths.slice(0, 3).map((st, i) => (
                  <li key={i} className="flex items-start gap-2 leading-snug">
                    <span className="font-mono text-[10px] font-bold text-pos shrink-0 mt-0.5">#{i + 1}</span>
                    <span>{st}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-ink-2">Evaluating core qualitative strengths…</p>
            )}
          </div>

          {/* Index Opportunity Cost */}
          <div className="mt-3 pt-2.5 border-t border-border/60 text-xs text-ink-1">
            <div className="flex items-center justify-between font-mono text-[11px] mb-1">
              <span className="text-ink-2">Index Hurdle Baseline:</span>
              <span className="text-ink-0 font-semibold">{currency === "CAD" ? "TSX 60" : "S&P 500"} ({indexBaseline.toFixed(1)}%)</span>
            </div>
            {expectedReturn != null && (
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-ink-2">Expected Hurdle Return:</span>
                <span className={`font-semibold ${hurdleBeaten ? "text-pos" : "text-warn"}`}>
                  {expectedReturn.toFixed(1)}% {hurdleMargin != null ? `(${hurdleMargin >= 0 ? "+" : ""}${hurdleMargin.toFixed(1)}% spread)` : ""}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Bear Case / Case Against This Stock (US-0074 & US-0705) */}
        <div
          data-testid="bear-case-panel"
          className="rounded border border-neg/30 bg-bg-0 p-3.5 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between border-b border-border/60 pb-2 mb-2.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-neg font-heading">
                <span className="h-2 w-2 rounded-full bg-neg" aria-hidden="true" />
                <span>Case Against This Stock (Key Vulnerabilities)</span>
              </div>
              <span className="rounded-chip bg-neg-weak border border-neg/30 px-2 py-0.5 font-mono text-[10px] font-bold text-neg">
                Bear Case
              </span>
            </div>

            {/* Synthesized Bear Thesis */}
            <p className="text-xs text-ink-0 leading-relaxed mb-3">
              {bearCase?.bear_thesis_narrative || keyRisk || "Vulnerability to macro downturns, margin pressure, or customer concentration."}
            </p>

            {/* 3 Lowest Percentiles */}
            {bearCase?.lowest_3_percentiles && bearCase.lowest_3_percentiles.length > 0 && (
              <div className="space-y-1.5 mb-2.5">
                <span className="block font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold">
                  Bottom Percentile Metrics (Sector-Relative):
                </span>
                <div className="space-y-1">
                  {bearCase.lowest_3_percentiles.slice(0, 3).map((lp) => (
                    <div
                      key={lp.metric_id}
                      className="flex items-center justify-between rounded bg-bg-1 px-2 py-1 text-[11px] font-mono border border-border/40"
                    >
                      <span className="text-ink-1 font-sans">{lp.label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-ink-2 text-[10px]">{lp.rank_descriptor}</span>
                        <span className="rounded bg-neg/10 text-neg px-1.5 py-0.2 text-[10px] font-bold">
                          Bottom {lp.percentile.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Forensic Flags if present */}
            {bearCase?.forensic_flags && bearCase.forensic_flags.length > 0 && (
              <div className="mt-2 space-y-1">
                {bearCase.forensic_flags.map((ff, idx) => (
                  <div key={idx} className="rounded bg-neg-weak/50 border border-neg/30 px-2 py-1 text-[10px] text-neg font-mono">
                    ⚠️ {ff.flag} ({ff.model}): {ff.detail} [FPR: {ff.false_positive_rate}]
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-3 pt-2.5 border-t border-border/60 text-[11px] text-ink-2 italic font-sans">
            "Automated counter-weight synthesized from weakest relative metrics to prevent confirmation bias."
          </div>
        </div>
      </div>
    </div>
  );
}

export default DecisionBullets;
