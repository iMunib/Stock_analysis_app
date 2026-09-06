import React from "react";

interface RevenueSparklineProps {
  values?: number[];
  width?: number;
  height?: number;
  className?: string;
}

export const RevenueSparkline: React.FC<RevenueSparklineProps> = ({
  values = [],
  width = 64,
  height = 18,
  className = "",
}) => {
  if (!values || values.length < 2) {
    return <span className="font-mono text-[10px] text-ink-2">Not reported in filing</span>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pad = 2;
  const innerH = height - pad * 2;
  const innerW = width - pad * 2;

  const points = values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * innerW;
    const y = pad + innerH - ((v - min) / range) * innerH;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const isUp = values[values.length - 1] >= values[0];
  const strokeColor = isUp ? "var(--pos, #10b981)" : "var(--neg, #ef4444)";

  const fmt = (n: number) => {
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
    return `$${n.toFixed(0)}`;
  };

  const label = `5Y Revenue: ${fmt(values[0])} → ${fmt(values[values.length - 1])} (${isUp ? "+" : ""}${(((values[values.length - 1] - values[0]) / (values[0] || 1)) * 100).toFixed(0)}%)`;

  return (
    <div className={`inline-flex items-center gap-1.5 ${className}`} title={label} aria-label={label}>
      <svg
        width={width}
        height={height}
        className="overflow-visible"
        role="img"
        aria-hidden="true"
      >
        <polyline
          fill="none"
          stroke={strokeColor}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points.join(" ")}
        />
        {points.length > 0 && (
          <circle
            cx={points[points.length - 1].split(",")[0]}
            cy={points[points.length - 1].split(",")[1]}
            r="1.8"
            fill={strokeColor}
          />
        )}
      </svg>
    </div>
  );
};

export default RevenueSparkline;