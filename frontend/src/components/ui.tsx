import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { signalLabel } from "../api/copy";

export function ErrorBanner({ message, onDismiss, onRetry }: { message: string; onDismiss?: () => void; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-md border border-bad/50 bg-bad/10 px-4 py-3 text-sm text-paper flex items-start justify-between gap-4">
      <span>{message}</span>
      <span className="flex gap-2 shrink-0">
        {onRetry && (
          <button onClick={onRetry} className="text-gold hover:underline" aria-label="Retry">
            Retry
          </button>
        )}
        {onDismiss && (
          <button onClick={onDismiss} className="text-dim hover:text-paper" aria-label="Dismiss error">
            ✕
          </button>
        )}
      </span>
    </div>
  );
}

export function SignalBadge({ signal, small }: { signal: string | null | undefined; small?: boolean }) {
  const label = signalLabel(signal);
  const color =
    signal === "strong_candidate" || signal === "constructive"
      ? "text-good border-good/40"
      : signal === "mixed"
        ? "text-mid border-mid/40"
        : signal === "weak" || signal === "avoid"
          ? "text-bad border-bad/40"
          : "text-info border-info/40";
  return (
    <span className={`inline-block rounded border px-2 py-0.5 font-mono uppercase tracking-wider ${color} ${small ? "text-[10px]" : "text-xs"}`}>
      {label}
    </span>
  );
}

export function HalalBadge({ status }: { status: string | null | undefined }) {
  const map: Record<string, { label: string; cls: string }> = {
    halal_candidate: { label: "Halal candidate", cls: "text-good border-good/40" },
    not_halal: { label: "Not halal", cls: "text-bad border-bad/40" },
    unknown: { label: "Halal unknown", cls: "text-dim border-line2" },
  };
  const it = map[status ?? "unknown"] ?? map.unknown;
  return (
    <span className={`inline-block rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${it.cls}`}>{it.label}</span>
  );
}

export function Score({ value, size }: { value: number | null | undefined; size?: "lg" | "sm" }) {
  if (value === null || value === undefined) {
    return <span className={`font-mono text-dim ${size === "lg" ? "text-4xl" : ""}`}>—</span>;
  }
  return (
    <span className={`font-mono tabular-nums text-gold ${size === "lg" ? "text-5xl" : "text-base"}`} title="Research score 0-10">
      {value.toFixed(1)}
    </span>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-fog" role="status" aria-live="polite">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-line2 border-t-gold" aria-hidden="true" />
      {label ?? "Loading…"}
    </div>
  );
}

export function CompanyLink({ companyId, children, className }: { companyId: string; children: React.ReactNode; className?: string }) {
  return (
    <Link to={`/c/${encodeURIComponent(companyId)}`} className={`text-paper underline decoration-line2 underline-offset-4 hover:decoration-gold ${className ?? ""}`}>
      {children}
    </Link>
  );
}

/** Debounced value hook for as-you-type search. */
export function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}
