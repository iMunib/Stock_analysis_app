import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, Chip } from "./layout";

interface GrahamPayload {
  company_id: string;
  currency: string | null;
  price: number | null;
  graham_number: number | null;
  graham_margin_of_safety: number | null;
  ncav_per_share: number | null;
  ncav_margin_of_safety: number | null;
  nnwc_per_share: number | null;
  nnwc_margin_of_safety: number | null;
  deep_net_net: boolean;
  proxy: boolean;
  basis_fiscal_year: number | null;
  basis_note: string | null;
}

const money = (v: number | null | undefined) =>
  v === null || v === undefined ? "0.00" : v.toLocaleString(undefined, { maximumFractionDigits: 2 });

const mos = (v: number | null | undefined) =>
  v === null || v === undefined ? "0.00" : `${v > 0 ? "+" : ""}${(v * 100).toFixed(0)}%`;

/**
 * Graham Value Floor (analytical sprint WS4): absolute margin-of-safety meters.
 * Horizontal range shows Current Price relative to NNWC / NCAV / Graham Number.
 */
export const GrahamCard: React.FC<{ companyId: string }> = ({ companyId }) => {
  const [data, setData] = useState<GrahamPayload | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .graham(companyId)
      .then((d) => {
        if (!cancelled) setData(d as GrahamPayload);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [companyId]);

  if (failed || !data || data.graham_number === null) return null;

  // Range meter: scale from min(floor values, price) to max(...)+headroom
  const floors = [data.nnwc_per_share, data.ncav_per_share, data.graham_number].filter(
    (v): v is number => v !== null && v !== undefined,
  );
  const price = data.price;
  const values = price !== null ? [...floors, price] : floors;
  if (values.length < 2 || price === null) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pos = (v: number) => ((v - min) / span) * 100;

  const rows: { label: string; value: number | null; mos: number | null }[] = [
    { label: "NNWC / share", value: data.nnwc_per_share, mos: data.nnwc_margin_of_safety },
    { label: "NCAV / share", value: data.ncav_per_share, mos: data.ncav_margin_of_safety },
    { label: "Graham Number", value: data.graham_number, mos: data.graham_margin_of_safety },
  ];

  return (
    <Card
      title="Graham Value Floor"
      subtitle="Absolute margin-of-safety floors (The Intelligent Investor)"
      padding="md"
      action={
        data.deep_net_net ? (
          <Chip tone="positive" size="sm">
            Graham Deep Net-Net
          </Chip>
        ) : undefined
      }
    >
      {/* Price position meter (pure CSS, token colors) */}
      <div
        className="relative mb-4 h-8 rounded-chip border border-border bg-bg-2"
        role="img"
        aria-label={`Price meter: current price ${money(price)} relative to NNWC ${money(data.nnwc_per_share)}, NCAV ${money(data.ncav_per_share)}, Graham Number ${money(data.graham_number)}`}
      >
        {/* floor ticks */}
        {rows.map((r) =>
          r.value !== null ? (
            <span
              key={r.label}
              className="absolute top-0 h-full w-px bg-border-strong"
              style={{ left: `${pos(r.value)}%` }}
              title={`${r.label}: ${money(r.value)}`}
            />
          ) : null,
        )}
        {/* price marker */}
        <span
          className="absolute top-1 h-6 w-1.5 rounded-full bg-accent"
          style={{ left: `calc(${pos(price)}% - 3px)` }}
          title={`Current price: ${money(price)}`}
        />
      </div>

      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border text-left font-mono text-[10px] uppercase tracking-widest text-ink-2">
            <th className="py-1.5">Floor</th>
            <th className="py-1.5 text-right">Value / share</th>
            <th className="py-1.5 text-right">Margin of safety</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((r) => (
            <tr key={r.label}>
              <td className="py-1.5 text-ink-1">{r.label}</td>
              <td className="py-1.5 text-right font-mono tabular-nums text-ink-0">{money(r.value)}</td>
              <td
                className={`py-1.5 text-right font-mono tabular-nums ${
                  r.mos !== null && r.mos > 0 ? "text-pos" : "text-ink-1"
                }`}
              >
                {mos(r.mos)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="mt-3 text-[11px] text-ink-2 leading-relaxed">
        Graham Number = √(22.5 × EPS × BVPS). {data.proxy ? "NCAV/NNWC use a documented conservative proxy (35% of non-cash assets treated as current) - AR/inventory detail is not on file. " : ""}
        Basis: {data.basis_fiscal_year ? `FY${data.basis_fiscal_year}` : data.basis_note ?? "latest filings"}
        {data.currency ? ` · ${data.currency}` : ""}.
      </p>
    </Card>
  );
};

export default GrahamCard;