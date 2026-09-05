export interface CurrencyBadgeProps {
  currency: string | null | undefined;
  size?: "sm" | "md";
  showQuarantineNote?: boolean;
}

export function CurrencyBadge({ currency, size = "md", showQuarantineNote = false }: CurrencyBadgeProps) {
  if (!currency) return null;
  const isUSD = currency.toUpperCase() === "USD";
  const isCAD = currency.toUpperCase() === "CAD";

  return (
    <span className="inline-flex items-center gap-1.5" title={isUSD ? "US Dollar (Quarantined ledger)" : isCAD ? "Canadian Dollar (Quarantined ledger)" : `${currency} ledger`}>
      <span
        className={`inline-flex items-center font-mono font-semibold tracking-wider rounded-chip border ${
          size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-xs"
        } ${
          isUSD
            ? "border-info/40 bg-info-weak text-info"
            : isCAD
            ? "border-warn/40 bg-warn-weak text-warn"
            : "border-border bg-bg-2 text-ink-1"
        }`}
      >
        <span className="inline-block w-1.5 h-1.5 rounded-full mr-1 bg-current opacity-70" aria-hidden="true" />
        {currency.toUpperCase()}
      </span>
      {showQuarantineNote && (
        <span className="text-[10px] font-mono text-ink-2">
          (Strict ledger isolation)
        </span>
      )}
    </span>
  );
}

export default CurrencyBadge;
