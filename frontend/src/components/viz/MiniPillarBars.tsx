import { barWidth } from "../../lib/bars";

export interface MiniPillarBarsProps {
  quality: number | null | undefined;
  value: number | null | undefined;
  growth: number | null | undefined;
  risk: number | null | undefined;
  className?: string;
}

export function MiniPillarBars({
  quality,
  value,
  growth,
  risk,
  className = "",
}: MiniPillarBarsProps) {
  const pillars: [string, number | null | undefined][] = [
    ["Q", quality],
    ["V", value],
    ["G", growth],
    ["R", risk],
  ];

  const ariaLabel = `Pillars: Q ${quality != null ? quality.toFixed(1) : "—"}, V ${value != null ? value.toFixed(1) : "—"}, G ${growth != null ? growth.toFixed(1) : "—"}, R ${risk != null ? risk.toFixed(1) : "—"}`;

  return (
    <div
      className={`inline-flex items-center gap-1.5 ${className}`}
      role="img"
      aria-label={ariaLabel}
    >
      {pillars.map(([label, val]) => {
        const hasVal = val !== null && val !== undefined;
        const w = hasVal ? barWidth(val, 10) : 0;
        return (
          <div key={label} className="flex flex-col items-center gap-0.5" title={`${label}: ${hasVal ? val.toFixed(1) : "unscored"}`}>
            <svg viewBox="0 0 100 8" preserveAspectRatio="none" className="h-1.5 w-6 rounded-sm overflow-hidden">
              <rect x="0" y="0" width="100" height="8" fill="var(--bg-2)" />
              {hasVal ? (
                <rect x="0" y="0" width={w} height="8" fill="var(--accent)" />
              ) : (
                <rect x="0" y="0" width="100" height="8" fill="none" stroke="var(--border-strong)" strokeDasharray="4 2" strokeWidth="2" />
              )}
            </svg>
            <span className="font-mono text-[8px] text-ink-2 uppercase">{label}</span>
          </div>
        );
      })}
    </div>
  );
}

export default MiniPillarBars;
