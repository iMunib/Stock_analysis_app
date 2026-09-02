import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { signalLabel } from "../api/copy";
import { Chip, type ChipTone } from "./layout/Chip";

export function ErrorBanner({ message, onDismiss, onRetry }: { message: string; onDismiss?: () => void; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-card border border-neg/50 bg-neg-weak px-4 py-3 text-sm text-ink-0 flex items-start justify-between gap-4">
      <span>{message}</span>
      <span className="flex gap-2 shrink-0">
        {onRetry && (
          <button onClick={onRetry} className="text-accent hover:underline font-mono text-xs" aria-label="Retry">
            Retry
          </button>
        )}
        {onDismiss && (
          <button onClick={onDismiss} className="text-ink-2 hover:text-ink-0" aria-label="Dismiss error">
            ✕
          </button>
        )}
      </span>
    </div>
  );
}

export function SignalBadge({ signal, small }: { signal: string | null | undefined; small?: boolean }) {
  const label = signalLabel(signal);
  const tone: ChipTone =
    signal === "strong_candidate" || signal === "constructive"
      ? "positive"
      : signal === "mixed"
        ? "warning"
        : signal === "weak" || signal === "avoid"
          ? "negative"
          : "info";

  return (
    <Chip tone={tone} size={small ? "sm" : "md"}>
      {label}
    </Chip>
  );
}

export function HalalBadge({ status }: { status: string | null | undefined }) {
  const map: Record<string, { label: string; tone: ChipTone }> = {
    halal_candidate: { label: "Halal candidate", tone: "positive" },
    not_halal: { label: "Not halal", tone: "negative" },
    unknown: { label: "Halal unknown", tone: "neutral" },
  };
  const it = map[status ?? "unknown"] ?? map.unknown;
  return (
    <Chip tone={it.tone} size="sm">
      {it.label}
    </Chip>
  );
}

export function Score({ value, size }: { value: number | null | undefined; size?: "lg" | "sm" }) {
  if (value === null || value === undefined) {
    return <span className={`font-mono text-ink-2 ${size === "lg" ? "text-4xl" : ""}`}>—</span>;
  }
  return (
    <span className={`font-mono tabular-nums text-accent ${size === "lg" ? "text-5xl" : "text-base"}`} title="Research score 0-10">
      {value.toFixed(1)}
    </span>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-ink-1" role="status" aria-live="polite">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-border-strong border-t-accent" aria-hidden="true" />
      {label ?? "Loading…"}
    </div>
  );
}

export function CompanyLink({ companyId, children, className }: { companyId: string; children: React.ReactNode; className?: string }) {
  return (
    <Link to={`/c/${encodeURIComponent(companyId)}`} className={`text-ink-0 underline decoration-border-strong underline-offset-4 hover:decoration-accent ${className ?? ""}`}>
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
