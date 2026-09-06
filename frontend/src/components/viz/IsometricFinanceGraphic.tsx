import React, { useId } from "react";

interface IsometricFinanceGraphicProps {
  className?: string;
  ticker?: string;
  moat?: string;
  solvency?: string;
  hurdle?: string;
}

/**
 * Pure SVG 3D Isometric Equity Research Architecture Visual
 * Depicts the 3-tier analytical stack:
 * Layer 1: Balance Sheet & Solvency Floor
 * Layer 2: Operating Moat & Cash Engine
 * Layer 3: Valuation Hurdle & Reverse DCF Horizon
 */
export const IsometricFinanceGraphic: React.FC<IsometricFinanceGraphicProps> = ({
  className = "",
  ticker = "SPX / TSX",
  moat = "Wide Moat · 58% ROIC",
  solvency = "Pristine · Altman Z 4.8",
  hurdle = "FCF Hurdle 11.2% CAGR",
}) => {
  const rawId = useId().replace(/:/g, "_");
  const p1Id = `isoP1_${rawId}`;
  const p2Id = `isoP2_${rawId}`;
  const p3Id = `isoP3_${rawId}`;
  const goldId = `goldGlow_${rawId}`;
  const beamId = `cyanBeam_${rawId}`;
  const glowId = `glow3d_${rawId}`;

  return (
    <div className={`relative flex items-center justify-center select-none overflow-hidden ${className}`}>
      <svg
        viewBox="0 0 540 320"
        width="100%"
        height="100%"
        role="img"
        aria-label="3D Isometric Decision Architecture"
        className="max-h-[300px] w-auto drop-shadow-xl"
      >
        <defs>
          <linearGradient id={p1Id} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--bg-2)" stopOpacity="0.85" />
            <stop offset="100%" stopColor="var(--bg-3)" stopOpacity="0.95" />
          </linearGradient>

          <linearGradient id={p2Id} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--bg-2)" stopOpacity="0.9" />
            <stop offset="100%" stopColor="var(--bg-3)" stopOpacity="0.95" />
          </linearGradient>

          <linearGradient id={p3Id} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--bg-2)" stopOpacity="0.95" />
            <stop offset="100%" stopColor="var(--bg-3)" stopOpacity="0.98" />
          </linearGradient>

          <linearGradient id={goldId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.8" />
            <stop offset="100%" stopColor="var(--accent-strong)" stopOpacity="0.2" />
          </linearGradient>

          <linearGradient id={beamId} x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="var(--pos)" stopOpacity="0.15" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.85" />
          </linearGradient>

          <filter id={glowId} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Isometric Grid Floor Guidelines */}
        <g stroke="var(--border)" strokeWidth="0.5" opacity="0.4">
          <line x1="270" y1="20" x2="490" y2="150" />
          <line x1="270" y1="20" x2="50" y2="150" />
          <line x1="50" y1="150" x2="270" y2="280" />
          <line x1="490" y1="150" x2="270" y2="280" />
        </g>

        {/* Central Vertical Decision Beam */}
        <line
          x1="270"
          y1="50"
          x2="270"
          y2="250"
          stroke={`url(#${beamId})`}
          strokeWidth="2.5"
          strokeDasharray="4 2"
          opacity="0.85"
        />

        {/* ==================================================================== */}
        {/* LAYER 1: FOUNDATION (SOLVENCY & BALANCE SHEET FLOOR)                */}
        {/* Center: (270, 230), Width: 320, Height: 90                         */}
        {/* ==================================================================== */}
        <g transform="translate(0, 30)">
          {/* Slab Bottom Thickness */}
          <polygon
            points="270,240 430,150 430,165 270,255"
            fill="var(--bg-3)"
            stroke="var(--border-strong)"
            strokeWidth="1"
          />
          <polygon
            points="270,240 110,150 110,165 270,255"
            fill="var(--bg-2)"
            stroke="var(--border-strong)"
            strokeWidth="1"
          />

          {/* Slab Top Surface */}
          <polygon
            points="270,150 430,240 270,330 110,240"
            transform="translate(0, -90)"
            fill={`url(#${p1Id})`}
            stroke="var(--border-strong)"
            strokeWidth="1.2"
          />

          {/* Grid lines on Layer 1 */}
          <line x1="190" y1="195" x2="350" y2="195" stroke="var(--border)" strokeWidth="0.75" strokeDasharray="2 2" />
          <line x1="270" y1="150" x2="270" y2="240" stroke="var(--border)" strokeWidth="0.75" strokeDasharray="2 2" />

          {/* Pill Badge on Layer 1: Solvency */}
          <g transform="translate(130, 185)">
            <rect x="0" y="0" width="130" height="22" rx="4" fill="var(--bg-0)" stroke="var(--pos)" strokeWidth="1" opacity="0.9" />
            <circle cx="10" cy="11" r="3" fill="var(--pos)" />
            <text x="18" y="14" fill="var(--ink-0)" fontSize="9" fontFamily="IBM Plex Mono" fontWeight="600">
              SOLVENCY FLOOR
            </text>
          </g>
          <text x="130" y="220" fill="var(--ink-2)" fontSize="8.5" fontFamily="IBM Plex Mono">
            {solvency}
          </text>
        </g>

        {/* ==================================================================== */}
        {/* LAYER 2: CASH GENERATION ENGINE (OPERATING MOAT & ROIC)            */}
        {/* Center: (270, 150)                                                 */}
        {/* ==================================================================== */}
        <g transform="translate(0, -25)">
          {/* Slab Bottom Thickness */}
          <polygon
            points="270,200 410,120 410,132 270,212"
            fill="var(--bg-3)"
            stroke="var(--border-strong)"
            strokeWidth="1"
          />
          <polygon
            points="270,200 130,120 130,132 270,212"
            fill="var(--bg-2)"
            stroke="var(--border-strong)"
            strokeWidth="1"
          />

          {/* Slab Top Surface */}
          <polygon
            points="270,120 410,200 270,280 130,200"
            transform="translate(0, -80)"
            fill={`url(#${p2Id})`}
            stroke="var(--border-strong)"
            strokeWidth="1.2"
          />

          {/* Layer 2 Badge: Operating Moat */}
          <g transform="translate(290, 115)">
            <rect x="0" y="0" width="130" height="22" rx="4" fill="var(--bg-0)" stroke="var(--accent)" strokeWidth="1" opacity="0.95" />
            <circle cx="10" cy="11" r="3" fill="var(--accent)" />
            <text x="18" y="14" fill="var(--accent)" fontSize="9" fontFamily="IBM Plex Mono" fontWeight="600">
              OPERATING MOAT
            </text>
          </g>
          <text x="290" y="150" fill="var(--ink-2)" fontSize="8.5" fontFamily="IBM Plex Mono">
            {moat}
          </text>
        </g>

        {/* ==================================================================== */}
        {/* LAYER 3: VALUATION HORIZON (REVERSE DCF & MARGIN OF SAFETY)       */}
        {/* Center: (270, 70)                                                  */}
        {/* ==================================================================== */}
        <g transform="translate(0, -75)">
          {/* Slab Bottom Thickness */}
          <polygon
            points="270,150 390,80 390,90 270,160"
            fill="var(--bg-3)"
            stroke="var(--border-strong)"
            strokeWidth="1"
          />
          <polygon
            points="270,150 150,80 150,90 270,160"
            fill="var(--bg-2)"
            stroke="var(--border-strong)"
            strokeWidth="1"
          />

          {/* Slab Top Surface */}
          <polygon
            points="270,80 390,150 270,220 150,150"
            transform="translate(0, -70)"
            fill={`url(#${p3Id})`}
            stroke="var(--accent)"
            strokeWidth="1.5"
          />

          {/* Apex Target Needle */}
          <g filter={`url(#${glowId})`}>
            <circle cx="270" cy="80" r="5" fill="var(--accent)" />
            <circle cx="270" cy="80" r="9" fill="none" stroke="var(--accent)" strokeWidth="1.2" strokeDasharray="3 3" />
          </g>

          {/* Layer 3 Badge: Valuation Hurdle */}
          <g transform="translate(195, 20)">
            <rect x="0" y="0" width="150" height="24" rx="4" fill="var(--bg-0)" stroke="var(--accent)" strokeWidth="1.2" />
            <text x="10" y="16" fill="var(--ink-0)" fontSize="9.5" fontFamily="IBM Plex Mono" fontWeight="700">
              ★ {ticker}
            </text>
            <text x="80" y="16" fill="var(--accent)" fontSize="9" fontFamily="IBM Plex Mono">
              REVERSE DCF
            </text>
          </g>
          <text x="270" y="58" textAnchor="middle" fill="var(--ink-1)" fontSize="9" fontFamily="IBM Plex Mono">
            {hurdle}
          </text>
        </g>
      </svg>
    </div>
  );
};

export default IsometricFinanceGraphic;
