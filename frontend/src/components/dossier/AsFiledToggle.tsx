import React from "react";

interface AsFiledToggleProps {
  value: "filed" | "restated";
  onChange: (v: "filed" | "restated") => void;
  hasRestatement: boolean;
  className?: string;
}

export const AsFiledToggle: React.FC<AsFiledToggleProps> = ({ value, onChange, hasRestatement, className = "" }) => {
  return (
    <div className={`inline-flex items-center gap-2 ${className}`} role="group" aria-label="As-filed vs as-restated toggle">
      <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2">History view:</span>
      <div className="inline-flex rounded-card p-0.5 bg-bg-0 border border-border" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={value === "filed"}
          onClick={() => onChange("filed")}
          onKeyDown={(e) => {
            if (e.key === "Escape") (e.target as HTMLElement).blur();
          }}
          className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all ${
            value === "filed" ? "bg-accent text-bg-0 shadow-xs" : "text-ink-1 hover:text-ink-0"
          }`}
        >
          As-Filed
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={value === "restated"}
          onClick={() => onChange("restated")}
          className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all ${
            value === "restated" ? "bg-accent text-bg-0 shadow-xs" : "text-ink-1 hover:text-ink-0"
          }`}
        >
          As-Restated
        </button>
      </div>
      {!hasRestatement && (
        <span className="font-mono text-[11px] text-ink-2">No restatements detected - values identical.</span>
      )}
      {hasRestatement && (
        <span className="font-mono text-[11px] text-warn">Restatement delta shown where provider rewrote history.</span>
      )}
    </div>
  );
};

export default AsFiledToggle;