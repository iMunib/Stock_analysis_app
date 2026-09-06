
import { useId } from "react";

export interface CompositeGaugeProps {
  value: number | null | undefined;
  signal?: string | null;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

export function CompositeGauge({
  value,
  signal,
  size = "md",
  showLabel = true,
  className = "",
}: CompositeGaugeProps) {
  const rawId = useId().replace(/:/g, "_");
  const gradientId = `gaugeGrad_${rawId}`;
  const glowId = `gaugeGlow_${rawId}`;
  // Clamp value between 0 and 10
  const hasValue = value !== null && value !== undefined && !isNaN(value);
  const clamped = hasValue ? Math.max(0, Math.min(10, value)) : 0;

  // Semicircle arc calculations: radius 40, center (50, 46), viewbox 0 0 100 58
  const r = 38;
  const cx = 50;
  const cy = 46;
  const arcLength = Math.PI * r; // ~119.38
  const progressOffset = arcLength - (clamped / 10) * arcLength;

  // Needle angle: 0 -> -180 deg, 10 -> 0 deg (or 180 deg sweep)
  const angleDeg = -180 + (clamped / 10) * 180;
  const angleRad = (angleDeg * Math.PI) / 180;
  const needleLength = r - 6;
  const needleX = cx + needleLength * Math.cos(angleRad);
  const needleY = cy + needleLength * Math.sin(angleRad);

  // Determine active signal color
  const color = !hasValue
    ? "var(--ink-2)"
    : clamped >= 7.0
      ? "var(--pos)"
      : clamped >= 4.0
        ? "var(--warn)"
        : "var(--neg)";

  // Sizing scale
  const sizeMap = {
    sm: { width: 70, height: 42, text: "text-sm", labelText: "text-[9px]" },
    md: { width: 110, height: 64, text: "text-lg", labelText: "text-[10px]" },
    lg: { width: 150, height: 86, text: "text-2xl", labelText: "text-xs" },
  };
  const cfg = sizeMap[size] || sizeMap.md;

  const ariaLabel = `Composite score gauge: ${hasValue ? `${value.toFixed(1)} out of 10` : "unscored"}${signal ? `, signal: ${signal}` : ""}`;

  return (
    <div className={`inline-flex flex-col items-center select-none ${className}`}>
      <svg
        viewBox="0 0 100 56"
        width={cfg.width}
        height={cfg.height}
        role="img"
        aria-label={ariaLabel}
        className="overflow-visible"
      >
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--neg)" />
            <stop offset="40%" stopColor="var(--warn)" />
            <stop offset="75%" stopColor="var(--pos)" />
            <stop offset="100%" stopColor="var(--accent)" />
          </linearGradient>
          <filter id={glowId} x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="1" stdDeviation="1.5" floodColor="rgba(0,0,0,0.5)" />
          </filter>
        </defs>

        {/* Outer subtle decorative hairline arc */}
        <path
          d="M 9,46 A 41,41 0 0,1 91,46"
          fill="none"
          stroke="var(--border)"
          strokeWidth="1"
          strokeDasharray="1.5 2.5"
          opacity="0.6"
        />

        {/* Background Track with bevel effect */}
        <path
          d="M 12,46 A 38,38 0 0,1 88,46"
          fill="none"
          stroke="var(--bg-2)"
          strokeWidth="6"
          strokeLinecap="round"
        />

        {/* Ticks at 0, 2.5, 5, 7.5, 10 */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((t) => {
          const a = -180 + t * 180;
          const rad = (a * Math.PI) / 180;
          const x1 = cx + (r - 5) * Math.cos(rad);
          const y1 = cy + (r - 5) * Math.sin(rad);
          const x2 = cx + (r + 4) * Math.cos(rad);
          const y2 = cy + (r + 4) * Math.sin(rad);
          return (
            <line
              key={t}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="var(--border-strong)"
              strokeWidth="1"
              opacity="0.8"
            />
          );
        })}

        {/* Foreground Progress Arc */}
        {hasValue && (
          <path
            d="M 12,46 A 38,38 0 0,1 88,46"
            fill="none"
            stroke={`url(#${gradientId})`}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={arcLength}
            strokeDashoffset={progressOffset}
            filter={`url(#${glowId})`}
            className="transition-all duration-700 ease-out"
          />
        )}

        {/* Needle Indicator with metallic shadow */}
        {hasValue && (
          <g filter={`url(#${glowId})`}>
            <line
              x1={cx}
              y1={cy}
              x2={needleX}
              y2={needleY}
              stroke="var(--ink-0)"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </g>
        )}

        {/* Metallic Center Pivot Bezel */}
        <circle cx={cx} cy={cy} r="4.5" fill="var(--bg-3)" stroke="var(--border-strong)" strokeWidth="1" />
        <circle cx={cx} cy={cy} r="2.2" fill={hasValue ? color : "var(--ink-2)"} />

        {/* Min / Max Tick Labels */}
        <text x="11" y="54" textAnchor="middle" className="font-mono text-[7px] fill-ink-2 font-medium">0</text>
        <text x="89" y="54" textAnchor="middle" className="font-mono text-[7px] fill-ink-2 font-medium">10</text>
      </svg>

      {/* Center Value and Signal Label */}
      <div className="text-center -mt-1">
        <span
          className={`font-mono tabular-nums font-bold tracking-tight text-ink-0 drop-shadow-xs ${cfg.text}`}
          style={{ color: hasValue ? color : "var(--ink-2)" }}
        >
          {hasValue ? value.toFixed(1) : "0.00"}
        </span>
        {showLabel && signal && (
          <div className={`font-mono uppercase tracking-wider text-ink-1 ${cfg.labelText} truncate max-w-[130px] mt-0.5`}>
            {signal.replace(/_/g, " ")}
          </div>
        )}
      </div>
    </div>
  );
}

export default CompositeGauge;