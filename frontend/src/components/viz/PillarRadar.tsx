
import { useId } from "react";

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
  const rawId = useId().replace(/:/g, "_");
  const gradId = `radarGrad_${rawId}`;
  const glowId = `vertexGlow_${rawId}`;

  const cx = 140;
  const cy = 112;
  const maxR = 66;

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
    <div className={`relative flex flex-col items-center select-none ${className}`}>
      <svg
        viewBox="0 0 280 230"
        width={size}
        height={Math.round((size * 230) / 280)}
        role="img"
        aria-label={ariaLabel}
        className="overflow-visible"
      >
        <defs>
          <radialGradient id={gradId} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.35" />
            <stop offset="65%" stopColor="var(--accent)" stopOpacity="0.18" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.04" />
          </radialGradient>
          <filter id={glowId} x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor="var(--accent)" floodOpacity="0.6" />
          </filter>
        </defs>

        {/* Circular background tint */}
        <circle cx={cx} cy={cy} r={maxR} fill="var(--bg-2)" opacity="0.3" />

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
              opacity={step === 1.0 ? 0.9 : 0.6}
            />
          );
        })}

        {/* Diagonal Cross Webbing (Corner to Corner) */}
        <line x1={cx - maxR * 0.707} y1={cy - maxR * 0.707} x2={cx + maxR * 0.707} y2={cy + maxR * 0.707} stroke="var(--border)" strokeWidth="0.75" strokeDasharray="1 3" opacity="0.5" />
        <line x1={cx - maxR * 0.707} y1={cy + maxR * 0.707} x2={cx + maxR * 0.707} y2={cy - maxR * 0.707} stroke="var(--border)" strokeWidth="0.75" strokeDasharray="1 3" opacity="0.5" />

        {/* Cross Axes */}
        <line x1={cx} y1={cy - maxR} x2={cx} y2={cy + maxR} stroke="var(--border-strong)" strokeWidth="1" />
        <line x1={cx - maxR} y1={cy} x2={cx + maxR} y2={cy} stroke="var(--border-strong)" strokeWidth="1" />

        {/* Value Polygon */}
        <polygon
          points={polygonPoints}
          fill={`url(#${gradId})`}
          stroke="var(--accent)"
          strokeWidth="2.2"
          strokeLinejoin="round"
          className="transition-all duration-300"
        />

        {/* Quality Vertex (North) */}
        {quality !== null && quality !== undefined ? (
          <g filter={`url(#${glowId})`}>
            <circle cx={qPoint.x} cy={qPoint.y} r="3.5" fill="var(--accent)" />
          </g>
        ) : (
          <circle cx={cx} cy={cy - maxR} r="3.5" fill="var(--bg-1)" stroke="var(--ink-2)" strokeWidth="1.5" />
        )}

        {/* Value Vertex (East) */}
        {value !== null && value !== undefined ? (
          <g filter={`url(#${glowId})`}>
            <circle cx={vPoint.x} cy={vPoint.y} r="3.5" fill="var(--accent)" />
          </g>
        ) : (
          <circle cx={cx + maxR} cy={cy} r="3.5" fill="var(--bg-1)" stroke="var(--ink-2)" strokeWidth="1.5" />
        )}

        {/* Growth Vertex (South) */}
        {growth !== null && growth !== undefined ? (
          <g filter={`url(#${glowId})`}>
            <circle cx={gPoint.x} cy={gPoint.y} r="3.5" fill="var(--accent)" />
          </g>
        ) : (
          <circle cx={cx} cy={cy + maxR} r="3.5" fill="var(--bg-1)" stroke="var(--ink-2)" strokeWidth="1.5" />
        )}

        {/* Risk Vertex (West) */}
        {risk !== null && risk !== undefined ? (
          <g filter={`url(#${glowId})`}>
            <circle cx={rPoint.x} cy={rPoint.y} r="3.5" fill="var(--accent)" />
          </g>
        ) : (
          <circle cx={cx - maxR} cy={cy} r="3.5" fill="var(--bg-1)" stroke="var(--ink-2)" strokeWidth="1.5" />
        )}

        {/* Axis Labels (positioned safely inside viewBox 280x230) */}
        <text
          x={cx}
          y={cy - maxR - 12}
          textAnchor="middle"
          className="font-mono text-[10px] uppercase font-semibold fill-ink-1"
        >
          Quality {quality !== null && quality !== undefined ? quality.toFixed(1) : "0.00"}
        </text>

        <text
          x={cx + maxR + 10}
          y={cy + 4}
          textAnchor="start"
          className="font-mono text-[10px] uppercase font-semibold fill-ink-1"
        >
          Value {value !== null && value !== undefined ? value.toFixed(1) : "0.00"}
        </text>

        <text
          x={cx}
          y={cy + maxR + 18}
          textAnchor="middle"
          className="font-mono text-[10px] uppercase font-semibold fill-ink-1"
        >
          Growth {growth !== null && growth !== undefined ? growth.toFixed(1) : "0.00"}
        </text>

        <text
          x={cx - maxR - 10}
          y={cy + 4}
          textAnchor="end"
          className="font-mono text-[10px] uppercase font-semibold fill-ink-1"
        >
          Risk {risk !== null && risk !== undefined ? risk.toFixed(1) : "0.00"}
        </text>
      </svg>
    </div>
  );
}

export default PillarRadar;