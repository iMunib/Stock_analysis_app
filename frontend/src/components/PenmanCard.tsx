import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, Chip } from "./layout";

interface PenmanPayload {
  company_id: string;
  status: string;
  fiscal_year?: number | null;
  rnoa?: number | null;
  flev?: number | null;
  nbc?: number | null;
  nopat?: number | null;
  noa?: number | null;
  nfo?: number | null;
  roe_operational_spread?: number | null;
  identity_ok?: boolean | null;
  leverage_distortion?: boolean | null;
  exclusion?: string | null;
}

const pct = (v: number | null | undefined) =>
  v === null || v === undefined ? "—" : `${(v * 100).toFixed(1)}%`;

/**
 * Penman Economic Engine (analytical sprint WS2): separates operating
 * performance (RNOA) from financial leverage (FLEV x spread). RNOA is the
 * honest operating return when book equity is buyback-shrunken.
 */
export const PenmanCard: React.FC<{ companyId: string }> = ({ companyId }) => {
  const [data, setData] = useState<PenmanPayload | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .penman(companyId)
      .then((d) => {
        if (!cancelled) setData(d as PenmanPayload);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [companyId]);

  if (failed || !data || data.status === "insufficient_data") return null;

  if (data.exclusion === "financial_institution_excluded") {
    return (
      <Card
        title="Penman Economic Engine"
        subtitle="Operating vs financing decomposition"
        padding="md"
      >
        <Chip tone="neutral" size="sm">
          financial_institution_excluded
        </Chip>
        <p className="mt-2 text-xs text-ink-1 leading-relaxed">
          Banks and insurers do not separate operating from financing activities —
          RNOA/NFO are not meaningful. Use CET1, efficiency ratio, and ROE instead.
        </p>
      </Card>
    );
  }

  const leveraged = data.leverage_distortion === true;

  return (
    <Card
      title="Penman Economic Engine"
      subtitle="RNOA strips financing leverage out of returns — the honest operating view"
      tone={leveraged ? "warning" : "neutral"}
      padding="md"
    >
      {leveraged && (
        <div role="status" className="mb-3 rounded-card border border-warn/40 bg-warn-weak px-3 py-2 text-xs text-ink-1">
          High ROE/ROIC is driven by financial leverage (FLEV), not superior operating
          returns. Economic operating return is RNOA.
        </div>
      )}
      <dl className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
        <div>
          <dt className="font-mono uppercase text-ink-2">RNOA</dt>
          <dd className="mt-0.5 font-mono text-base font-semibold text-ink-0">{pct(data.rnoa)}</dd>
        </div>
        <div>
          <dt className="font-mono uppercase text-ink-2">FLEV</dt>
          <dd className="mt-0.5 font-mono text-base text-ink-0">
            {data.flev === null || data.flev === undefined ? "—" : `${data.flev.toFixed(2)}x`}
          </dd>
        </div>
        <div>
          <dt className="font-mono uppercase text-ink-2">Net borrowing cost</dt>
          <dd className="mt-0.5 font-mono text-base text-ink-0">{pct(data.nbc)}</dd>
        </div>
        <div>
          <dt className="font-mono uppercase text-ink-2">RNOA − NBC spread</dt>
          <dd className="mt-0.5 font-mono text-base text-ink-0">{pct(data.roe_operational_spread)}</dd>
        </div>
      </dl>
      <p className="mt-3 text-[11px] text-ink-2 leading-relaxed">
        NOPAT = operating income × (1 − tax, clamped 15–30%). NOA = (assets − cash) −
        (liabilities − debt). RNOA = NOPAT / NOA. Basis:{" "}
        {data.fiscal_year ? `FY${data.fiscal_year}` : "owner-workbook seed"}
        {data.identity_ok === false ? " · balance-sheet identity gap >5% (minority interest/preferred likely)" : ""}
      </p>
    </Card>
  );
};

export default PenmanCard;
