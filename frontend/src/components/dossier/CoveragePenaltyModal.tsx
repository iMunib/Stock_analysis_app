import { useEffect } from "react";
import type { CoveragePenaltyDetails } from "../../api/types";

export interface CoveragePenaltyModalProps {
  isOpen: boolean;
  onClose: () => void;
  details?: CoveragePenaltyDetails | null;
}

export function CoveragePenaltyModal({
  isOpen,
  onClose,
  details,
}: CoveragePenaltyModalProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !details) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="penalty-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-card border border-border bg-bg-1 p-5 shadow-modal transition-all">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-border/80 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-accent">
                COVERAGE PENALTY VISUALIZER
              </span>
              <span className="rounded bg-bg-2 px-1.5 py-0.2 font-mono text-[10px] text-ink-2">
                US-0100
              </span>
            </div>
            <h2 id="penalty-modal-title" className="font-heading text-base font-bold text-ink-0 mt-1">
              Deterministic Coverage Penalty Breakdown
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-ink-2 hover:bg-bg-2 hover:text-ink-0"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* 3 Step Breakdown (US-0100) */}
        <div className="my-4 space-y-3">
          {/* Step 1: Unadjusted Weighted Score */}
          <div className="rounded border border-border bg-bg-0 p-3 flex items-center justify-between">
            <div>
              <span className="font-mono text-[10px] uppercase text-ink-2 block">
                1. Unadjusted Weighted Score
              </span>
              <span className="text-xs text-ink-1 font-sans">
                Base composite calculated across {details.coverage_count} available pillars
              </span>
            </div>
            <span className="font-mono text-lg font-bold text-ink-0">
              {details.unadjusted_weighted_score != null ? details.unadjusted_weighted_score.toFixed(2) : "0.00"}
            </span>
          </div>

          {/* Step 2: Coverage Deduction Formula */}
          <div className="rounded border border-border bg-bg-0 p-3">
            <span className="font-mono text-[10px] uppercase text-ink-2 block mb-1">
              2. Coverage Penalty Deduction Formula
            </span>
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-xs text-accent">
                Multiplier: {(details.multiplier * 100).toFixed(0)}% (×{details.multiplier.toFixed(2)})
              </span>
              <span className="font-mono text-sm font-semibold text-warn">
                -{details.deduction.toFixed(2)} pts
              </span>
            </div>
            <code className="mt-2 block rounded bg-bg-2 p-2 font-mono text-[11px] text-ink-1">
              {details.formula_string}
            </code>
          </div>

          {/* Step 3: Final Published Score */}
          <div className="rounded border border-accent/40 bg-accent-weak/20 p-3 flex items-center justify-between">
            <div>
              <span className="font-mono text-[10px] uppercase text-accent font-semibold block">
                3. Final Published Composite
              </span>
              <span className="text-xs text-ink-1 font-sans">
                Official composite published on Dossier and Screener
              </span>
            </div>
            <span className="font-mono text-2xl font-bold text-accent">
              {details.published_score != null ? details.published_score.toFixed(2) : "NULL"}
            </span>
          </div>
        </div>

        {/* Multiplier Tier Schedule */}
        <div className="rounded border border-border/70 bg-bg-2/50 p-3">
          <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold block mb-2">
            Locked Penalty Schedule (SCORING_SPEC §4):
          </span>
          <div className="space-y-1">
            {details.penalty_table.map((tier) => (
              <div
                key={tier.pillars}
                className={`flex items-center justify-between text-xs py-1 px-1.5 rounded ${
                  tier.pillars === details.coverage_count ? "bg-accent/15 text-accent font-bold" : "text-ink-2"
                }`}
              >
                <span>{tier.label}</span>
                <span className="font-mono">×{tier.multiplier.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded bg-bg-2 px-3 py-1.5 font-mono text-xs text-ink-0 hover:bg-bg-3"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default CoveragePenaltyModal;