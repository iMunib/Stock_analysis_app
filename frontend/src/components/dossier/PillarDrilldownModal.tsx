import { useEffect, useState } from "react";
import type { PillarDetail, PillarDrilldownOut } from "../../api/types";
import { ScoreBar } from "../bars";

export interface PillarDrilldownModalProps {
  isOpen: boolean;
  onClose: () => void;
  pillarKey: "quality" | "value" | "growth" | "risk";
  drilldown: PillarDrilldownOut | null;
  companyName?: string;
  currency?: string;
}

export function PillarDrilldownModal({
  isOpen,
  onClose,
  pillarKey,
  drilldown,
  companyName = "Company",
  currency = "USD",
}: PillarDrilldownModalProps) {
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !drilldown) return null;

  const pillar: PillarDetail | undefined = drilldown.pillars[pillarKey];
  if (!pillar) return null;

  const titleMap = {
    quality: "Quality Pillar Methodology & Exact Breakdown",
    value: "Value Pillar Methodology & Peer Percentiles",
    growth: "Growth Pillar Methodology & Multi-Year CAGRs",
    risk: "Risk Pillar Methodology & Solvency Decomposition",
  };

  const weightMap = {
    quality: "30% of Composite Score",
    value: "25% of Composite Score",
    growth: "25% of Composite Score",
    risk: "20% of Composite Score (Inverted: High = Safe)",
  };

  const toggleMetric = (id: string) => {
    setExpandedMetric(expandedMetric === id ? null : id);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="pillar-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <div className="relative max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-card border border-border bg-bg-1 p-6 shadow-modal transition-all">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-border/80 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-accent">
                {pillarKey.toUpperCase()} DRILLDOWN
              </span>
              <span className="rounded bg-bg-2 px-2 py-0.5 font-mono text-[10px] text-ink-2">
                {weightMap[pillarKey]}
              </span>
            </div>
            <h2 id="pillar-modal-title" className="font-heading text-lg font-bold text-ink-0 mt-1">
              {titleMap[pillarKey]}
            </h2>
            <p className="font-mono text-xs text-ink-2 mt-0.5">
              {companyName} · Denominated in {currency} · Math Engine v1
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1.5 text-ink-2 hover:bg-bg-2 hover:text-ink-0 transition-colors"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Score & Peer Median Banner */}
        <div className="my-4 rounded-card border border-border bg-bg-0 p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="font-mono text-[10px] uppercase text-ink-2">Calculated Score</span>
              <div className="font-mono text-2xl font-bold text-ink-0">
                {pillar.score != null ? `${pillar.score.toFixed(1)} / 10` : "- / 10"}
              </div>
            </div>
            {pillar.sector_median != null && (
              <div className="text-right">
                <span className="font-mono text-[10px] uppercase text-ink-2">Sector Peer Median</span>
                <div className="font-mono text-lg font-semibold text-accent">
                  {pillar.sector_median.toFixed(1)} / 10
                </div>
              </div>
            )}
          </div>
          <div className="mt-3">
            <ScoreBar
              value={pillar.score}
              median={pillar.sector_median}
              label={`${pillarKey.toUpperCase()} Score`}
            />
          </div>

          {/* US-0052: Plain-English 1-Line Interpretation */}
          <div className="mt-3 border-t border-border/60 pt-2.5">
            <span className="font-mono text-[10px] uppercase text-ink-2">Plain-English Interpretation:</span>
            <p className="text-xs text-ink-1 font-sans mt-0.5 leading-relaxed">
              {pillar.interpretation}
            </p>
          </div>
        </div>

        {/* US-0051: Exact Mathematical Formula */}
        <div className="mb-4 rounded border border-border bg-bg-2/60 p-3.5">
          <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold block mb-1">
            Exact Mathematical Formula:
          </span>
          <code className="font-mono text-xs text-accent block leading-relaxed break-words">
            {pillar.formula}
          </code>
        </div>

        {/* US-0080: Risk Sub-Bars Decomposition */}
        {pillarKey === "risk" && pillar.sub_bars && (
          <div className="mb-5 space-y-3 rounded-card border border-border bg-bg-0 p-4">
            <div className="flex items-center justify-between border-b border-border/70 pb-2">
              <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
                Risk Decomposition (3 Core Sub-Bars)
              </span>
              <span className="font-mono text-[10px] text-ink-2">Inverted: 10 = Maximum Solvency Cushion</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {Object.entries(pillar.sub_bars).map(([k, bar]) => (
                <div key={k} className="rounded border border-border bg-bg-1 p-3">
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="font-mono text-xs font-semibold text-ink-1">{bar.name}</span>
                    <span className="font-mono text-sm font-bold text-accent">{bar.score.toFixed(1)}/10</span>
                  </div>
                  <ScoreBar value={bar.score} label={bar.name} />
                  <p className="mt-2 text-[11px] text-ink-2 leading-tight font-sans">
                    {bar.interpretation}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* US-0051 & US-0056: Raw Metric Inputs & Expandable Line Items */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
              Metric Inputs & Weight Breakdown (Click to Inspect Line Items)
            </span>
            <span className="font-mono text-[10px] text-ink-2">US-0051 · US-0056</span>
          </div>

          <div className="space-y-2">
            {pillar.sub_metrics.map((sm) => {
              const isExpanded = expandedMetric === sm.metric_id;
              return (
                <div
                  key={sm.metric_id}
                  className="rounded border border-border bg-bg-2/40 transition-colors hover:border-accent/40"
                >
                  <button
                    type="button"
                    onClick={() => toggleMetric(sm.metric_id)}
                    className="flex w-full items-center justify-between p-3 text-left"
                    aria-expanded={isExpanded}
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold text-ink-0">
                          {sm.name}
                        </span>
                        <span className="rounded bg-bg-3 px-1.5 py-0.2 font-mono text-[10px] text-ink-2">
                          {(sm.weight * 100).toFixed(0)}% weight
                        </span>
                      </div>
                      <div className="font-mono text-[11px] text-ink-2">
                        Formula: {sm.formula_definition}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-xs font-bold text-accent">
                        {sm.formatted_value}
                      </div>
                      <div className="font-mono text-[10px] text-ink-2">
                        Score: {sm.normalized_score != null ? `${sm.normalized_score.toFixed(1)}/10` : "0.00"}
                      </div>
                    </div>
                  </button>

                  {/* US-0056: Expanded Line Items & SEC Provenance */}
                  {isExpanded && (
                    <div className="border-t border-border/80 bg-bg-0 p-3.5 space-y-2 animate-fade-in">
                      <div className="flex items-center justify-between font-mono text-[10px] uppercase text-ink-2 border-b border-border/60 pb-1">
                        <span>Statement Line Item</span>
                        <span>Amount & Filing Origin</span>
                      </div>
                      <div className="space-y-1.5">
                        {sm.line_items.map((li, idx) => (
                          <div key={idx} className="flex items-center justify-between text-xs">
                            <span className="font-mono text-ink-1">{li.name}</span>
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-semibold text-ink-0">
                                {li.formatted}
                              </span>
                              <span className="rounded bg-bg-2 px-1.5 py-0.5 font-mono text-[10px] text-ink-2">
                                {li.period}
                              </span>
                              {li.sec_edgar_url ? (
                                <a
                                  href={li.sec_edgar_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-accent hover:underline font-mono text-[11px]"
                                  title={li.sec_edgar_url.includes("sedarplus.ca") ? "Open filing in SEDAR+" : "Open filing in SEC EDGAR"}
                                >
                                  {li.sec_edgar_url.includes("sedarplus.ca") ? "SEDAR+ ↗" : "EDGAR ↗"}
                                </a>
                              ) : null}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* US-0083: Honest Missing Data Explainer FAQ */}
        <div className="mt-5 rounded border border-border/80 bg-bg-0 p-3.5">
          <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold block mb-1">
            Data Provenance & Missing Input Policy (US-0083):
          </span>
          <p className="text-xs text-ink-1 font-sans leading-relaxed">
            {pillar.missing_faq}
          </p>
        </div>

        {/* Footer */}
        <div className="mt-5 flex justify-end border-t border-border/80 pt-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded bg-bg-2 px-4 py-1.5 font-mono text-xs font-semibold text-ink-0 hover:bg-bg-3 transition-colors"
          >
            Close Drilldown
          </button>
        </div>
      </div>
    </div>
  );
}

export default PillarDrilldownModal;