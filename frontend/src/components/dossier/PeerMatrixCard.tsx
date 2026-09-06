import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { PeerMatrixMetric, PeerMatrixOut } from "../../api/types";
import { Card } from "../layout";

interface PeerMatrixCardProps {
  companyId: string;
}

export const PeerMatrixCard: React.FC<PeerMatrixCardProps> = ({ companyId }) => {
  const [data, setData] = useState<PeerMatrixOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.peerMatrix(companyId)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load peer matrix");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [companyId]);

  if (loading) {
    return (
      <Card padding="md" className="animate-pulse">
        <div className="h-5 bg-bg-2 rounded w-1/3 mb-4" />
        <div className="h-28 bg-bg-2/50 rounded" />
      </Card>
    );
  }

  if (error || !data || !data.pillars) {
    return null;
  }

  const renderMetric = (label: string, m?: PeerMatrixMetric, format: "pct" | "multiple" | "raw" = "raw") => {
    if (!m) return null;
    const pct = m.percentile ?? 50;

    let displayVal = "Not reported in filing";
    if (m.value !== null && m.value !== undefined) {
      if (format === "pct") {
        displayVal = `${(m.value * (Math.abs(m.value) < 1 ? 100 : 1)).toFixed(1)}%`;
      } else if (format === "multiple") {
        displayVal = `${m.value.toFixed(1)}x`;
      } else {
        displayVal = m.value.toFixed(2);
      }
    }

    const barColor =
      pct >= 70 ? "bg-pos" : pct >= 40 ? "bg-accent" : "bg-neg";

    return (
      <div className="py-1.5 text-xs">
        <div className="flex items-center justify-between text-[11px] mb-1">
          <span className="text-ink-1 font-medium">{label}</span>
          <div className="flex items-center gap-2 font-mono">
            <span className="text-ink-0 font-semibold">{displayVal}</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-bg-2 text-ink-2">
              P{Math.round(pct)}
            </span>
          </div>
        </div>
        <div className="w-full bg-bg-2 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <span>Sector Peer Percentile Matrix</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-bg-2 text-info font-mono uppercase">
            Same-Currency Cohort
          </span>
        </div>
      }
      subtitle={`Empirical percentile ranks (0–100%) against ${data.peer_count} peer companies in ${data.peer_group}`}
      padding="md"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pillar 1: Valuation */}
        <div className="rounded-card border border-border bg-surface-1 p-3">
          <div className="flex items-center justify-between pb-1.5 mb-2 border-b border-border">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink-0">
              Valuation
            </span>
            <span className="text-[10px] font-mono text-ink-2">Cheaper = Higher Pct</span>
          </div>
          <div className="space-y-1">
            {renderMetric("P/E Ratio", data.pillars.valuation?.pe_ratio, "multiple")}
            {renderMetric("P/B Ratio", data.pillars.valuation?.pb_ratio, "multiple")}
            {renderMetric("EV / EBITDA", data.pillars.valuation?.ev_to_ebitda, "multiple")}
            {renderMetric("Owner Earnings Yield", data.pillars.valuation?.owner_earnings_yield, "pct")}
          </div>
        </div>

        {/* Pillar 2: Quality */}
        <div className="rounded-card border border-border bg-surface-1 p-3">
          <div className="flex items-center justify-between pb-1.5 mb-2 border-b border-border">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink-0">
              Quality
            </span>
            <span className="text-[10px] font-mono text-ink-2">Higher = Superior</span>
          </div>
          <div className="space-y-1">
            {renderMetric("ROIC", data.pillars.quality?.roic, "pct")}
            {renderMetric("ROE", data.pillars.quality?.roe, "pct")}
            {renderMetric("Gross Margin", data.pillars.quality?.gross_margin, "pct")}
            {renderMetric("Operating Margin", data.pillars.quality?.operating_margin, "pct")}
          </div>
        </div>

        {/* Pillar 3: Financial Health */}
        <div className="rounded-card border border-border bg-surface-1 p-3">
          <div className="flex items-center justify-between pb-1.5 mb-2 border-b border-border">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink-0">
              Financial Health
            </span>
            <span className="text-[10px] font-mono text-ink-2">Solvency &amp; Safety</span>
          </div>
          <div className="space-y-1">
            {renderMetric("Altman Z-Score", data.pillars.financial_health?.altman_z, "raw")}
            {renderMetric("Net Debt / EBITDA", data.pillars.financial_health?.net_debt_to_ebitda, "multiple")}
          </div>
        </div>

        {/* Pillar 4: Capital Allocation */}
        <div className="rounded-card border border-border bg-surface-1 p-3">
          <div className="flex items-center justify-between pb-1.5 mb-2 border-b border-border">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink-0">
              Capital Allocation
            </span>
            <span className="text-[10px] font-mono text-ink-2">Shareholder Returns</span>
          </div>
          <div className="space-y-1">
            {renderMetric("True Shareholder Yield", data.pillars.capital_allocation?.true_shareholder_yield, "pct")}
            {renderMetric("3Y Float Shrink CAGR", data.pillars.capital_allocation?.float_shrink_3y_pct, "pct")}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default PeerMatrixCard;