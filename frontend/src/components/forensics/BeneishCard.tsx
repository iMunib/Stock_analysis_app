import React from "react";
import type { BeneishAnalysis } from "../../api/types";

interface BeneishCardProps {
  analysis?: BeneishAnalysis | null;
}

export const BeneishCard: React.FC<BeneishCardProps> = ({ analysis }) => {
  if (!analysis) {
    return (
      <div className="rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface)] p-6 text-sm text-[var(--color-text-muted)]">
        Beneish M-Score analysis is not available for this company.
      </div>
    );
  }

  if (analysis.status === "financial_institution_excluded") {
    return (
      <div className="rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface)] p-6">
        <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] pb-4">
          <div>
            <h3 className="text-base font-semibold text-[var(--color-text-primary)]">
              Beneish M-Score (8-Variable Manipulation Engine)
            </h3>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
              Forensic accounting model detecting financial statement manipulation.
            </p>
          </div>
          <span className="rounded-full px-3 py-1 text-xs font-semibold bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border border-[var(--color-border-subtle)]">
            Excluded (Financial Institution)
          </span>
        </div>
        <p className="mt-4 text-sm text-[var(--color-text-muted)]">
          {analysis.message || "Financial institutions are excluded from Beneish M-Score analysis because loan book and reserve accounting differ fundamentally from corporate accrual structures."}
        </p>
      </div>
    );
  }

  const isManipulator = analysis.is_manipulator;
  const mScore = analysis.m_score;
  const vars = analysis.variables;

  const variableDefs: Array<{ key: keyof NonNullable<typeof vars>; label: string; desc: string; neutral: number }> = [
    { key: "dsri", label: "DSRI", desc: "Days Sales in Receivables Index", neutral: 1.0 },
    { key: "gmi", label: "GMI", desc: "Gross Margin Index (Prev / Curr)", neutral: 1.0 },
    { key: "aqi", label: "AQI", desc: "Asset Quality Index (Capitalized Costs)", neutral: 1.0 },
    { key: "sgi", label: "SGI", desc: "Sales Growth Index", neutral: 1.0 },
    { key: "depi", label: "DEPI", desc: "Depreciation Index", neutral: 1.0 },
    { key: "sgai", label: "SGAI", desc: "SG&A Expense Growth Index", neutral: 1.0 },
    { key: "lvgi", label: "LVGI", desc: "Leverage Index (Total Debt / Assets)", neutral: 1.0 },
    { key: "tata", label: "TATA", desc: "Total Accruals to Total Assets", neutral: 0.0 },
  ];

  return (
    <div className="rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface)] p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-border-subtle)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-[var(--color-text-primary)]">
              Beneish M-Score Forensic Screen
            </h3>
            <span className="text-xs px-2 py-0.5 rounded bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] font-mono">
              Threshold: -1.78
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
            8-variable empirical model predicting probabilistic financial statement manipulation (Beneish 1999).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">M-Score</div>
            <div
              className={`text-2xl font-bold font-mono ${
                isManipulator ? "text-[var(--color-signal-bearish)]" : "text-[var(--color-signal-bullish)]"
              }`}
            >
              {mScore !== null ? mScore.toFixed(2) : "N/A"}
            </div>
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold border ${
              isManipulator
                ? "bg-[var(--color-signal-bearish-bg)] text-[var(--color-signal-bearish)] border-[var(--color-signal-bearish-border)]"
                : "bg-[var(--color-signal-bullish-bg)] text-[var(--color-signal-bullish)] border-[var(--color-signal-bullish-border)]"
            }`}
          >
            {isManipulator ? "High Manipulation Risk" : "Clean Profile (Non-manipulator)"}
          </span>
        </div>
      </div>

      <p className="mt-3 text-xs text-[var(--color-text-muted)] leading-relaxed">
        {analysis.interpretation}
      </p>

      {/* 8-Variable Breakdown Grid */}
      {vars && (
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {variableDefs.map((item) => {
            const val = vars[item.key];
            const isAbnormal =
              item.key === "tata"
                ? val !== null && val !== undefined && val > 0.10
                : val !== null && val !== undefined && val > 1.30;

            return (
              <div
                key={item.key}
                className="rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface-hover)] p-3 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-[var(--color-text-primary)]">
                    {item.label}
                  </span>
                  <span
                    className={`font-mono text-xs font-bold ${
                      isAbnormal ? "text-[var(--color-signal-bearish)]" : "text-[var(--color-text-primary)]"
                    }`}
                  >
                    {val !== null && val !== undefined ? val.toFixed(2) : "0.00"}
                  </span>
                </div>
                <div className="mt-1 text-[10px] text-[var(--color-text-muted)] line-clamp-1" title={item.desc}>
                  {item.desc}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};