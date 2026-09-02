import React from "react";

export interface StatTileProps {
  label: React.ReactNode;
  value: React.ReactNode;
  infoTip?: React.ReactNode;
  delta?: number | string | null;
  deltaLabel?: string;
  subtext?: React.ReactNode;
  tone?: "neutral" | "positive" | "negative" | "warning";
  className?: string;
}

export function StatTile({
  label,
  value,
  infoTip,
  delta,
  deltaLabel,
  subtext,
  tone,
  className = "",
}: StatTileProps) {
  // Determine delta color and arrow if delta is a number
  let deltaNode: React.ReactNode = null;
  if (typeof delta === "number") {
    const isPos = delta > 0;
    const isNeg = delta < 0;
    const arrow = isPos ? "▲" : isNeg ? "▼" : "•";
    const deltaColor = isPos ? "text-pos" : isNeg ? "text-neg" : "text-ink-2";
    deltaNode = (
      <span className={`inline-flex items-center gap-0.5 font-mono text-[11px] font-medium ${deltaColor}`}>
        <span aria-hidden="true">{arrow}</span>
        <span>{Math.abs(delta).toFixed(1)}%</span>
        {deltaLabel && <span className="text-ink-2 ml-0.5">{deltaLabel}</span>}
      </span>
    );
  } else if (delta) {
    deltaNode = (
      <span className="font-mono text-[11px] text-ink-1">
        {delta}
      </span>
    );
  }

  const valueToneClass =
    tone === "positive"
      ? "text-pos"
      : tone === "negative"
        ? "text-neg"
        : tone === "warning"
          ? "text-warn"
          : "text-ink-0";

  return (
    <div
      className={`rounded-card border border-border bg-bg-2/60 p-3 sm:p-3.5 transition-colors hover:border-border-strong ${className}`}
    >
      <div className="flex items-center justify-between gap-1 text-[10px] font-mono uppercase tracking-widest text-ink-2 mb-1">
        <span className="truncate">{label}</span>
        {infoTip && <span className="shrink-0">{infoTip}</span>}
      </div>

      <div className="flex items-baseline justify-between gap-2 mt-1">
        <div className={`font-mono tabular-nums text-lg sm:text-xl font-semibold ${valueToneClass}`}>
          {value ?? "—"}
        </div>
        {deltaNode}
      </div>

      {subtext && (
        <div className="mt-1 text-[11px] text-ink-2 truncate">
          {subtext}
        </div>
      )}
    </div>
  );
}

export default StatTile;
