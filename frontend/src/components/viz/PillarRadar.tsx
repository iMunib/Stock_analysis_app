
export interface PillarRadarProps {
  quality: number | null | undefined;
  value: number | null | undefined;
  growth: number | null | undefined;
  risk: number | null | undefined;
  size?: number;
  className?: string;
}

export function PillarRadar({
  quality,
  value,
  growth,
  risk,
  size = 220,
  className = "",
}: PillarRadarProps) {
  const cx = 110;
  const cy = 110;
  const maxR = 70;

  // Scale 0-10 to radius 0-maxR (clamped)
  const getR = (val: number | null | undefined) => {
    if (val === null || val === undefined || isNaN(val)) return 0;
    return (Math.max(0, Math.min(10, val)) / 10) * maxR;
  };

  const qR = getR(quality);
  const vR = getR(value);
  const gR = getR(growth);
  const rR = getR(risk);

  const qPoint = { x: cx, y: cy - qR };
  const vPoint = { x: cx + vR, y: cy };
  const gPoint = { x: cx, y: cy + gR };
  const rPoint = { x: cx - rR, y: cy };

  // Generate polygon points from valid pillars
  const polygonPoints = `${qPoint.x},${qPoint.y} ${vPoint.x},${vPoint.y} ${gPoint.x},${gPoint.y} ${rPoint.x},${rPoint.y}`;

  // Accessible summary
  const qStr = quality !== null && quality !== undefined ? `${quality.toFixed(1)}/10` : "unscored";
  const vStr = value !== null && value !== undefined ? `${value.toFixed(1)}/10` : "unscored";
  const gStr = growth !== null && growth !== undefined ? `${growth.toFixed(1)}/10` : "unscored";
  const rStr = risk !== null && risk !== undefined ? `${risk.toFixed(1)}/10` : "unscored";
  const ariaLabel = `Pillar radar chart: Quality ${qStr}, Value ${vStr}, Growth ${gStr}, Risk ${rStr}`;

  return (
    <div className={`relative flex flex-col items-center ${className}`}>
      <svg
        viewBox="0 0 220 220"
        width={size}
        height={size}
        role="img"
        aria-label={ariaLabel}
        className="overflow-visible"
      >
        {/* Background Grid: Concentric Reference Polygons (2.5, 5.0, 7.5, 10.0) */}
        {[0.25, 0.5, 0.75, 1.0].map((step) => {
          const r = maxR * step;
          return (
            <polygon
              key={step}
              points={`${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`}
              fill="none"
              stroke="var(--border)"
              strokeWidth={step === 1.0 ? "1.5" : "1"}
              strokeDasharray={step === 1.0 ? undefined : "2 2"}
            />
          );
        })}

        {/* Cross Axes */}
        <line x1={cx} y1={cy - maxR} x2={cx} y2={cy + maxR} stroke="var(--border)" strokeWidth="1" />
        <line x1={cx - maxR} y1={cy} x2={cx + maxR} y2={cy} stroke="var(--border)" strokeWidth="1" />

        {/* Value Polygon */}
        <polygon
          points={polygonPoints}
          fill="var(--accent-weak)"
          stroke="var(--accent)"
          strokeWidth="2"
          strokeLinejoin="round"
          className="transition-all duration-300"
        />

        {/* Quality Vertex (North) */}
        {quality !== null && quality !== undefined ? (
          <circle cx={qPoint.x} cy={qPoint.y} r="3.5" fill="var(--accent)" />
        ) : (
          <circle cx={cx} cy={cy - maxR} r="3.5" fill="var(--bg-1)" stroke="var(--ink-2)" strokeWidth="1.5" />
        )}

        {/* Value Vertex (East) */}
        {value !== null && value !== undefined ? (
          <circle cx={vPoint.x} cy={vPoint.y} r="3.5" fill="var(--accent)" />
        ) : (
          <circle cx={cx + maxR} cy={cy} r="3.5" fill="var(--bg-1)" stroke="var(--ink-2)" strokeWidth="1.5" />
        )}

        {/* Growth Vertex (South) */}
        {growth !== null && growth !== undefined ? (
          <circle cx={gPoint.x} cy={gPoint.y} r="3.5" fill="var(--accent)" />
        ) : (
          <circle cx={cx} cy={cy + maxR} r="3.5" fill="var(--bg-1)" stroke="var(--ink-2)" strokeWidth="1.5" />
        )}

        {/* Risk Vertex (West) */}
        {risk !== null && risk !== undefined ? (
          <circle cx={rPoint.x} cy={rPoint.y} r="3.5" fill="var(--accent)" />
        ) : (
          <circle cx={cx - maxR} cy={cy} r="3.5" fill="var(--bg-1)" stroke="var(--ink-2)" strokeWidth="1.5" />
        )}

        {/* Axis Labels */}
        <text
          x={cx}
          y={cy - maxR - 12}
          textAnchor="middle"
          className="font-mono text-[10px] uppercase font-semibold fill-ink-1"
        >
          Quality {quality !== null && quality !== undefined ? quality.toFixed(1) : "—"}
        </text>

        <text
          x={cx + maxR + 10}
          y={cy + 4}
          textAnchor="start"
          className="font-mono text-[10px] uppercase font-semibold fill-ink-1"
        >
          Value {value !== null && value !== undefined ? value.toFixed(1) : "—"}
        </text>

        <text
          x={cx}
          y={cy + maxR + 18}
          textAnchor="middle"
          className="font-mono text-[10px] uppercase font-semibold fill-ink-1"
        >
          Growth {growth !== null && growth !== undefined ? growth.toFixed(1) : "—"}
        </text>

        <text
          x={cx - maxR - 10}
          y={cy + 4}
          textAnchor="end"
          className="font-mono text-[10px] uppercase font-semibold fill-ink-1"
        >
          Risk {risk !== null && risk !== undefined ? risk.toFixed(1) : "—"}
        </text>
      </svg>
    </div>
  );
}

export default PillarRadar;
