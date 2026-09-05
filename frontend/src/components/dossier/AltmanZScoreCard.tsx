import Tooltip from "../ui/Tooltip";

export interface AltmanZScoreCardProps {
  zScore?: number | null;
  zone?: "Safe" | "Grey" | "Distress" | string | null;
  x1?: number | null; // Working Capital / Total Assets
  x2?: number | null; // Retained Earnings / Total Assets
  x3?: number | null; // EBIT / Total Assets
  x4?: number | null; // Market Value Equity / Total Liabilities
  x5?: number | null; // Sales / Total Assets
  className?: string;
}

export function AltmanZScoreCard({
  zScore,
  zone,
  x1,
  x2,
  x3,
  x4,
  x5,
  className = "",
}: AltmanZScoreCardProps) {
  const score = zScore ?? null;
  const inferredZone =
    zone ?? (score != null ? (score > 2.99 ? "Safe" : score < 1.81 ? "Distress" : "Grey") : "Unavailable");

  const zoneConfig: Record<string, { label: string; badge: string; text: string }> = {
    Safe: {
      label: "SAFE ZONE (Z > 2.99)",
      badge: "bg-pos-weak border-pos/40 text-pos",
      text: "Negligible 24-month bankruptcy probability.",
    },
    Grey: {
      label: "GREY ZONE (1.81 - 2.99)",
      badge: "bg-warn-weak border-warn/40 text-warn",
      text: "Moderate vulnerability to liquidity squeezes.",
    },
    Distress: {
      label: "DISTRESS ZONE (Z < 1.81)",
      badge: "bg-neg-weak border-neg/40 text-neg",
      text: "High probability of balance sheet distress.",
    },
    Excluded: {
      label: "EXCLUDED (FINANCIALS)",
      badge: "bg-bg-2 border-border text-ink-2",
      text: "Altman Z is inapplicable for banks and financials where capital ratios supersede corporate debt models.",
    },
    Unavailable: {
      label: "DATA PENDING",
      badge: "bg-bg-2 border-border text-ink-2",
      text: "Balance sheet filing history pending or insufficient to compute distress suite.",
    },
  };

  const currentZone = zoneConfig[inferredZone] || (score != null ? zoneConfig.Grey : zoneConfig.Unavailable);

  const factors = [
    { code: "X1", name: "Working Capital / Assets", value: x1, weight: "1.2" },
    { code: "X2", name: "Retained Earnings / Assets", value: x2, weight: "1.4" },
    { code: "X3", name: "EBIT / Total Assets", value: x3, weight: "3.3" },
    { code: "X4", name: "Market Equity / Liabilities", value: x4, weight: "0.6" },
    { code: "X5", name: "Sales / Total Assets", value: x5, weight: "1.0" },
  ];

  return (
    <div
      className={`rounded-card border border-border bg-bg-1 p-4 shadow-card transition-colors ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/70 pb-3 mb-3">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
              Edward Altman Distress & Solvency Suite
            </span>
            <Tooltip term="altman" />
          </div>
          <p className="text-xs text-ink-2 mt-0.5 font-mono">
            {currentZone.text}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase text-ink-2 block">Altman Z-Score</span>
            <span className="font-mono text-base font-bold text-ink-0">
              {score != null ? score.toFixed(2) : "—"}
            </span>
          </div>
          <span className={`rounded-chip border px-2.5 py-1 font-mono text-xs font-bold ${currentZone.badge}`}>
            {currentZone.label}
          </span>
        </div>
      </div>

      {/* 5-Factor Decomposition Grid */}
      <div className="space-y-1.5 font-mono text-xs">
        {factors.map((f) => (
          <div
            key={f.code}
            className="flex items-center justify-between p-1.5 rounded bg-bg-0 border border-border/50"
          >
            <div className="flex items-center gap-2 truncate">
              <span className="font-bold text-accent">{f.code}</span>
              <span className="text-ink-1 truncate">{f.name}</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[10px] text-ink-2 font-normal">(w: {f.weight})</span>
              <span className="font-semibold text-ink-0">
                {f.value != null ? f.value.toFixed(2) : "—"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AltmanZScoreCard;
