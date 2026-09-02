import { barWidth } from "../lib/bars";

export function ScoreBar({ value, max = 10, label }: { value: number | null; max?: number; label?: string }) {
  const w = barWidth(value, max);
  const fill = value == null ? "#33404d" : "#e0a84f";
  return (
    <svg
      viewBox="0 0 100 10"
      preserveAspectRatio="none"
      className="h-2.5 w-full"
      role="img"
      aria-label={label ? `${label}: ${value == null ? "not scored" : value.toFixed(1)}` : undefined}
    >
      <rect x="0" y="0" width="100" height="10" rx="2" fill="#141a21" />
      <rect x="0" y="0" width={w} height="10" rx="2" fill={fill} />
    </svg>
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
        <svg key={k} viewBox="0 0 100 10" preserveAspectRatio="none" className="h-2 w-7">
          <rect x="0" y="0" width="100" height="10" rx="2" fill="#141a21" />
          <rect x="0" y="0" width={barWidth(v, 10)} height="10" rx="2" fill="#e0a84f" />
        </svg>
      ))}
    </div>
  );
}
