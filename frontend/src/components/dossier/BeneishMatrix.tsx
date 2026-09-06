import type { BeneishAnalysis } from "../../api/types";
import Tooltip from "../ui/Tooltip";

export interface BeneishMatrixProps {
  analysis?: BeneishAnalysis | null;
  className?: string;
}

type BeneishKey = "dsri" | "gmi" | "aqi" | "sgi" | "depi" | "sgai" | "lvgi" | "tata";

export function BeneishMatrix({ analysis, className = "" }: BeneishMatrixProps) {
  if (!analysis) {
    return (
      <div className={`rounded-card border border-border bg-bg-1 p-4 text-xs text-ink-2 font-mono ${className}`}>
        Beneish M-Score analysis pending or insufficient financial filing history.
      </div>
    );
  }

  if (analysis.status === "financial_institution_excluded") {
    return (
      <div className={`rounded-card border border-border bg-bg-1 p-4 shadow-card ${className}`}>
        <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-2">
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
            Beneish 8-Variable Forensic Matrix
          </span>
          <span className="rounded-chip border border-border px-2 py-0.5 text-[10px] font-mono text-ink-2 bg-bg-2">
            Excluded (Financial Institution)
          </span>
        </div>
        <p className="text-xs text-ink-1 leading-relaxed">
          {analysis.message || "Financial institutions are excluded from Beneish M-Score analysis because loan book provisions differ fundamentally from corporate accruals."}
        </p>
      </div>
    );
  }

  const isManipulator = analysis.is_manipulator;
  const mScore = analysis.m_score;
  const vars = analysis.variables ?? {};

  const items: Array<{
    key: BeneishKey;
    name: string;
    label: string;
    desc: string;
    threshold: string;
    isFlag: (v: number) => boolean;
  }> = [
    {
      key: "dsri",
      name: "DSRI",
      label: "Days Sales in Receivables",
      desc: "Detects accelerated revenue recognition or lenient credit terms.",
      threshold: "> 1.30",
      isFlag: (v) => v > 1.30,
    },
    {
      key: "gmi",
      name: "GMI",
      label: "Gross Margin Index",
      desc: "Prior year margin / current year margin. > 1 indicates deteriorating margins.",
      threshold: "> 1.25",
      isFlag: (v) => v > 1.25,
    },
    {
      key: "aqi",
      name: "AQI",
      label: "Asset Quality Index",
      desc: "Detects capitalization of ordinary operating expenses into non-current assets.",
      threshold: "> 1.25",
      isFlag: (v) => v > 1.25,
    },
    {
      key: "sgi",
      name: "SGI",
      label: "Sales Growth Index",
      desc: "High growth companies have higher incentives to manipulate when deceleration begins.",
      threshold: "> 1.30",
      isFlag: (v) => v > 1.30,
    },
    {
      key: "depi",
      name: "DEPI",
      label: "Depreciation Rate Index",
      desc: "Prior depreciation rate / current rate. > 1 indicates extended asset useful lives.",
      threshold: "> 1.20",
      isFlag: (v) => v > 1.20,
    },
    {
      key: "sgai",
      name: "SGAI",
      label: "SG&A Efficiency Index",
      desc: "Current SG&A % / prior SG&A %. Disproportionate increases signal overhead creep.",
      threshold: "> 1.20",
      isFlag: (v) => v > 1.20,
    },
    {
      key: "lvgi",
      name: "LVGI",
      label: "Leverage Index",
      desc: "Total debt to total assets ratio change. Rising leverage increases covenant pressure.",
      threshold: "> 1.20",
      isFlag: (v) => v > 1.20,
    },
    {
      key: "tata",
      name: "TATA",
      label: "Total Accruals to Assets",
      desc: "Compares net operating profit vs cash generated. High accruals warn of paper profit.",
      threshold: "> 0.08",
      isFlag: (v) => v > 0.08,
    },
  ];

  return (
    <div className={`rounded-card border border-border bg-bg-1 p-4 shadow-card transition-colors ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-3 mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
              Beneish 8-Variable Forensic Matrix
            </span>
            <Tooltip term="beneish" />
            <span className="rounded bg-bg-2 border border-border px-1.5 py-0.5 font-mono text-[9px] text-ink-2" title="Sample Window">
              Beneish (1999): 1982–1992 Compustat sample
            </span>
          </div>
          <p className="text-xs text-ink-2 mt-0.5 font-mono">
            Threshold: M &gt; -1.78 = Red Flag (Empirical manipulation probability)
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase text-ink-2 block">Beneish M-Score</span>
            <span
              className={`font-mono text-base font-bold ${
                isManipulator ? "text-neg" : "text-pos"
              }`}
            >
              {mScore != null ? mScore.toFixed(2) : "0.00"}
            </span>
          </div>
          <span
            className={`rounded-chip border px-2.5 py-1 font-mono text-xs font-bold ${
              isManipulator
                ? "bg-neg-weak border-neg/40 text-neg"
                : "bg-pos-weak border-pos/40 text-pos"
            }`}
          >
            {isManipulator ? "FLAGGED: HIGH RISK" : "CLEAN PROFILE"}
          </span>
        </div>
      </div>

      {/* False-Positive Rate Disclosure (US-0947) */}
      {isManipulator && (
        <div className="mb-3 rounded border border-warn/40 bg-warn-weak/30 p-2 text-xs text-ink-1 font-sans">
          <strong className="text-warn font-mono text-[11px]">False-Positive Rate (~14%):</strong> Beneish M-Score false-positive rate is ~14% among fast-growing firms; capital expenditure growth, seasonal receivable swings, or rapid top-line expansion can simulate earnings manipulation.
        </div>
      )}

      <p className="text-xs text-ink-1 leading-relaxed mb-3">
        {analysis.interpretation}
      </p>

      {/* 8-Variable Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-3">
        {items.map((it) => {
          const rawVal = (vars as Record<string, number | null | undefined>)[it.key];
          const val = typeof rawVal === "number" ? rawVal : null;
          const flagged = val != null && it.isFlag(val);

          return (
            <div
              key={it.key}
              className={`rounded border p-2.5 flex flex-col justify-between transition-colors ${
                flagged
                  ? "border-neg/40 bg-neg-weak/40"
                  : "border-border bg-bg-0"
              }`}
            >
              <div className="flex items-center justify-between gap-1">
                <span className="font-mono text-xs font-bold text-ink-0">{it.name}</span>
                <span
                  className={`rounded-chip px-1.5 py-0.2 font-mono text-[9px] font-bold border ${
                    flagged
                      ? "bg-neg text-bg-0 border-neg"
                      : "bg-pos-weak text-pos border-pos/30"
                  }`}
                >
                  {val != null ? (flagged ? "FLAG" : "PASS") : "Not reported in filing"}
                </span>
              </div>

              <div className="my-1.5 flex items-baseline justify-between">
                <span className="text-[10px] font-mono text-ink-2">Value:</span>
                <span
                  className={`font-mono text-xs font-semibold ${
                    flagged ? "text-neg font-bold" : "text-ink-0"
                  }`}
                >
                  {val != null ? val.toFixed(2) : "0.00"}
                </span>
              </div>

              <div className="border-t border-border/50 pt-1 text-[9px] font-mono text-ink-2 truncate" title={it.desc}>
                {it.label}
              </div>
            </div>
          );
        })}
      </div>

      {/* Historical Behavior & Decay Disclosure (US-0063) */}
      <div className="border-t border-border/50 pt-2 text-[10px] font-mono text-ink-2">
        <span>Model Decay: Beneish published 1999. While robust for accrual red flags, aggressive post-2000 revenue models require verifying cash collections directly on SEC EDGAR.</span>
      </div>
    </div>
  );
}

export default BeneishMatrix;