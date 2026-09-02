
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
    <div className={`inline-flex flex-col items-center ${className}`}>
      <svg
        viewBox="0 0 100 56"
        width={cfg.width}
        height={cfg.height}
        role="img"
        aria-label={ariaLabel}
        className="overflow-visible"
      >
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--neg)" />
            <stop offset="45%" stopColor="var(--warn)" />
            <stop offset="85%" stopColor="var(--pos)" />
          </linearGradient>
        </defs>

        {/* Background Track */}
        <path
          d="M 12,46 A 38,38 0 0,1 88,46"
          fill="none"
          stroke="var(--bg-2)"
          strokeWidth="6"
          strokeLinecap="round"
        />

        {/* Foreground Progress Arc */}
        {hasValue && (
          <path
            d="M 12,46 A 38,38 0 0,1 88,46"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={arcLength}
            strokeDashoffset={progressOffset}
            className="transition-all duration-500 ease-out"
          />
        )}

        {/* Needle Indicator */}
        {hasValue && (
          <line
            x1={cx}
            y1={cy}
            x2={needleX}
            y2={needleY}
            stroke="var(--ink-0)"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        )}

        {/* Center Pivot Dot */}
        <circle cx={cx} cy={cy} r="3" fill="var(--ink-0)" />

        {/* Min / Max Tick Labels */}
        <text x="12" y="54" textAnchor="middle" className="font-mono text-[7px] fill-ink-2">0</text>
        <text x="88" y="54" textAnchor="middle" className="font-mono text-[7px] fill-ink-2">10</text>
      </svg>

      {/* Center Value and Signal Label */}
      <div className="text-center -mt-1">
        <span
          className={`font-mono tabular-nums font-bold text-ink-0 ${cfg.text}`}
          style={{ color: hasValue ? color : "var(--ink-2)" }}
        >
          {hasValue ? value.toFixed(1) : "—"}
        </span>
        {showLabel && signal && (
          <div className={`font-mono uppercase tracking-wider text-ink-1 ${cfg.labelText} truncate max-w-[120px]`}>
            {signal.replace(/_/g, " ")}
          </div>
        )}
      </div>
    </div>
  );
}

export default CompositeGauge;
