import { useEffect, useState } from "react";
import type { RatioInspectOut } from "../../api/types";
import { api } from "../../api/client";

export interface RatioInspectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  companyId: string;
  ratioName: string;
  initialData?: RatioInspectOut | null;
}

export function RatioInspectorModal({
  isOpen,
  onClose,
  companyId,
  ratioName,
  initialData,
}: RatioInspectorModalProps) {
  const [data, setData] = useState<RatioInspectOut | null>(initialData ?? null);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    if (initialData && initialData.ratio_id === ratioName) {
      setData(initialData);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    api.inspectRatio(companyId, ratioName)
      .then((res) => {
        setData(res);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load ratio calculation");
      })
      .finally(() => setLoading(false));
  }, [isOpen, companyId, ratioName, initialData]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="ratio-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-card border border-border bg-bg-1 p-5 shadow-modal transition-all">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-border/80 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-accent">
                RATIO CALCULATION INSPECTOR
              </span>
              <span className="rounded bg-bg-2 px-1.5 py-0.2 font-mono text-[10px] text-ink-2">
                US-0460 · US-0453
              </span>
            </div>
            <h2 id="ratio-modal-title" className="font-heading text-lg font-bold text-ink-0 mt-1">
              {data ? data.label : `Inspect Calculation: ${ratioName}`}
            </h2>
            <p className="font-mono text-xs text-ink-2 mt-0.5">
              {data?.vintage || `${companyId} · Audited Statement Line Items`}
            </p>
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

        {loading ? (
          <div className="py-12 text-center font-mono text-xs text-ink-2">
            Resolving audited line items from database…
          </div>
        ) : error ? (
          <div className="my-4 rounded border border-neg/40 bg-neg-weak/30 p-3 font-mono text-xs text-neg">
            {error}
          </div>
        ) : data ? (
          <div className="my-4 space-y-4">
            {/* Formula Definition (US-0460.1) */}
            <div className="rounded border border-border bg-bg-0 p-3">
              <span className="font-mono text-[10px] uppercase text-ink-2 block mb-1">
                1. Exact Formula Definition
              </span>
              <code className="font-mono text-xs text-accent font-semibold block">
                {data.formula_string}
              </code>
            </div>

            {/* Numerator and Denominator Side-by-Side (US-0460.2, US-0460.3) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Numerator */}
              <div className="rounded border border-border bg-bg-2/50 p-3 space-y-1.5">
                <span className="font-mono text-[10px] uppercase text-ink-2 block font-semibold">
                  2. Numerator Component
                </span>
                <div className="text-sm font-bold text-ink-0 font-mono">
                  {data.numerator.formatted}
                </div>
                <div className="text-xs text-ink-1 font-heading">
                  {data.numerator.label}
                </div>
                <div className="text-[11px] font-mono text-ink-2">
                  Currency: {data.numerator.currency} · As-of: {data.numerator.as_of_date}
                </div>
                <div className="text-[11px] text-ink-2 font-sans">
                  {data.numerator.statement_location}
                </div>
                {data.numerator.sec_edgar_url && (
                  <div className="pt-1">
                    <a
                      href={data.numerator.sec_edgar_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent hover:underline font-mono text-[11px]"
                      title={data.numerator.sec_edgar_url.includes("sedarplus.ca") ? "Open filing in SEDAR+" : "Open filing in SEC EDGAR"}
                    >
                      {data.numerator.sec_edgar_url.includes("sedarplus.ca") ? "View filing on SEDAR+ ↗" : "View filing on SEC EDGAR ↗"}
                    </a>
                  </div>
                )}
              </div>

              {/* Denominator */}
              <div className="rounded border border-border bg-bg-2/50 p-3 space-y-1.5">
                <span className="font-mono text-[10px] uppercase text-ink-2 block font-semibold">
                  3. Denominator Component
                </span>
                <div className="text-sm font-bold text-ink-0 font-mono">
                  {data.denominator.formatted}
                </div>
                <div className="text-xs text-ink-1 font-heading">
                  {data.denominator.label}
                </div>
                <div className="text-[11px] font-mono text-ink-2">
                  Currency: {data.denominator.currency} · As-of: {data.denominator.as_of_date}
                </div>
                <div className="text-[11px] text-ink-2 font-sans">
                  {data.denominator.statement_location}
                </div>
                {data.denominator.sec_edgar_url && (
                  <div className="pt-1">
                    <a
                      href={data.denominator.sec_edgar_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent hover:underline font-mono text-[11px]"
                      title={data.denominator.sec_edgar_url.includes("sedarplus.ca") ? "Open filing in SEDAR+" : "Open filing in SEC EDGAR"}
                    >
                      {data.denominator.sec_edgar_url.includes("sedarplus.ca") ? "View filing on SEDAR+ ↗" : "View filing on SEC EDGAR ↗"}
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Step-by-Step Arithmetic Resolution (US-0460.4) */}
            <div className="rounded border border-accent/40 bg-accent-weak/20 p-3">
              <span className="font-mono text-[10px] uppercase text-accent font-semibold block mb-1.5">
                4. Step-by-Step Arithmetic Resolution
              </span>
              <div className="space-y-1">
                {data.arithmetic_resolution.map((step, idx) => (
                  <div key={idx} className="font-mono text-xs text-ink-0">
                    {step}
                  </div>
                ))}
              </div>
              <div className="mt-2 border-t border-accent/30 pt-2 flex items-center justify-between">
                <span className="font-mono text-xs text-ink-1">Final Computed Value:</span>
                <span className="font-mono text-lg font-bold text-accent">
                  {data.result_formatted}
                </span>
              </div>
            </div>
          </div>
        ) : null}

        {/* Footer */}
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded bg-bg-2 px-3 py-1.5 font-mono text-xs text-ink-0 hover:bg-bg-3"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}

export default RatioInspectorModal;
