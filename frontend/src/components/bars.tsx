import { barWidth } from "../lib/bars";

export function ScoreBar({
  value,
  max = 10,
  label,
  median,
}: {
  value: number | null;
  max?: number;
  label?: string;
  median?: number | null;
}) {
  const w = barWidth(value, max);
  const fill = value == null ? "var(--border)" : "var(--accent)";
  const medianX = median != null ? Math.max(0, Math.min(100, (median / max) * 100)) : null;

  const ariaLabel = label
    ? `${label}: ${value == null ? "not scored" : value.toFixed(1)}${
        median != null ? `, Sector Peer Median: ${median.toFixed(1)}` : ""
      }`
    : undefined;

  return (
    <div className="relative w-full">
      <svg
        viewBox="0 0 100 10"
        preserveAspectRatio="none"
        className="h-2.5 w-full overflow-visible rounded-chip"
        role="img"
        aria-label={ariaLabel}
      >
        <rect x="0" y="0" width="100" height="10" rx="2" fill="var(--bg-0)" />
        <rect
          x="0"
          y="0"
          width={w}
          height="10"
          rx="2"
          fill={fill}
          className="transition-all duration-300 motion-reduce:transition-none"
        />
        {/* US-0067: Overlay distinct marker for sector peer median */}
        {medianX != null && (
          <g className="median-marker">
            <line
              x1={medianX}
              y1="-1"
              x2={medianX}
              y2="11"
              stroke="var(--ink-0)"
              strokeWidth="1.5"
            />
            <title>{`Sector Peer Median: ${median?.toFixed(1)}`}</title>
          </g>
        )}
      </svg>
      {median != null && (
        <div className="flex justify-between items-center mt-1 text-[9px] font-mono text-ink-2">
          <span>0</span>
          <span className="text-ink-1">Peer Median: {median.toFixed(1)}</span>
          <span>{max}</span>
        </div>
      )}
    </div>
  );
}

export function PillarMiniBars({ p }: { p: { quality: number | null; value: number | null; growth: number | null; risk: number | null } }) {
  const items: [string, number | null][] = [
    ["Q", p.quality],
    ["V", p.value],
    ["G", p.growth],
    ["R", p.risk],
  ];
  return (
    <div className="flex items-end gap-1" aria-hidden="true">
      {items.map(([k, v]) => (
        <svg key={k} viewBox="0 0 100 10" preserveAspectRatio="none" className="h-2 w-7 overflow-hidden rounded-chip">
          <rect x="0" y="0" width="100" height="10" rx="2" fill="var(--bg-0)" />
          <rect x="0" y="0" width={barWidth(v, 10)} height="10" rx="2" fill={v == null ? "var(--border)" : "var(--accent)"} />
        </svg>
      ))}
    </div>
  );
}
