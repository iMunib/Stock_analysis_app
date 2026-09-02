
export interface SparklineProps {
  data: (number | null | undefined)[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
  ariaLabel?: string;
}

export function Sparkline({
  data,
  width = 60,
  height = 20,
  color = "var(--accent)",
  className = "",
  ariaLabel = "Historical trend sparkline",
}: SparklineProps) {
  // Filter valid numbers
  const validPoints = data
    .map((val, idx) => ({ val, idx }))
    .filter((p): p is { val: number; idx: number } => p.val !== null && p.val !== undefined && !isNaN(p.val));

  if (validPoints.length < 2) {
    return (
      <div
        style={{ width, height }}
        className={`inline-flex items-center justify-center text-[10px] font-mono text-ink-2 ${className}`}
      >
        —
      </div>
    );
  }

  const values = validPoints.map((p) => p.val);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  // Add padding around edges
  const padX = 2;
  const padY = 3;
  const plotW = width - padX * 2;
  const plotH = height - padY * 2;

  const points = validPoints.map((p) => {
    const x = padX + (p.idx / (data.length - 1 || 1)) * plotW;
    const y = padY + plotH - ((p.val - min) / range) * plotH;
    return { x, y, val: p.val };
  });

  const linePath = points.reduce((acc, p, i) => `${acc} ${i === 0 ? "M" : "L"} ${p.x.toFixed(1)},${p.y.toFixed(1)}`, "");
  const lastPoint = points[points.length - 1];

  // Area path: line path + close down to baseline
  const areaPath = `${linePath} L ${lastPoint.x.toFixed(1)},${height} L ${points[0].x.toFixed(1)},${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      role="img"
      aria-label={ariaLabel}
      className={`inline-block overflow-visible ${className}`}
    >
      {/* Area fill */}
      <path d={areaPath} fill="var(--accent-weak)" />

      {/* Stroke line */}
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Final point marker */}
      <circle cx={lastPoint.x} cy={lastPoint.y} r="2" fill={color} />
    </svg>
  );
}

export default Sparkline;
