import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Card, Chip } from "../layout";

interface InsiderActivityCardProps {
  companyId: string;
}

export const InsiderActivityCard: React.FC<InsiderActivityCardProps> = ({ companyId }) => {
  const [data, setData] = useState<any | null>(null);
  const [pureMode, setPureMode] = useState(() => {
    try { return localStorage.getItem("filingsOnlyPureMode") === "1"; } catch { return false; }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try { localStorage.setItem("filingsOnlyPureMode", pureMode ? "1" : "0"); } catch {}
  }, [pureMode]);

  useEffect(() => {
    let cancelled = false;
    api
      .requestInsiders(companyId, pureMode)
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [companyId, pureMode]);

  if (loading) return <Card padding="md" className="animate-pulse"><div className="h-20 bg-bg-2 rounded" /></Card>;
  if (!data) return null;

  const filings: any[] = data.filings ?? [];
  const cluster = data.cluster ?? {};

  return (
    <Card
      title="SEC Form 4 - Insider Activity & Cluster Detector"
      subtitle="Filed historical facts - cluster ≥3 distinct open-market buyers in 90 days"
      padding="md"
    >
      <div className="flex items-center justify-between mb-3">
        <label className="flex items-center gap-2 text-xs font-mono cursor-pointer">
          <input type="checkbox" checked={pureMode} onChange={(e) => setPureMode(e.target.checked)} className="rounded" aria-label="Filings-only pure mode" />
          Filings-only pure mode (verified SEC/SEDAR+ only, no editorial noise)
        </label>
        {cluster.cluster_buy && <Chip tone="positive" size="sm">Cluster Buy - {cluster.distinct_buyers} buyers in 90d</Chip>}
      </div>

      {cluster.cluster_buy && (
        <div className="mb-3 rounded border border-pos/30 bg-pos-weak p-2 text-xs">
          <strong className="text-pos">High-conviction cluster:</strong> {cluster.cluster_buyers?.join(", ")} within {cluster.cluster_window?.[0]} → {cluster.cluster_window?.[1]} (90-day window). Open-market cash purchases, 10b5-1 excluded.
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-xs" role="table" aria-label="Insider transactions">
          <thead>
            <tr className="border-b border-border text-left font-mono text-[10px] uppercase text-ink-2">
              <th className="py-1.5 px-2">Insider</th>
              <th className="py-1.5 px-2">Role</th>
              <th className="py-1.5 px-2">Type</th>
              <th className="py-1.5 px-2 text-right">Shares</th>
              <th className="py-1.5 px-2 text-right">Price</th>
              <th className="py-1.5 px-2">Tag</th>
              <th className="py-1.5 px-2">Filing Date</th>
              <th className="py-1.5 px-2 text-right">Lag</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {filings.slice(0, 8).map((f: any, idx: number) => (
              <tr key={idx} className="hover:bg-bg-2/40">
                <td className="py-1.5 px-2 font-medium">{f.insider_name}</td>
                <td className="py-1.5 px-2 font-mono text-ink-2">{f.role}</td>
                <td className="py-1.5 px-2 font-mono">{f.transaction_type}</td>
                <td className="py-1.5 px-2 text-right font-mono">{f.shares?.toLocaleString()}</td>
                <td className="py-1.5 px-2 text-right font-mono">{f.price != null ? `$${f.price.toFixed(2)}` : "0.00"}</td>
                <td className="py-1.5 px-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${f.is_10b5_1 ? "bg-warn-weak text-warn border-warn/30" : f.is_open_market ? "bg-pos-weak text-pos border-pos/30" : "bg-bg-2 text-ink-2"}`}>
                    {f.opportunistic_tag}
                  </span>
                </td>
                <td className="py-1.5 px-2 font-mono text-ink-2">
                  <a href={f.filing_url} target="_blank" rel="noreferrer" className="text-accent hover:underline" aria-label={`Form 4 filing ${f.filing_date}`}>{f.filing_date}</a>
                  <span className="text-[10px] text-ink-2 ml-1">as-of {f.reporting_date}</span>
                </td>
                <td className="py-1.5 px-2 text-right font-mono text-ink-2">{f.lag_days != null ? `${f.lag_days}d` : "0.00"}</td>
              </tr>
            ))}
            {filings.length === 0 && <tr><td colSpan={8} className="py-4 text-center text-ink-2">No Form 4 filings - filings-only pure mode shows verified SEC/SEDAR+ events only.</td></tr>}
          </tbody>
        </table>
      </div>

      <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2 mt-3">Personal research software, not investment advice. Price momentum is market sentiment context, not an intrinsic verdict. Insider transactions are filed historical facts.</p>
    </Card>
  );
};

export default InsiderActivityCard;