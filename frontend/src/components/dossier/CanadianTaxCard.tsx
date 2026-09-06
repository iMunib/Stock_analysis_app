import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Card, Chip } from "../layout";

interface CanadianTaxCardProps {
  companyId: string;
}

export const CanadianTaxCard: React.FC<CanadianTaxCardProps> = ({ companyId }) => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .requestCanadianTax(companyId)
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [companyId]);

  if (loading) return <Card padding="md" className="animate-pulse"><div className="h-20 bg-bg-2 rounded" /></Card>;
  if (!data) return null;

  return (
    <Card
      title="Canadian Tax-Account Placement Guide"
      subtitle="Informational - TFSA/RRSP/FHSA/Non-Registered optimization (not tax advice)"
      padding="md"
    >
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2 text-[11px] font-mono">
          <Chip tone={data.is_us_dividend_payer ? "warning" : "info"} size="sm">{data.is_us_dividend_payer ? "US dividend payer" : "CA eligible"}</Chip>
          <Chip tone="info" size="sm">{data.is_canadian_eligible ? "Canadian eligible" : "US withholding applies"}</Chip>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {Object.entries(data.guides ?? {}).map(([acct, guide]: any) => (
            <div key={acct} className="rounded border border-border bg-bg-0 p-3">
              <span className="font-mono text-xs font-semibold text-ink-0">{acct}</span>
              <p className="text-xs text-ink-1 mt-1 leading-relaxed">{guide.withholding}</p>
              <p className="text-[11px] text-ink-2 mt-1">{guide.note}</p>
              <p className="text-[11px] font-mono text-accent mt-1">Best for: {guide.best_for}</p>
            </div>
          ))}
        </div>

        <div className="rounded border border-border bg-bg-2/40 p-2 text-[11px] text-ink-2">
          Example: $100 US dividend in TFSA → $15 withholding lost (net $85). In RRSP → $0 withholding via treaty (net $100). Canadian eligible $100 dividend in Non-Registered → gross-up 38% → $138 taxable, federal credit ~15% + provincial → tax-efficient.
        </div>

        <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Informational, not tax advice. Consult a Canadian tax professional. Personal research software, not investment advice.</p>
      </div>
    </Card>
  );
};

export default CanadianTaxCard;