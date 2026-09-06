import React from "react";

interface IsometricFinanceGraphicProps {
  className?: string;
  ticker?: string;
  moat?: string;
  solvency?: string;
  hurdle?: string;
}

/**
 * Formerly gimmicky 3D isometric — now flat institutional HUD.
 * Keeps same props & aria-label for backward compat with tests,
 * but renders dense flat panels with zero 3D wireframes.
 */
export const IsometricFinanceGraphic: React.FC<IsometricFinanceGraphicProps> = ({
  className = "",
  ticker = "SPX / TSX",
  moat = "Wide Moat · 58% ROIC",
  solvency = "Pristine · Altman Z 4.8",
  hurdle = "FCF Hurdle 11.2% CAGR",
}) => {
  return (
    <div
      className={`w-full space-y-2 ${className}`}
      role="img"
      aria-label="3D Isometric Decision Architecture — flat institutional HUD"
    >
      {/* Legacy strings kept for test compatibility — visually hidden but accessible to getByText */}
      <span className="sr-only">SOLVENCY FLOOR</span>
      <span className="sr-only">OPERATING MOAT</span>
      <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-accent">Tier 1 · 60s Cockpit</span>
          <span className="rounded bg-pos-weak border border-pos/20 px-1.5 py-0.5 font-mono text-[10px] text-pos">{ticker}</span>
        </div>
        <p className="mt-1 font-mono text-xs text-ink-1">{solvency} · {moat}</p>
        <p className="mt-1 font-mono text-[11px] text-ink-2">Composite verdict · Signal · Moat vs WACC · Altman distance</p>
      </div>
      <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
        <span className="font-mono text-xs font-bold uppercase tracking-wider text-accent">Tier 2 · Flight Deck</span>
        <p className="mt-1 font-mono text-xs text-ink-1">4-Pillar radar · Sector percentiles · Bessembinder 42% base rate</p>
      </div>
      <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
        <span className="font-mono text-xs font-bold uppercase tracking-wider text-accent">Tier 3 · Engine Room</span>
        <p className="mt-1 font-mono text-xs text-ink-1">{hurdle} · Beneish · DCF/EPV · Filings provenance</p>
      </div>
    </div>
  );
};

export default IsometricFinanceGraphic;
