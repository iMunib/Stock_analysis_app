import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Card, Chip } from "../layout";

interface BankValuationCardProps {
  companyId: string;
}

export const BankValuationCard: React.FC<BankValuationCardProps> = ({ companyId }) => {
  const [ddm, setDdm] = useState<any | null>(null);
  const [ri, setRi] = useState<any | null>(null);
  const [isFinancial, setIsFinancial] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    // Probe via guided DCF to see if financial
    api.requestGuided(companyId).then((g: any) => {
      if (!cancelled && g?.is_financial) setIsFinancial(true);
    }).catch(()=>{});
    Promise.allSettled([api.requestDDM(companyId), api.requestResidual(companyId)]).then(([r1, r2]) => {
      if (cancelled) return;
      if (r1.status === "fulfilled") setDdm(r1.value);
      if (r2.status === "fulfilled") setRi(r2.value);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [companyId]);

  if (loading) return <Card padding="md" className="animate-pulse"><div className="h-20 bg-bg-2 rounded" /></Card>;

  // If not financial, show routing notice but still allow DDM display
  return (
    <Card
      title="Bank / Insurer Valuation - DDM & Residual Income"
      subtitle="Sector-appropriate models (FCF DCF not meaningful for Financials)"
      padding="md"
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Chip tone={isFinancial ? "warning" : "info"} size="sm">{isFinancial ? "Financial sector - DDM/Residual routed" : "DDM available for all; Residual primary for banks"}</Chip>
        {!isFinancial && <span className="text-xs text-ink-2">Standard FCF DCF remains available in the Guided DCF sandbox below.</span>}
      </div>

      {/* DDM */}
      <div className="rounded-card border border-border bg-bg-0 p-3 mb-3">
        <h4 className="font-heading text-sm font-semibold text-ink-0">Dividend Discount Model (Multi-Stage Gordon)</h4>
        {ddm?.status === "computed" ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-2 text-xs">
            <div><span className="font-mono text-[10px] uppercase text-ink-2 block">Fair Value / Share</span><span className="font-mono font-bold text-ink-0">{ddm.fair_value_per_share != null ? `$${ddm.fair_value_per_share.toFixed(2)}` : "0.00"}</span></div>
            <div><span className="font-mono text-[10px] uppercase text-ink-2 block">Yield / Payout</span><span className="font-mono text-ink-0">{ddm.dividend_yield_pct ?? "0.0%"}% / {ddm.payout_ratio_pct ?? "0.0%"}%</span></div>
            <div><span className="font-mono text-[10px] uppercase text-ink-2 block">Cost of Equity / g</span><span className="font-mono text-ink-0">{(ddm.cost_of_equity*100).toFixed(1)}% / {(ddm.gordon_g*100).toFixed(1)}%</span></div>
          </div>
        ) : (
          <p className="text-xs text-ink-1 mt-2">Insufficient dividend history - {ddm?.reason ?? "requires 3+ years"} <span className="text-ink-2">({ddm?.status})</span></p>
        )}
        <p className="text-[11px] text-ink-1 mt-2">DDM: P0 = D1/(k−g) with 5-yr supernormal where payout history supports it. Dividends derived via retained-earnings walk (NI − ΔRE) where explicit dividends_paid absent.</p>
      </div>

      {/* Residual Income */}
      <div className="rounded-card border border-border bg-bg-0 p-3">
        <h4 className="font-heading text-sm font-semibold text-ink-0">Residual Income - Excess Returns</h4>
        {ri?.status === "computed" ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-2 text-xs">
            <div><span className="font-mono text-[10px] uppercase text-ink-2 block">Equity Value / Share</span><span className="font-mono font-bold text-ink-0">{ri.equity_value_per_share != null ? `$${ri.equity_value_per_share.toFixed(2)}` : "0.00"}</span></div>
            <div><span className="font-mono text-[10px] uppercase text-ink-2 block">Book / Norm ROE</span><span className="font-mono text-ink-0">${(ri.book_equity/1e9).toFixed(2)}B / {(ri.normalized_roe*100).toFixed(1)}%</span></div>
            <div><span className="font-mono text-[10px] uppercase text-ink-2 block">Cost Eq / Excess</span><span className="font-mono text-ink-0">{(ri.cost_of_equity*100).toFixed(1)}% / {(ri.excess_roe*100).toFixed(1)}%</span></div>
          </div>
        ) : ri?.status === "not_applicable" ? (
          <p className="text-xs text-ink-2 mt-2">Residual Income primary for banks/insurers - not applicable for this sector. {ri.reason}</p>
        ) : (
          <p className="text-xs text-ink-1 mt-2">Insufficient book/earnings history - {ri?.reason ?? "requires 3+ years"}.</p>
        )}
        <p className="text-[11px] text-ink-1 mt-2">Residual Income: Equity + PV(Excess ROE over Cost of Equity). Book + (ROE−k)×Book / k. Perpetuity of excess returns.</p>
      </div>

      <p className="text-[11px] font-mono text-ink-2 mt-3">Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.</p>
    </Card>
  );
};

export default BankValuationCard;